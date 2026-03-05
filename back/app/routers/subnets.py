import uuid
import asyncio
import ipaddress
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.database import get_db, Host
from app import crud
from app.models import Subnet, SubnetDevice, AuditLog
from app.auth import require_role
from app.websocket_manager import ws_manager
from app.scanners import (
    ping_multiple, expand_network,
    scan_ports_segment, scan_services_segment,
    detect_os_segment, scan_mac, get_mac_single_host,
    scan_ports, scan_services, detect_os,
)
from app.ssh_operations import shutdown_host_ssh, shutdown_multiple_hosts
from app.utils import audit_log, get_user_id, get_user_info, logger, host_to_dict

router = APIRouter(prefix="/api/subnets", tags=["subnets"])


# subnet schemas
class SubnetCreate(BaseModel):
    name: str
    start_ip: str
    end_ip: str

    @field_validator("start_ip", "end_ip")
    @classmethod
    def validate_ip(cls, v):
        try:
            ipaddress.ip_address(v.strip())
            return v.strip()
        except ValueError:
            raise ValueError(f"IP inválida: {v}")


# update schema allows partial updates
class SubnetUpdate(BaseModel):
    name: Optional[str] = None
    start_ip: Optional[str] = None
    end_ip: Optional[str] = None


class DeviceTypeUpdate(BaseModel):
    device_type: str

    @field_validator("device_type")
    @classmethod
    def validate_type(cls, v):
        allowed = {"pc", "laptop", "phone", "printer", "server", "router", "switch", "tablet", "camera", "unknown"}
        if v not in allowed:
            raise ValueError(f"Tipo no válido. Permitidos: {', '.join(sorted(allowed))}")
        return v


class DeviceLabelUpdate(BaseModel):
    label: str


class DeviceShutdownRequest(BaseModel):
    username: str
    password: str
    sudo_password: Optional[str] = None


# helper functions

def ip_range_to_list(start_ip: str, end_ip: str) -> list[str]:
    start = int(ipaddress.ip_address(start_ip))
    end = int(ipaddress.ip_address(end_ip))
    if start > end:
        start, end = end, start
    return [str(ipaddress.ip_address(i)) for i in range(start, end + 1)]


def subnet_to_dict(subnet: Subnet) -> dict:
    return {
        "id": subnet.id,
        "name": subnet.name,
        "start_ip": subnet.start_ip,
        "end_ip": subnet.end_ip,
        "created_by": subnet.created_by,
        "created_at": subnet.created_at.isoformat() if subnet.created_at else None,
        "updated_at": subnet.updated_at.isoformat() if subnet.updated_at else None,
    }


def device_to_dict(device: SubnetDevice) -> dict:
    return {
        "id": device.id,
        "subnet_id": device.subnet_id,
        "ip": device.ip,
        "label": device.label,
        "device_type": device.device_type,
        "status": device.status,
        "last_scan_at": device.last_scan_at.isoformat() if device.last_scan_at else None,
        "scan_data": device.scan_data,
        "created_at": device.created_at.isoformat() if device.created_at else None,
    }


# helper to convert IP range to list of IPs

@router.get("")
async def list_subnets(db: Session = Depends(get_db), _role=Depends(require_role("viewer"))):
    subnets = db.query(Subnet).order_by(Subnet.id).all()
    result = []
    for s in subnets:
        d = subnet_to_dict(s)
        devices = db.query(SubnetDevice).filter(SubnetDevice.subnet_id == s.id).all()
        d["device_count"] = len(devices)
        d["active_count"] = sum(1 for dev in devices if dev.status == "green")
        d["inactive_count"] = sum(1 for dev in devices if dev.status == "red")
        d["unknown_count"] = sum(1 for dev in devices if dev.status == "grey")
        result.append(d)
    return result


@router.post("")
async def create_subnet(
    data: SubnetCreate,
    request: Request,
    db: Session = Depends(get_db),
    _role=Depends(require_role("op"))
):
    user_info = get_user_info(request)
    ips = ip_range_to_list(data.start_ip, data.end_ip)
    if len(ips) > 1024:
        raise HTTPException(400, "El rango no puede exceder 1024 IPs")

    subnet = Subnet(
        name=data.name,
        start_ip=data.start_ip,
        end_ip=data.end_ip,
        created_by=user_info.get("username"),
    )
    db.add(subnet)
    db.flush()

    for idx, ip in enumerate(ips, 1):
        device = SubnetDevice(
            subnet_id=subnet.id,
            ip=ip,
            label=f"PC {idx}",
            device_type="pc",
            status="grey",
        )
        db.add(device)

    db.commit()
    db.refresh(subnet)

    audit_log(db, request, "create", "subnet",
              f"Subred creada: {data.name} ({data.start_ip} - {data.end_ip}, {len(ips)} dispositivos)",
              {"subnet_id": subnet.id, "name": data.name, "start_ip": data.start_ip, "end_ip": data.end_ip})

    return {"id": subnet.id, "name": subnet.name, "device_count": len(ips)}


@router.get("/{subnet_id}")
async def get_subnet(subnet_id: int, db: Session = Depends(get_db), _role=Depends(require_role("viewer"))):
    subnet = db.query(Subnet).filter(Subnet.id == subnet_id).first()
    if not subnet:
        raise HTTPException(404, "Subred no encontrada")
    d = subnet_to_dict(subnet)
    devices = db.query(SubnetDevice).filter(SubnetDevice.subnet_id == subnet_id).order_by(SubnetDevice.id).all()
    d["devices"] = [device_to_dict(dev) for dev in devices]
    return d


@router.put("/{subnet_id}")
async def update_subnet(
    subnet_id: int,
    data: SubnetUpdate,
    request: Request,
    db: Session = Depends(get_db),
    _role=Depends(require_role("op"))
):
    subnet = db.query(Subnet).filter(Subnet.id == subnet_id).first()
    if not subnet:
        raise HTTPException(404, "Subred no encontrada")
    if data.name is not None:
        subnet.name = data.name
    if data.start_ip is not None and data.end_ip is not None:
        # Re-generate devices
        db.query(SubnetDevice).filter(SubnetDevice.subnet_id == subnet_id).delete()
        subnet.start_ip = data.start_ip
        subnet.end_ip = data.end_ip
        ips = ip_range_to_list(data.start_ip, data.end_ip)
        if len(ips) > 1024:
            raise HTTPException(400, "El rango no puede exceder 1024 IPs")
        for idx, ip in enumerate(ips, 1):
            db.add(SubnetDevice(subnet_id=subnet_id, ip=ip, label=f"PC {idx}", device_type="pc", status="grey"))
    db.commit()
    audit_log(db, request, "update", "subnet", f"Subred actualizada: {subnet.name}", {"subnet_id": subnet_id})
    return {"ok": True}


@router.delete("/{subnet_id}")
async def delete_subnet(
    subnet_id: int,
    request: Request,
    db: Session = Depends(get_db),
    _role=Depends(require_role("op"))
):
    subnet = db.query(Subnet).filter(Subnet.id == subnet_id).first()
    if not subnet:
        raise HTTPException(404, "Subred no encontrada")
    name = subnet.name
    db.query(SubnetDevice).filter(SubnetDevice.subnet_id == subnet_id).delete()
    db.delete(subnet)
    db.commit()
    audit_log(db, request, "delete", "subnet", f"Subred eliminada: {name}", {"subnet_id": subnet_id})
    return {"ok": True}



@router.post("/{subnet_id}/scan")
async def scan_subnet(
    subnet_id: int,
    request: Request,
    db: Session = Depends(get_db),
    _role=Depends(require_role("op"))
):
    subnet = db.query(Subnet).filter(Subnet.id == subnet_id).first()
    if not subnet:
        raise HTTPException(404, "Subred no encontrada")

    devices = db.query(SubnetDevice).filter(SubnetDevice.subnet_id == subnet_id).order_by(SubnetDevice.id).all()
    ip_list = [d.ip for d in devices]

    scan_id = str(uuid.uuid4())
    ws_manager.register_scan(scan_id, get_user_id(request))

    audit_log(db, request, "scan", "subnet",
              f"Ping sweep subred: {subnet.name} ({len(ip_list)} IPs)",
              {"subnet_id": subnet_id, "scan_id": scan_id})

    results = await ping_multiple(ip_list, emit_progress=True, scan_id=scan_id, resolve_hostname=False, host_timeout=2, concurrency=50)
    ws_manager.schedule_unregister(scan_id)

    # Build active set
    active_ips = set()
    for r in results:
        if r.get("status") == "up":
            active_ips.add(r.get("host"))

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)

    for dev in devices:
        old_status = dev.status
        if dev.ip in active_ips:
            dev.status = "green"
        else:
            # Was green → now red (went down)
            if old_status == "green":
                dev.status = "red"
            # grey stays grey, red stays red
        dev.last_scan_at = now

    db.commit()

    # Return updated devices
    devices = db.query(SubnetDevice).filter(SubnetDevice.subnet_id == subnet_id).order_by(SubnetDevice.id).all()
    return {
        "scan_id": scan_id,
        "devices": [device_to_dict(d) for d in devices],
        "active_count": len(active_ips),
        "total": len(ip_list),
    }




@router.put("/{subnet_id}/devices/{device_id}/type")
async def update_device_type(
    subnet_id: int,
    device_id: int,
    data: DeviceTypeUpdate,
    request: Request,
    db: Session = Depends(get_db),
    _role=Depends(require_role("op"))
):
    device = db.query(SubnetDevice).filter(
        SubnetDevice.id == device_id,
        SubnetDevice.subnet_id == subnet_id
    ).first()
    if not device:
        raise HTTPException(404, "Dispositivo no encontrado")
    device.device_type = data.device_type
    db.commit()
    audit_log(db, request, "update", "subnet",
              f"Tipo de dispositivo cambiado: {device.ip} → {data.device_type}",
              {"device_id": device_id, "ip": device.ip, "device_type": data.device_type})
    return device_to_dict(device)


@router.put("/{subnet_id}/devices/{device_id}/label")
async def update_device_label(
    subnet_id: int,
    device_id: int,
    data: DeviceLabelUpdate,
    request: Request,
    db: Session = Depends(get_db),
    _role=Depends(require_role("op"))
):
    device = db.query(SubnetDevice).filter(
        SubnetDevice.id == device_id,
        SubnetDevice.subnet_id == subnet_id
    ).first()
    if not device:
        raise HTTPException(404, "Dispositivo no encontrado")
    device.label = data.label
    db.commit()
    audit_log(db, request, "update", "subnet",
              f"Etiqueta de dispositivo cambiada: {device.ip} → {data.label}",
              {"device_id": device_id, "ip": device.ip, "label": data.label})
    return device_to_dict(device)


@router.get("/{subnet_id}/devices/{device_id}/info")
async def get_device_info(
    subnet_id: int,
    device_id: int,
    request: Request,
    db: Session = Depends(get_db),
    _role=Depends(require_role("viewer"))
):
    device = db.query(SubnetDevice).filter(
        SubnetDevice.id == device_id,
        SubnetDevice.subnet_id == subnet_id
    ).first()
    if not device:
        raise HTTPException(404, "Dispositivo no encontrado")

    # Check if host exists in main DB with data
    host = db.query(Host).filter(Host.ip == device.ip).first()
    if host and host.mac:
        # Data exists — return from DB
        info = host_to_dict(host)
        # Cache in device
        device.scan_data = {
            "mac": info.get("mac"),
            "vendor": info.get("vendor"),
            "os_name": info.get("os_name"),
            "os_accuracy": info.get("os_accuracy"),
            "ports": info.get("ports", []),
            "services": info.get("services", []),
            "source": "database",
        }
        db.commit()
        return {"source": "database", "data": device.scan_data}

    # If we have cached scan_data, return it
    if device.scan_data and device.scan_data.get("mac"):
        return {"source": "cache", "data": device.scan_data}

    return {"source": "none", "data": None}


@router.post("/{subnet_id}/devices/{device_id}/scan")
async def scan_device(
    subnet_id: int,
    device_id: int,
    request: Request,
    db: Session = Depends(get_db),
    _role=Depends(require_role("op"))
):
    device = db.query(SubnetDevice).filter(
        SubnetDevice.id == device_id,
        SubnetDevice.subnet_id == subnet_id
    ).first()
    if not device:
        raise HTTPException(404, "Dispositivo no encontrado")

    ip = device.ip
    scan_data = {}

    audit_log(db, request, "scan", "subnet",
              f"Escaneo de dispositivo: {ip}",
              {"device_id": device_id, "ip": ip})
    
    # MAC + Vendor
    try:
        mac_result = await asyncio.to_thread(get_mac_single_host, ip)
        if mac_result and mac_result[0]:
            scan_data["mac"] = mac_result[0]
            scan_data["vendor"] = mac_result[1]
        else:
            scan_data["mac"] = None
            scan_data["vendor"] = None
    except Exception as e:
        logger.error(f"MAC scan error for {ip}: {e}")
        scan_data["mac"] = None
        scan_data["vendor"] = None

    # Port scan
    try:
        ports = await scan_ports(ip, "1-1024")
        scan_data["ports"] = ports if ports else []
    except Exception as e:
        logger.error(f"Port scan error for {ip}: {e}")
        scan_data["ports"] = []

    # Service scan
    try:
        services = await scan_services(ip, "1-1024")
        scan_data["services"] = services if services else []
    except Exception as e:
        logger.error(f"Service scan error for {ip}: {e}")
        scan_data["services"] = []

    # OS detection
    try:
        os_result = await detect_os(ip)
        if os_result:
            scan_data["os_name"] = os_result.get("name")
            scan_data["os_accuracy"] = os_result.get("accuracy")
        else:
            scan_data["os_name"] = None
            scan_data["os_accuracy"] = None
    except Exception as e:
        logger.error(f"OS scan error for {ip}: {e}")
        scan_data["os_name"] = None
        scan_data["os_accuracy"] = None

    scan_data["source"] = "live_scan"

    from datetime import datetime, timezone
    device.scan_data = scan_data
    device.last_scan_at = datetime.now(timezone.utc)
    db.commit()

    # Also save to main Host DB
    try:
        crud.create_or_update_host(db, {
            "ip": ip,
            "mac": scan_data.get("mac"),
            "vendor": scan_data.get("vendor"),
            "os_name": scan_data.get("os_name"),
            "os_accuracy": scan_data.get("os_accuracy"),
            "status": "active" if device.status == "green" else "down",
        })
    except Exception as e:
        logger.error(f"Error guardando host {ip} en BD: {e}")

    return {"source": "live_scan", "data": scan_data}


@router.post("/{subnet_id}/devices/{device_id}/shutdown")
async def shutdown_device(
    subnet_id: int,
    device_id: int,
    data: DeviceShutdownRequest,
    request: Request,
    db: Session = Depends(get_db),
    _role=Depends(require_role("op"))
):
    device = db.query(SubnetDevice).filter(
        SubnetDevice.id == device_id,
        SubnetDevice.subnet_id == subnet_id
    ).first()
    if not device:
        raise HTTPException(404, "Dispositivo no encontrado")

    ip = device.ip
    audit_log(db, request, "shutdown", "subnet",
              f"Apagado de dispositivo: {ip} ({device.label})",
              {"device_id": device_id, "ip": ip, "label": device.label})

    result = await shutdown_host_ssh(ip, data.username, data.password)

    if result.get("success"):
        device.status = "red"
        db.commit()
        try:
            crud.mark_host_as_down(db, ip)
        except Exception:
            pass

    return result


class LabShutdownRequest(BaseModel):
    username: str
    password: str


@router.post("/{subnet_id}/shutdown")
async def shutdown_lab(
    subnet_id: int,
    data: LabShutdownRequest,
    request: Request,
    db: Session = Depends(get_db),
    _role=Depends(require_role("op"))
):
    subnet = db.query(Subnet).filter(Subnet.id == subnet_id).first()
    if not subnet:
        raise HTTPException(404, "Subred no encontrada")

    devices = db.query(SubnetDevice).filter(
        SubnetDevice.subnet_id == subnet_id,
        SubnetDevice.status == "green"
    ).all()

    if not devices:
        return {"total": 0, "success_count": 0, "fail_count": 0, "results": [], "message": "No hay dispositivos activos para apagar"}

    ip_list = [d.ip for d in devices]

    audit_log(db, request, "shutdown", "subnet",
              f"Apagado de laboratorio: {subnet.name} ({len(ip_list)} dispositivos activos)",
              {"subnet_id": subnet_id, "ips": ip_list})

    results = await shutdown_multiple_hosts(ip_list, data.username, data.password)

    # Mark successful shutdowns as red
    success_ips = set()
    for r in results:
        if r.get("success"):
            success_ips.add(r.get("host"))

    for dev in devices:
        if dev.ip in success_ips:
            dev.status = "red"
    db.commit()

    # Also mark in main hosts DB
    if success_ips:
        try:
            crud.mark_multiple_hosts_as_down(db, list(success_ips))
        except Exception:
            pass

    return {
        "total": len(ip_list),
        "success_count": len(success_ips),
        "fail_count": len(ip_list) - len(success_ips),
        "results": results,
    }
