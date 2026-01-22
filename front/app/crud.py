from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime
from app.database import Host, Port, Service, Vulnerability, ConnectionHistory
from typing import List, Optional
import ipaddress
import asyncio

def get_ws_manager():
    from app.websocket_manager import ws_manager
    return ws_manager

def create_or_update_host(db: Session, scan_data: dict):
    """Crea o actualiza un host con todos sus datos"""
    
    # Buscar host existente
    host = db.query(Host).filter(Host.ip == scan_data["host"]).first()
    is_new = host is None

    if not host:
        host = Host(ip=scan_data["host"])
        db.add(host)
    
    # Actualizar datos básicos
    host.hostname = scan_data.get("hostname")
    if scan_data.get("mac"):
        host.mac = scan_data["mac"]
    if scan_data.get("vendor"):
        host.vendor = scan_data["vendor"]
    host.status = scan_data.get("status", "unknown")
    host.latency_ms = scan_data.get("latency_ms")
    host.last_seen = datetime.utcnow()
    
    # OS info
    os_info = scan_data.get("os")
    if os_info:
        host.os_name = os_info.get("name")
        host.os_accuracy = os_info.get("accuracy")
    
    db.commit()
    db.refresh(host)

# Notificar por WebSocket (en background para no bloquear)
    try:
        ws_manager = get_ws_manager()
        asyncio.create_task(ws_manager.broadcast("host_update", {
            "action": "created" if is_new else "updated",
            "host": {
                "id": host.id,
                "ip": host.ip,
                "hostname": host.hostname,
                "mac": host.mac,
                "vendor": host.vendor,
                "status": host.status,
                "latency_ms": host.latency_ms,
                "os_name": host.os_name,
                "os_accuracy": host.os_accuracy,
                "last_seen": host.last_seen.isoformat() if host.last_seen else None
            }
        }))
    except Exception as e:
        pass


    # Guardar puertos
    if "ports" in scan_data:
        for port_data in scan_data["ports"]:
            port = db.query(Port).filter(
                and_(
                    Port.host_id == host.id,
                    Port.port == port_data["port"],
                    Port.protocol == port_data.get("protocol", "tcp")
                )
            ).first()
            
            if not port:
                port = Port(
                    host_id=host.id,
                    port=port_data["port"],
                    protocol=port_data.get("protocol", "tcp"),
                    service=port_data.get("service"),
                    state="open"
                )
                db.add(port)
    
    # Guardar servicios
    if "services" in scan_data:
        for service_data in scan_data["services"]:
            service = db.query(Service).filter(
                and_(
                    Service.host_id == host.id,
                    Service.port == service_data["port"],
                    Service.protocol == service_data.get("protocol", "tcp")
                )
            ).first()
            
            if not service:
                service = Service(host_id=host.id)
            
            service.port = service_data["port"]
            service.protocol = service_data.get("protocol", "tcp")
            service.service_name = service_data.get("service")
            service.product = service_data.get("product")
            service.version = service_data.get("version")
            service.extra_info = service_data.get("extra")
            
            if not service.id:
                db.add(service)
    
    # Guardar vulnerabilidades
    if "vulnerabilities" in scan_data:
        for vuln_data in scan_data["vulnerabilities"]:
            vuln = Vulnerability(
                host_id=host.id,
                port=vuln_data.get("port"),
                script_name=vuln_data.get("script"),
                output=vuln_data.get("output"),
                severity=extract_severity(vuln_data.get("output", ""))
            )
            db.add(vuln)
    
    # Guardar en historial de conexiones
    history = ConnectionHistory(
        host_id=host.id,
        status=scan_data.get("status", "unknown"),
        latency_ms=scan_data.get("latency_ms")
    )
    db.add(history)
    
    db.commit()
    return host


def extract_severity(output: str) -> str:
    """Extrae la severidad de la salida de un script de vulnerabilidad"""
    output_lower = output.lower()
    if "critical" in output_lower:
        return "critical"
    elif "high" in output_lower:
        return "high"
    elif "medium" in output_lower:
        return "medium"
    elif "low" in output_lower:
        return "low"
    return "info"


def get_all_hosts(db: Session, skip: int = 0, limit: int = 1000):
    """Obtiene todos los hosts con sus relaciones"""
    return db.query(Host).offset(skip).limit(limit).all()


def get_host_by_ip(db: Session, ip: str):
    """Obtiene un host por su IP"""
    return db.query(Host).filter(Host.ip == ip).first()


def filter_hosts_by_ip_range(db: Session, start_ip: str, end_ip: str):
    """Filtra hosts por rango de IPs"""
    try:
        start = int(ipaddress.IPv4Address(start_ip))
        end = int(ipaddress.IPv4Address(end_ip))
        
        hosts = db.query(Host).all()
        filtered = []
        
        for host in hosts:
            try:
                host_int = int(ipaddress.IPv4Address(host.ip))
                if start <= host_int <= end:
                    filtered.append(host)
            except:
                continue
        
        return filtered
    except:
        return []


def filter_hosts_by_subnet(db: Session, subnet: str):
    """Filtra hosts por subnet (CIDR)"""
    try:
        network = ipaddress.ip_network(subnet, strict=False)
        hosts = db.query(Host).all()
        
        filtered = []
        for host in hosts:
            try:
                if ipaddress.ip_address(host.ip) in network:
                    filtered.append(host)
            except:
                continue
        
        return filtered
    except:
        return []


def search_hosts(db: Session, query: str):
    """Busca hosts por IP, hostname o vendor"""
    return db.query(Host).filter(
        or_(
            Host.ip.ilike(f"%{query}%"),
            Host.hostname.ilike(f"%{query}%"),
            Host.vendor.ilike(f"%{query}%")
        )
    ).all()


def delete_host(db: Session, ip: str):
    """Elimina un host por su IP"""
    host = db.query(Host).filter(Host.ip == ip).first()
    if host:
        db.delete(host)
        db.commit()
        return True
    return False


def get_host_statistics(db: Session):
    """Obtiene estadísticas generales"""
    total = db.query(Host).count()
    online = db.query(Host).filter(Host.status == "up").count()
    offline = db.query(Host).filter(Host.status == "down").count()
    
    return {
        "total": total,
        "online": online,
        "offline": offline,
        "unknown": total - online - offline
    }

def mark_host_as_down(db: Session, ip: str):
    """Marca un host como down (útil después de apagarlo)"""
    host = db.query(Host).filter(Host.ip == ip).first()
    if host:
        host.status = "down"
        host.last_seen = datetime.utcnow()
        
        # Guardar en historial
        history = ConnectionHistory(
            host_id=host.id,
            status="down",
            latency_ms=None
        )
        db.add(history)
        
        db.commit()
        return True
    return False


def mark_multiple_hosts_as_down(db: Session, ips: List[str]):
    """Marca múltiples hosts como down"""
    for ip in ips:
        mark_host_as_down(db, ip)
    db.commit()