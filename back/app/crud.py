from sqlalchemy.orm import Session, joinedload, subqueryload
from sqlalchemy import and_, or_, cast, String, func, text
from datetime import datetime, timezone
from app.database import Host, Port, Service, Vulnerability, ConnectionHistory
from typing import List, Optional
import ipaddress
import asyncio

def get_ws_manager():
    from app.websocket_manager import ws_manager
    return ws_manager

def clean_ip(ip_str: str) -> str:
    if ip_str and '/' in str(ip_str):
        return str(ip_str).split('/')[0]
    return str(ip_str).strip() if ip_str else ip_str

def create_or_update_host(db: Session, scan_data: dict):
    ip = clean_ip(scan_data["host"])
    
    host = _find_host_by_ip(db, ip)
    is_new = host is None

    if not host:
        host = Host(ip=ip)
        db.add(host)
    
    host.hostname = scan_data.get("hostname")
    if scan_data.get("mac"):
        host.mac = scan_data["mac"]
    if scan_data.get("vendor"):
        host.vendor = scan_data["vendor"]
    host.status = scan_data.get("status", "unknown")
    host.latency_ms = scan_data.get("latency_ms")
    host.last_seen = datetime.now(timezone.utc)
    
    os_info = scan_data.get("os")
    if os_info:
        host.os_name = os_info.get("name")
        host.os_accuracy = os_info.get("accuracy")
    
    db.commit()
    db.refresh(host)

    try:
        ws_manager = get_ws_manager()
        asyncio.create_task(ws_manager.broadcast("host_update", {
            "action": "created" if is_new else "updated",
            "host": {
                "id": host.id,
                "ip": clean_ip(host.ip),
                "hostname": host.hostname,
                "nickname": host.nickname,
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
    return db.query(Host).options(
        subqueryload(Host.ports),
        subqueryload(Host.services),
        subqueryload(Host.vulnerabilities)
    ).offset(skip).limit(limit).all()


def count_all_hosts(db: Session) -> int:
    return db.query(Host).count()


def _find_host_by_ip(db: Session, ip: str):
    ip = clean_ip(ip)
    host = db.query(Host).filter(
        func.split_part(cast(Host.ip, String), '/', 1) == ip
    ).first()
    return host


def get_host_by_ip(db: Session, ip: str):
    return _find_host_by_ip(db, ip)


def filter_hosts_by_ip_range(db: Session, start_ip: str, end_ip: str):
    try:
        ipaddress.IPv4Address(start_ip)
        ipaddress.IPv4Address(end_ip)
        return db.query(Host).options(
            joinedload(Host.ports),
            joinedload(Host.services),
            joinedload(Host.vulnerabilities)
        ).filter(
            cast(Host.ip, String).op('::inet') >= text(f"'{start_ip}'::inet"),
            cast(Host.ip, String).op('::inet') <= text(f"'{end_ip}'::inet")
        ).all()
    except Exception:
        return []


def filter_hosts_by_subnet(db: Session, subnet: str):
    try:
        ipaddress.ip_network(subnet, strict=False)
        return db.query(Host).options(
            joinedload(Host.ports),
            joinedload(Host.services),
            joinedload(Host.vulnerabilities)
        ).filter(
            text(f"ip::inet <<= '{subnet}'::inet")
        ).all()
    except Exception:
        return []


def search_hosts(db: Session, query: str):
    return db.query(Host).filter(
        or_(
            cast(Host.ip, String).ilike(f"%{query}%"),
            Host.hostname.ilike(f"%{query}%"),
            Host.nickname.ilike(f"%{query}%"),
            Host.vendor.ilike(f"%{query}%")
        )
    ).all()


def update_host_nickname(db: Session, ip: str, nickname: str):
    ip = clean_ip(ip)
    host = _find_host_by_ip(db, ip)
    if host:
        host.nickname = nickname if nickname and nickname.strip() else None
        db.commit()
        db.refresh(host)
        return host
    return None


def delete_host(db: Session, ip: str):
    ip = clean_ip(ip)
    host = _find_host_by_ip(db, ip)
    if host:
        db.delete(host)
        db.commit()
        return True
    return False


def get_host_statistics(db: Session):
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
    ip = clean_ip(ip)
    host = _find_host_by_ip(db, ip)
    if host:
        host.status = "down"
        host.last_seen = datetime.now(timezone.utc)
        
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
    clean_ips = [clean_ip(ip) for ip in ips]
    # Bulk update in a single query
    db.query(Host).filter(
        func.split_part(cast(Host.ip, String), '/', 1).in_(clean_ips)
    ).update({Host.status: "down", Host.last_seen: datetime.now(timezone.utc)}, synchronize_session='fetch')
    db.commit()
