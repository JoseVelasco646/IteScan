from fastapi import FastAPI, Depends, HTTPException, Body, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
import asyncio
from contextlib import asynccontextmanager
from fastapi.responses import StreamingResponse

import io
from app.ping import (
    ping_multiple,
    expand_network,
    scan_ports,
    scan_services,
    scan_vulnerabilities,
    detect_os,
    scan_mac,
    scan_ports_segment,
    scan_services_segment,
    full_host_scan
)
from fastapi.middleware.cors import CORSMiddleware
from app.database import get_db, create_tables, Host
from app import crud
from app.ssh_operations import shutdown_host_ssh, shutdown_ip_range, execute_command_ssh
from app.ssh_operations import test_ssh_connection
from app.schedule_routes import calculate_next_run, create_schedule, list_schedules, get_schedule, update_schedule, delete_schedule, toggle_schedule, run_schedule_now, execute_scheduled_scan, execute_shutdown,shutdown_network_segment, shutdown_segment_background
from app.schedule_routes import router as schedule_router
from app.websocket_manager import ws_manager





from app.scheduler_service import scheduler_service
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    print("iniciando network")

    asyncio.create_task(scheduler_service.start())

    yield
    scheduler_service.stop()

app = FastAPI(title="Network Scanner API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data =='ping':
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception as e:
        print("erorr en websocet")
        await ws_manager.disconnect(websocket)

app.include_router(schedule_router)


#modelos

class HostsRequest(BaseModel):
    hosts: List[str]

class NetworkRequest(BaseModel):
    cidr: str

class PortScanRequest(BaseModel):
    host: str
    ports: str = "1-1024"

class ServiceScanRequest(BaseModel):
    host: str
    ports: str = "1-1024"

class VulnScanRequest(BaseModel):
    host: str

class OSRequest(BaseModel):
    host: str

class MacScanRequest(BaseModel):
    cidr: str

class PortSegmentScanRequest(BaseModel):
    hosts: List[str]
    ports: str = "1-1024"

class ServiceSegmentScanRequest(BaseModel):
    hosts: List[str]
    ports: str = "1-1024"

class FullScanRequest(BaseModel):
    host: str
    save_to_db: bool = True

class SSHShutdownRequest(BaseModel):
    host: str
    username: str
    password: Optional[str] = None
    key_file: Optional[str] = None
    sudo_password: Optional[str] = None
    os_type: str = "linux" 

class SSHRangeShutdownRequest(BaseModel):
    start_ip: str
    end_ip: str
    username: str
    password: Optional[str] = None
    key_file: Optional[str] = None
    sudo_password: Optional[str] = None
    os_type: str = "linux"

class IPRangeFilter(BaseModel):
    start_ip: str
    end_ip: str

class SubnetFilter(BaseModel):
    subnet: str


#endpoints


@app.post("/ping")
async def ping_hosts(data: HostsRequest):
    import uuid
    scan_id = str(uuid.uuid4())
    results = await ping_multiple(data.hosts, emit_progress=True, scan_id=scan_id)
    return {"scan_id": scan_id, "results": results}


@app.post("/scan/network")
async def scan_network(data: NetworkRequest):
    import uuid
    scan_id = str(uuid.uuid4())
    hosts = expand_network(data.cidr)
    results = await ping_multiple(hosts, emit_progress=True, scan_id=scan_id)
    return {"scan_id": scan_id, "network": data.cidr, "results": results}


@app.post("/scan/ports")
async def scan_ports_endpoint(data: PortScanRequest):
    ports = await scan_ports(data.host, data.ports)
    return {"host": data.host, "ports": ports}


    
@app.post("/scan/ports/segment")
async def scan_ports_by_segment(data: PortSegmentScanRequest):
    import uuid
    scan_id = str(uuid.uuid4())
    results = await scan_ports_segment(
        hosts=data.hosts,
        ports=data.ports,
        emit_progress=True,
        scan_id=scan_id
    )
    return {"scan_id": scan_id, "results": results}

@app.post("/scan/services")
async def scan_services_endpoint(data: ServiceScanRequest):
    services = await scan_services(data.host, data.ports)
    return {"host": data.host, "services": services}

@app.post("/scan/services/segment")
async def scan_services_by_segment(data: ServiceSegmentScanRequest):
    import uuid
    scan_id = str(uuid.uuid4())
    results = await scan_services_segment(
        hosts=data.hosts,
        ports=data.ports,
        emit_progress=True,
        scan_id=scan_id
    )
    return {"scan_id": scan_id, "results": results}


@app.post("/scan/vulnerabilities")
async def scan_vulnerabilities_endpoint(data: VulnScanRequest):
    vulns = await scan_vulnerabilities(data.host)
    return {"host": data.host, "vulnerabilities": vulns}


@app.post("/scan/os")
async def detect_os_endpoint(data: OSRequest):
    os_data = await detect_os(data.host)
    return {"host": data.host, "os": os_data}


@app.post("/scan/mac")
async def scan_mac_endpoint(data: MacScanRequest):
    import uuid
    scan_id = str(uuid.uuid4())
    devices = await scan_mac(data.cidr, emit_progress=True, scan_id=scan_id)
    return {"scan_id": scan_id, "network": data.cidr, "devices": devices}

@app.post("/scan/full")
async def full_scan_endpoint(data: FullScanRequest, db: Session = Depends(get_db)):
    """Escaneo completo de un host y guardado en BD"""
    import uuid
    scan_id = str(uuid.uuid4())
    result = await full_host_scan(data.host, emit_progress=True, scan_id=scan_id)
    
    if data.save_to_db:
        await crud.create_or_update_host(db, result)
    
    return {"scan_id": scan_id, "result": result}

@app.get("/hosts")
async def get_hosts(skip: int = 0, limit: int = 1000, db: Session = Depends(get_db)):
    """Obtiene todos los hosts de la BD"""
    hosts = crud.get_all_hosts(db, skip, limit)
    return [host_to_dict(host) for host in hosts]

@app.get("/hosts/{ip}")
async def get_host(ip: str, db: Session = Depends(get_db)):
    """Obtiene un host específico"""
    host = crud.get_host_by_ip(db, ip)
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    return host_to_dict(host)

@app.get("/hosts/filter/range")
async def filter_by_range(start_ip: str, end_ip: str, db: Session = Depends(get_db)):
    hosts = crud.filter_hosts_by_ip_range(db, start_ip, end_ip)
    return [host_to_dict(host) for host in hosts]

@app.get("/hosts/filter/subnet")
async def filter_by_subnet(subnet: str, db: Session = Depends(get_db)):
    hosts = crud.filter_hosts_by_subnet(db, subnet)
    return [host_to_dict(host) for host in hosts]


@app.get("/hosts/search/{query}")
async def search(query: str, db: Session = Depends(get_db)):
    """Busca hosts por IP, hostname o vendor"""
    hosts = crud.search_hosts(db, query)
    return [host_to_dict(host) for host in hosts]

@app.delete("/hosts/{ip}")
async def delete_host(ip: str, db: Session = Depends(get_db)):
    """Elimina un host"""
    success = crud.delete_host(db, ip)
    if not success:
        raise HTTPException(status_code=404, detail="Host not found")
    return {"message": "Host deleted successfully"}

@app.get("/statistics")
async def get_statistics(db: Session = Depends(get_db)):
    """Obtiene estadísticas generales"""
    return crud.get_host_statistics(db)

# ==================== SSH ENDPOINTS ====================

@app.post("/ssh/shutdown")
async def shutdown_host(data: SSHShutdownRequest,db: Session = Depends(get_db)):
    """Apaga un host Windows via SSH"""
    result = await shutdown_host_ssh(
        data.host,
        data.username,
        data.password,
        data.key_file
    )
    if result.get("success"):
        crud.mark_host_as_down(db, data.host)
    return result


@app.post("/ssh/shutdown/range")
async def shutdown_range(data: SSHRangeShutdownRequest):
    """Apaga un rango de hosts Windows via SSH"""
    results = await shutdown_ip_range(
        data.start_ip,
        data.end_ip,
        data.username,
        data.password,
        data.key_file
    )
    successful_hosts = [r["host"] for r in results if r.get("success")]
    if successful_hosts:
        crud.mark_multiple_hosts_as_down(db, successful_hosts)
    return {"results": results}


@app.post("/ssh/test")
async def test_ssh(data: SSHShutdownRequest):
    result = await asyncio.to_thread(
        test_ssh_connection,
        data.host,
        data.username,
        data.password,
        data.key_file
    )
    return result


@app.post("/ssh/reboot")
async def reboot_host(data: SSHShutdownRequest):
    """Reinicia un host Windows via SSH"""
    result = await reboot_host_ssh(
        data.host,
        data.username,
        data.password,
        data.key_file
    )
    return result


# ==================== EXPORT ENDPOINTS ====================

@app.get("/export/csv")
async def export_csv(db: Session = Depends(get_db)):
    """Exporta hosts a CSV"""
    import csv
    from io import StringIO
    
    hosts = crud.get_all_hosts(db)
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'IP', 'Hostname', 'MAC', 'Vendor', 'OS', 'Status', 
        'Latency (ms)', 'Last Seen', 'Ports', 'Services'
    ])
    
    # Data
    for host in hosts:
        ports_str = ', '.join([f"{p.port}/{p.protocol}" for p in host.ports])
        services_str = ', '.join([f"{s.service_name}" for s in host.services])
        
        writer.writerow([
            host.ip,
            host.hostname or '',
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

# ==================== UTILIDADES ====================

def host_to_dict(host: Host) -> dict:
    """Convierte un objeto Host a diccionario"""
    return {
        "id": host.id,
        "ip": host.ip,
        "hostname": host.hostname,
        "mac": host.mac,
        "vendor": host.vendor,
        "os_name": host.os_name,
        "os_accuracy": host.os_accuracy,
        "status": host.status,
        "latency_ms": host.latency_ms,
        "last_seen": host.last_seen.isoformat() if host.last_seen else None,
        "ports": [
            {
                "port": p.port,
                "protocol": p.protocol,
                "service": p.service,
                "state": p.state
            }
            for p in host.ports
        ],
        "services": [
            {
                "port": s.port,
                "service": s.service_name,
                "product": s.product,
                "version": s.version
            }
            for s in host.services
        ],
        "vulnerabilities": [
            {
                "port": v.port,
                "script": v.script_name,
                "severity": v.severity,
                "output": v.output
            }
            for v in host.vulnerabilities
        ]
    }

@app.get("/health")
async def healt_check():
    return {"status": "ok", "message": "Bacnked running"}

@app.get("/")
async def root():
    return {
        "message": "Network Scanner API",
        "version": "2.0",
        "features": [
            "Host discovery",
            "Port scanning",
            "Service detection",
            "OS detection",
            "Vulnerability scanning",
            "Database storage",
            "SSH remote shutdown",
            "Data export (CSV)"
        ]
    }
