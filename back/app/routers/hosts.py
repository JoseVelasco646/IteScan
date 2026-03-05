import csv
from io import StringIO

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc

from app.database import get_db, Host
from app.database import Port, Service, Vulnerability
from app import crud
from app.models import FullScanHistory, ScanSchedule
from app.auth import require_role
from app.schemas import (
    DeleteHostRequest, DeleteHostsRequest, UpdateNicknameRequest
)
from app.utils import audit_log, host_to_dict

router = APIRouter()


@router.get("/hosts")
async def get_hosts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    total = crud.count_all_hosts(db)
    hosts = crud.get_all_hosts(db, skip, limit)
    return {
        "total": total,
        "page": skip // limit + 1 if limit > 0 else 1,
        "page_size": limit,
        "items": [host_to_dict(host) for host in hosts]
    }


@router.get("/hosts/{ip}")
async def get_host(ip: str, db: Session = Depends(get_db)):
    host = crud.get_host_by_ip(db, ip)
    if not host:
        raise HTTPException(status_code=404, detail="Host no encontrado")
    return host_to_dict(host)


@router.get("/hosts/filter/range")
async def filter_by_range(start_ip: str, end_ip: str, db: Session = Depends(get_db)):
    hosts = crud.filter_hosts_by_ip_range(db, start_ip, end_ip)
    return [host_to_dict(host) for host in hosts]


@router.get("/hosts/filter/subnet")
async def filter_by_subnet(subnet: str, db: Session = Depends(get_db)):
    hosts = crud.filter_hosts_by_subnet(db, subnet)
    return [host_to_dict(host) for host in hosts]


@router.get("/hosts/search/{query}")
async def search(query: str, db: Session = Depends(get_db)):
    hosts = crud.search_hosts(db, query)
    return [host_to_dict(host) for host in hosts]


@router.delete("/hosts/{ip:path}")
async def delete_host(ip: str, request: Request, db: Session = Depends(get_db), _role=Depends(require_role("mod"))):
    clean_ip = ip.split('/')[0].strip()
    success = crud.delete_host(db, clean_ip)
    if not success:
        raise HTTPException(status_code=404, detail="Host no encontrado")
    audit_log(db, request, "delete", "host", f"Host eliminado: {clean_ip}", {"ip": clean_ip})
    return {"message": "Host deleted successfully"}


@router.post("/hosts/delete")
async def delete_host_post(data: DeleteHostRequest, request: Request, db: Session = Depends(get_db), _role=Depends(require_role("mod"))):
    clean_ip = data.ip.split('/')[0].strip()
    success = crud.delete_host(db, clean_ip)
    if not success:
        raise HTTPException(status_code=404, detail="Host no encontrado")
    audit_log(db, request, "delete", "host", f"Host eliminado: {clean_ip}", {"ip": clean_ip})
    return {"message": "Host deleted successfully"}


@router.post("/hosts/nickname")
async def update_host_nickname(data: UpdateNicknameRequest, request: Request, db: Session = Depends(get_db), _role=Depends(require_role("mod"))):
    host = crud.update_host_nickname(db, data.ip, data.nickname)
    if not host:
        raise HTTPException(status_code=404, detail="Host no encontrado")
    audit_log(db, request, "update", "host", f"Nickname actualizado: {data.ip} -> '{data.nickname}'", {"ip": data.ip, "nickname": data.nickname})
    return {"message": "Nickname updated successfully", "host": host_to_dict(host)}


@router.post("/hosts/delete-batch")
async def delete_hosts_batch(data: DeleteHostsRequest, request: Request, db: Session = Depends(get_db), _role=Depends(require_role("mod"))):
    deleted = 0
    failed = 0
    for ip in data.ips:
        clean_ip = ip.split('/')[0].strip()
        if crud.delete_host(db, clean_ip):
            deleted += 1
        else:
            failed += 1
    audit_log(db, request, "delete", "host", f"Eliminación masiva: {deleted} hosts eliminados", {"deleted": deleted, "failed": failed, "ips": data.ips})
    return {"deleted": deleted, "failed": failed}


@router.get("/statistics")
async def get_statistics(db: Session = Depends(get_db)):
    return crud.get_host_statistics(db)

@router.get("/export/csv")
async def export_csv(db: Session = Depends(get_db)):
    hosts = crud.get_all_hosts(db)

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow([
        'IP', 'Hostname', 'Apodo', 'MAC', 'Vendor', 'OS', 'Status',
        'Latency (ms)', 'Last Seen', 'Ports', 'Services'
    ])

    for host in hosts:
        ports_str = ', '.join([f"{p.port}/{p.protocol}" for p in host.ports])
        services_str = ', '.join([f"{s.service_name}" for s in host.services])

        writer.writerow([
            host.ip,
            host.hostname or '',
            host.nickname or '',
            host.mac or '',
            host.vendor or '',
            host.os_name or '',
            host.status,
            host.latency_ms or '',
            host.last_seen or '',
            ports_str,
            services_str
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=network_scan.csv"}
    )


@router.get("/api/dashboard/summary")
async def get_dashboard_summary(db: Session = Depends(get_db)):

    total_hosts = db.query(Host).count()
    hosts_up = db.query(Host).filter(Host.status == "up").count()
    hosts_down = db.query(Host).filter(Host.status == "down").count()
    hosts_unknown = total_hosts - hosts_up - hosts_down

    total_ports = db.query(Port).count()
    total_services = db.query(Service).count()
    total_vulns = db.query(Vulnerability).count()

    vuln_by_severity = dict(
        db.query(Vulnerability.severity, sqlfunc.count(Vulnerability.id))
        .group_by(Vulnerability.severity).all()
    )

    recent_scans = db.query(FullScanHistory).order_by(
        FullScanHistory.created_at.desc()
    ).limit(5).all()

    active_schedules = db.query(ScanSchedule).filter(ScanSchedule.enabled == True).count()
    total_schedules = db.query(ScanSchedule).count()

    recent_hosts = db.query(Host).order_by(Host.last_seen.desc()).limit(5).all()

    return {
        "hosts": {
            "total": total_hosts,
            "up": hosts_up,
            "down": hosts_down,
            "unknown": hosts_unknown
        },
        "network": {
            "total_ports": total_ports,
            "total_services": total_services,
            "total_vulnerabilities": total_vulns,
            "vulnerabilities_by_severity": vuln_by_severity
        },
        "schedules": {
            "active": active_schedules,
            "total": total_schedules
        },
        "recent_scans": [
            {
                "id": s.id,
                "scan_type": s.scan_type,
                "target": s.target,
                "hosts_scanned": s.hosts_scanned,
                "hosts_active": s.hosts_active,
                "status": s.status,
                "duration_seconds": s.duration_seconds,
                "username": s.username,
                "created_at": s.created_at.isoformat() if s.created_at else None
            }
            for s in recent_scans
        ],
        "recent_hosts": [
            {
                "ip": str(h.ip).split('/')[0] if h.ip else None,
                "hostname": h.hostname,
                "nickname": h.nickname,
                "status": h.status,
                "os_name": h.os_name,
                "last_seen": h.last_seen.isoformat() if h.last_seen else None
            }
            for h in recent_hosts
        ]
    }
