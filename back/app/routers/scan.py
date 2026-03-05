import uuid
import asyncio
import time as _time
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db, Host
from app import crud
from app.models import FullScanHistory
from app.auth import require_role
from app.websocket_manager import ws_manager
from app.scanners import (
    ping_multiple, ping_auto, expand_network,
    scan_ports, scan_services, scan_vulnerabilities,
    detect_os, detect_os_segment, scan_mac,
    scan_ports_segment, scan_services_segment,
    full_host_scan
)
from app.schemas import (
    HostsRequest, NetworkRequest,
    PortScanRequest, ServiceScanRequest,
    VulnScanRequest, VulnSegmentScanRequest,
    OSRequest, OSSegmentRequest, MacScanRequest,
    PortSegmentScanRequest, ServiceSegmentScanRequest,
    FullScanRequest, FullScanRangeRequest,
    SavePingResultsRequest, FullScanHistorySave
)
from app.utils import audit_log, get_user_id, get_user_info, logger

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "ok", "message": "Network Scanner API is running"}


# ping network

@router.post("/ping")
async def ping_hosts(data: HostsRequest, request: Request, db: Session = Depends(get_db), _role=Depends(require_role("op"))):
    scan_id = str(uuid.uuid4())
    ws_manager.register_scan(scan_id, get_user_id(request))
    audit_log(db, request, "scan", "scan", f"Ping scan: {len(data.hosts)} hosts", {"scan_id": scan_id, "host_count": len(data.hosts)})
    results = await ping_multiple(data.hosts, emit_progress=True, scan_id=scan_id, resolve_hostname=False, host_timeout=data.host_timeout, concurrency=max(1, min(data.concurrency, 200)))
    ws_manager.schedule_unregister(scan_id)
    return {"scan_id": scan_id, "results": results}


@router.post("/scan/network")
async def scan_network(data: NetworkRequest, request: Request, db: Session = Depends(get_db), _role=Depends(require_role("op"))):
    scan_id = str(uuid.uuid4())
    ws_manager.register_scan(scan_id, get_user_id(request))
    hosts = expand_network(data.cidr)
    audit_log(db, request, "scan", "scan", f"Network scan: {data.cidr} ({len(hosts)} hosts)", {"scan_id": scan_id, "cidr": data.cidr, "host_count": len(hosts)})
    results = await ping_multiple(hosts, emit_progress=True, scan_id=scan_id, resolve_hostname=False, host_timeout=data.host_timeout, concurrency=max(1, min(data.concurrency, 200)))
    ws_manager.schedule_unregister(scan_id)
    return {"scan_id": scan_id, "network": data.cidr, "results": results}


# port scan

@router.post("/scan/ports")
async def scan_ports_endpoint(data: PortScanRequest, _role=Depends(require_role("op"))):
    ports = await scan_ports(data.host, data.ports)
    return {"host": data.host, "ports": ports}


@router.post("/scan/ports/segment")
async def scan_ports_by_segment(data: PortSegmentScanRequest, request: Request, db: Session = Depends(get_db), _role=Depends(require_role("op"))):
    scan_id = str(uuid.uuid4())
    ws_manager.register_scan(scan_id, get_user_id(request))

    expanded_hosts = []
    for host in data.hosts:
        if '/' in host:
            expanded = expand_network(host)
            expanded_hosts.extend(expanded)
        else:
            expanded_hosts.append(host)

    audit_log(db, request, "scan", "scan", f"Port scan: {len(expanded_hosts)} hosts", {"scan_id": scan_id, "host_count": len(expanded_hosts), "ports": data.ports})
    results = await scan_ports_segment(
        hosts=expanded_hosts,
        ports=data.ports,
        emit_progress=True,
        scan_id=scan_id,
        host_timeout=data.host_timeout,
        concurrency=max(1, min(data.concurrency, 200))
    )
    ws_manager.schedule_unregister(scan_id)
    return {"scan_id": scan_id, "results": results}


# service scan

@router.post("/scan/services")
async def scan_services_endpoint(data: ServiceScanRequest, _role=Depends(require_role("op"))):
    services = await scan_services(data.host, data.ports)
    return {"host": data.host, "services": services}


@router.post("/scan/services/segment")
async def scan_services_by_segment(data: ServiceSegmentScanRequest, request: Request, db: Session = Depends(get_db), _role=Depends(require_role("op"))):
    scan_id = str(uuid.uuid4())
    ws_manager.register_scan(scan_id, get_user_id(request))

    expanded_hosts = []
    for host in data.hosts:
        if '/' in host:
            expanded = expand_network(host)
            expanded_hosts.extend(expanded)
        else:
            expanded_hosts.append(host)

    audit_log(db, request, "scan", "scan", f"Service scan: {len(expanded_hosts)} hosts", {"scan_id": scan_id, "host_count": len(expanded_hosts), "ports": data.ports})
    results = await scan_services_segment(
        hosts=expanded_hosts,
        ports=data.ports,
        emit_progress=True,
        scan_id=scan_id,
        host_timeout=data.host_timeout,
        concurrency=max(1, min(data.concurrency, 200))
    )
    ws_manager.schedule_unregister(scan_id)
    return {"scan_id": scan_id, "results": results}


# vulnerability scan

@router.post("/scan/vulnerabilities")
async def scan_vulnerabilities_endpoint(data: VulnScanRequest, _role=Depends(require_role("op"))):
    vulns = await scan_vulnerabilities(data.host)
    return {"host": data.host, "vulnerabilities": vulns}


@router.post("/scan/vulnerabilities/segment")
async def scan_vulnerabilities_segment_endpoint(data: VulnSegmentScanRequest, request: Request, db: Session = Depends(get_db), _role=Depends(require_role("op"))):
    scan_id = str(uuid.uuid4())
    ws_manager.register_scan(scan_id, get_user_id(request))

    expanded_hosts = []
    for host in data.hosts:
        if '/' in host:
            expanded = expand_network(host)
            expanded_hosts.extend(expanded)
        else:
            expanded_hosts.append(host)

    audit_log(db, request, "scan", "scan", f"Vulnerability scan: {len(expanded_hosts)} hosts", {"scan_id": scan_id, "host_count": len(expanded_hosts)})

    results = []
    total = len(expanded_hosts)

    await ws_manager.broadcast("scan_progress", {
        "scan_id": scan_id,
        "scan_type": "vulnerabilities",
        "status": "started",
        "total": total,
        "completed": 0,
        "progress": 0
    })

    for i, host in enumerate(expanded_hosts):
        if ws_manager.is_scan_cancelled(scan_id):
            break
        vulns = await scan_vulnerabilities(host)
        if vulns:
            results.append({"host": host, "vulnerabilities": vulns})

        progress = round(((i + 1) / total) * 100, 2)
        await ws_manager.broadcast("scan_progress", {
            "scan_id": scan_id,
            "scan_type": "vulnerabilities",
            "status": "scanning",
            "total": total,
            "completed": i + 1,
            "progress": progress,
            "current_host": host
        })

    await ws_manager.broadcast("scan_progress", {
        "scan_id": scan_id,
        "scan_type": "vulnerabilities",
        "status": "completed",
        "total": total,
        "completed": total,
        "progress": 100
    })

    ws_manager.schedule_unregister(scan_id)
    return {"scan_id": scan_id, "results": results}


# operating system detection

@router.post("/scan/os")
async def detect_os_endpoint(data: OSRequest, _role=Depends(require_role("op"))):
    os_data = await detect_os(data.host)
    return {"host": data.host, "os": os_data}


@router.post("/scan/os/segment")
async def detect_os_segment_endpoint(data: OSSegmentRequest, request: Request, db: Session = Depends(get_db), _role=Depends(require_role("op"))):
    scan_id = str(uuid.uuid4())
    ws_manager.register_scan(scan_id, get_user_id(request))

    expanded_hosts = []
    for host in data.hosts:
        if '/' in host:
            expanded = expand_network(host)
            expanded_hosts.extend(expanded)
        else:
            expanded_hosts.append(host)

    audit_log(db, request, "scan", "scan", f"OS scan: {len(expanded_hosts)} hosts", {"scan_id": scan_id, "host_count": len(expanded_hosts)})
    results = await detect_os_segment(expanded_hosts, emit_progress=True, scan_id=scan_id, host_timeout=data.host_timeout, concurrency=max(1, min(data.concurrency, 200)))
    ws_manager.schedule_unregister(scan_id)
    return {"scan_id": scan_id, "results": results}


# mac address scan

@router.post("/scan/mac")
async def scan_mac_endpoint(data: MacScanRequest, request: Request, db: Session = Depends(get_db), _role=Depends(require_role("op"))):
    scan_id = str(uuid.uuid4())
    ws_manager.register_scan(scan_id, get_user_id(request))
    audit_log(db, request, "scan", "scan", f"MAC scan: {data.cidr}", {"scan_id": scan_id, "cidr": data.cidr})
    devices = await scan_mac(data.cidr, emit_progress=True, scan_id=scan_id, host_timeout=data.host_timeout, concurrency=max(1, min(data.concurrency, 200)))
    ws_manager.schedule_unregister(scan_id)
    return {"scan_id": scan_id, "network": data.cidr, "devices": devices}


# full scan

@router.post("/scan/full")
async def full_scan_endpoint(data: FullScanRequest, request: Request, db: Session = Depends(get_db), _role=Depends(require_role("op"))):
    scan_id = str(uuid.uuid4())
    ws_manager.register_scan(scan_id, get_user_id(request))
    audit_log(db, request, "scan", "scan", f"Full scan: {data.host}", {"scan_id": scan_id, "host": data.host})
    result = await full_host_scan(data.host, emit_progress=True, scan_id=scan_id, host_timeout=data.host_timeout)

    if data.save_to_db:
        host_status = result.get("status", "unknown")
        if host_status == "up":
            crud.create_or_update_host(db, result)
        else:
            existing = crud.get_host_by_ip(db, data.host)
            if existing:
                crud.mark_host_as_down(db, data.host)

    ws_manager.schedule_unregister(scan_id)
    return {"scan_id": scan_id, "result": result}


@router.post("/scan/full/range")
async def full_scan_range_endpoint(data: FullScanRangeRequest, request: Request, db: Session = Depends(get_db), _role=Depends(require_role("op"))):
    scan_id = str(uuid.uuid4())
    ws_manager.register_scan(scan_id, get_user_id(request))
    audit_log(db, request, "scan", "scan", f"Full range scan: {len(data.hosts)} hosts", {"scan_id": scan_id, "host_count": len(data.hosts)})

    total_hosts = len(data.hosts)

    await ws_manager.broadcast("scan_progress", {
        "scan_id": scan_id,
        "scan_type": "full_range",
        "status": "ping_phase",
        "total": total_hosts,
        "completed": 0,
        "progress": 0,
        "message": f"Detectando hosts activos ({total_hosts} IPs)..."
    })

    ping_completed = 0
    ping_active_found = 0
    ping_results_list = []
    ping_semaphore = asyncio.Semaphore(50)
    ping_lock = asyncio.Lock()
    last_ping_broadcast = 0
    last_ping_broadcast_time = _time.time()
    ping_update_interval = max(1, total_hosts // 50)
    ping_min_interval = 0.2

    async def ping_one_host(host_ip):
        nonlocal ping_completed, ping_active_found, last_ping_broadcast, last_ping_broadcast_time
        async with ping_semaphore:
            if ws_manager.is_scan_cancelled(scan_id):
                return {"host": host_ip, "hostname": None, "status": "down", "latency_ms": None, "method": "cancelled"}
            try:
                result = await ping_auto(host_ip, timeout=2)
            except Exception:
                result = {"host": host_ip, "hostname": None, "status": "down", "latency_ms": None, "method": "error"}

            async with ping_lock:
                ping_completed += 1
                if result.get("status") == "up":
                    ping_active_found += 1
                ping_results_list.append(result)

                current_time = _time.time()
                should_broadcast = (
                    (ping_completed - last_ping_broadcast >= ping_update_interval) or
                    (current_time - last_ping_broadcast_time >= ping_min_interval and ping_completed > last_ping_broadcast) or
                    (ping_completed == total_hosts)
                )

                if should_broadcast:
                    last_ping_broadcast = ping_completed
                    last_ping_broadcast_time = current_time
                    progress = round((ping_completed / total_hosts) * 5, 1)
                    await ws_manager.broadcast("scan_progress", {
                        "scan_id": scan_id,
                        "scan_type": "full_range",
                        "status": "ping_progress",
                        "total": total_hosts,
                        "completed": ping_completed,
                        "active_found": ping_active_found,
                        "progress": progress,
                        "message": f"Ping: {ping_completed}/{total_hosts} IPs verificadas ({ping_active_found} activas)..."
                    })

            return result

    await asyncio.gather(*[ping_one_host(h) for h in data.hosts])

    active_hosts = [r["host"] for r in ping_results_list if r.get("status") == "up"]
    inactive_hosts = [r["host"] for r in ping_results_list if r.get("status") != "up"]

    if ws_manager.is_scan_cancelled(scan_id):
        ws_manager.clear_scan(scan_id)
        return {
            "scan_id": scan_id,
            "total": total_hosts,
            "active_count": 0,
            "inactive_count": total_hosts,
            "results": [],
            "cancelled": True
        }

    await ws_manager.broadcast("scan_progress", {
        "scan_id": scan_id,
        "scan_type": "full_range",
        "status": "ping_done",
        "total": total_hosts,
        "active_count": len(active_hosts),
        "inactive_count": len(inactive_hosts),
        "active_hosts": active_hosts,
        "inactive_hosts": inactive_hosts,
        "progress": 5,
        "message": f"{len(active_hosts)} hosts activos de {total_hosts} detectados"
    })

    MAX_CONCURRENT = max(1, min(data.concurrency, 100))
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    scan_results = []
    total_active = len(active_hosts)
    completed_count = 0
    currently_scanning = set()
    results_lock = asyncio.Lock()

    async def scan_single_host(host_ip, save_to_db, timeout):
        nonlocal completed_count

        async with semaphore:
            if ws_manager.is_scan_cancelled(scan_id):
                return None

            currently_scanning.add(host_ip)
            await ws_manager.broadcast("scan_progress", {
                "scan_id": scan_id,
                "scan_type": "full_range",
                "status": "scanning_host",
                "current_host": host_ip,
                "current_hosts": list(currently_scanning),
                "completed_count": completed_count,
                "total_active": total_active,
                "total": total_hosts,
                "progress": round(5 + ((completed_count / max(total_active, 1)) * 90), 1),
                "message": f"Escaneando {host_ip} ({len(currently_scanning)} simultáneos, {completed_count}/{total_active} completados)..."
            })

            try:
                result = await full_host_scan(
                    host_ip,
                    emit_progress=False,
                    host_timeout=timeout
                )

                host_status = result.get("status", "unknown")

                if save_to_db:
                    if host_status == "up":
                        crud.create_or_update_host(db, result)
                    else:
                        existing = crud.get_host_by_ip(db, host_ip)
                        if existing:
                            crud.mark_host_as_down(db, host_ip)

            except Exception as e:
                result = {
                    "host": host_ip,
                    "status": "error",
                    "error": str(e),
                    "ports": [],
                    "services": [],
                    "vulnerabilities": []
                }

            async with results_lock:
                scan_results.append(result)
                completed_count += 1
                currently_scanning.discard(host_ip)

            await ws_manager.broadcast("scan_progress", {
                "scan_id": scan_id,
                "scan_type": "full_range",
                "status": "host_completed",
                "current_host": host_ip,
                "current_hosts": list(currently_scanning),
                "completed_count": completed_count,
                "total_active": total_active,
                "total": total_hosts,
                "progress": round(5 + ((completed_count / max(total_active, 1)) * 90), 1),
                "result": result,
                "message": f"Completado {host_ip} ({completed_count}/{total_active})"
            })

            return result

    tasks = [scan_single_host(h, data.save_to_db, data.host_timeout) for h in active_hosts]
    await asyncio.gather(*tasks, return_exceptions=True)

    if data.save_to_db:
        existing_inactive = [
            ip for ip in inactive_hosts if crud.get_host_by_ip(db, ip)
        ]
        if existing_inactive:
            crud.mark_multiple_hosts_as_down(db, existing_inactive)

    await ws_manager.broadcast("scan_progress", {
        "scan_id": scan_id,
        "scan_type": "full_range",
        "status": "completed",
        "total": total_hosts,
        "active_count": total_active,
        "inactive_count": len(inactive_hosts),
        "scanned_count": len(scan_results),
        "completed_count": completed_count,
        "progress": 100,
        "message": f"Completado: {len(scan_results)} hosts escaneados de {total_active} activos (máx {MAX_CONCURRENT} simultáneos)"
    })

    ws_manager.clear_scan(scan_id)

    return {
        "scan_id": scan_id,
        "total": total_hosts,
        "active_count": total_active,
        "inactive_count": len(inactive_hosts),
        "results": scan_results
    }


# save ping results

@router.post("/ping/save")
async def save_ping_results(data: SavePingResultsRequest, db: Session = Depends(get_db), _role=Depends(require_role("mod"))):
    saved = 0
    updated = 0
    for r in data.results:
        if r.get("status") == "up":
            raw_ip = r["host"]
            clean = raw_ip.split('/')[0].strip() if '/' in str(raw_ip) else str(raw_ip).strip()
            host = crud.get_host_by_ip(db, clean)
            if not host:
                host = Host(
                    ip=clean,
                    status="up",
                    latency_ms=r.get("latency_ms"),
                    last_seen=datetime.utcnow()
                )
                db.add(host)
                saved += 1
            else:
                host.status = "up"
                host.latency_ms = r.get("latency_ms")
                host.last_seen = datetime.utcnow()
                updated += 1
    db.commit()
    return {"saved": saved, "updated": updated, "total": saved + updated}


# full scan history

@router.post("/api/fullscan-history")
async def save_fullscan_history(data: FullScanHistorySave, request: Request, db: Session = Depends(get_db), _role=Depends(require_role("op"))):
    user_info = get_user_info(request)
    entry = FullScanHistory(
        scan_type=data.scan_type,
        target=data.target,
        hosts_scanned=data.hosts_scanned,
        hosts_active=data.hosts_active,
        total_ports=data.total_ports,
        total_services=data.total_services,
        status=data.status,
        duration_seconds=data.duration_seconds,
        scan_results=data.scan_results,
        error_message=data.error_message,
        user_id=user_info["user_id"],
        username=user_info["username"],
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    audit_log(db, request, "create", "scan", f"FullScan guardado: {data.target}", {"scan_type": data.scan_type, "target": data.target, "hosts_scanned": data.hosts_scanned})
    return {
        "id": entry.id,
        "message": "Registro guardado",
        "created_at": entry.created_at.isoformat() if entry.created_at else None
    }


@router.get("/api/fullscan-history")
async def get_fullscan_history(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    total = db.query(FullScanHistory).count()
    entries = db.query(FullScanHistory).order_by(
        FullScanHistory.created_at.desc()
    ).offset(skip).limit(limit).all()

    return {
        "total": total,
        "items": [
            {
                "id": e.id,
                "scan_type": e.scan_type,
                "target": e.target,
                "hosts_scanned": e.hosts_scanned,
                "hosts_active": e.hosts_active,
                "total_ports": e.total_ports,
                "total_services": e.total_services,
                "status": e.status,
                "duration_seconds": e.duration_seconds,
                "error_message": e.error_message,
                "created_at": e.created_at.isoformat() if e.created_at else None,
                "username": e.username,
                "user_id": e.user_id,
            }
            for e in entries
        ]
    }


@router.get("/api/fullscan-history/{history_id}")
async def get_fullscan_history_detail(history_id: int, db: Session = Depends(get_db)):
    entry = db.query(FullScanHistory).filter(FullScanHistory.id == history_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Registro no encontrado")

    return {
        "id": entry.id,
        "scan_type": entry.scan_type,
        "target": entry.target,
        "hosts_scanned": entry.hosts_scanned,
        "hosts_active": entry.hosts_active,
        "total_ports": entry.total_ports,
        "total_services": entry.total_services,
        "status": entry.status,
        "duration_seconds": entry.duration_seconds,
        "scan_results": entry.scan_results,
        "error_message": entry.error_message,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
    }


@router.delete("/api/fullscan-history/{history_id}")
async def delete_fullscan_history(history_id: int, request: Request, db: Session = Depends(get_db), _role=Depends(require_role("mod"))):
    entry = db.query(FullScanHistory).filter(FullScanHistory.id == history_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Registro no encontrado")

    audit_log(db, request, "delete", "scan", f"FullScan historial eliminado: {entry.target}", {"history_id": history_id, "target": entry.target})
    db.delete(entry)
    db.commit()
    return {"message": "Registro eliminado"}


@router.delete("/api/fullscan-history")
async def clear_fullscan_history(request: Request, db: Session = Depends(get_db), _role=Depends(require_role("admin"))):
    count = db.query(FullScanHistory).delete()
    db.commit()
    audit_log(db, request, "delete", "scan", f"Historial FullScan limpiado: {count} registros", {"count": count})
    return {"message": f"{count} registros eliminados"}
