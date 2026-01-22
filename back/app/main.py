from fastapi import FastAPI, Depends, HTTPException, Body, WebSocket, WebSocketDisconnect, Request
from pydantic import BaseModel, field_validator
from typing import List, Optional
from sqlalchemy.orm import Session
import asyncio
from contextlib import asynccontextmanager
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
import ipaddress
import os
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
import subprocess
import re
import json

import io
from app.ping import (
    ping_multiple,
    expand_network,
    scan_ports,
    scan_services,
    scan_vulnerabilities,
    detect_os,
    detect_os_segment,
    scan_mac,
    scan_ports_segment,
    scan_services_segment,
    full_host_scan,
    nmap_mac_sync
)
from fastapi.middleware.cors import CORSMiddleware
from app.database import get_db, create_tables, Host
from app import crud
from app.ssh_operations import shutdown_host_ssh, shutdown_ip_range, execute_command_ssh, reboot_host_ssh
from app.ssh_operations import test_ssh_connection
from app.schedule_routes import router as schedule_router
from app.websocket_manager import ws_manager
from app.ssh_terminal_manager import ssh_manager
import json

ENV_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', '.env')

MEXICO_TZ = ZoneInfo("America/Mexico_City")

def get_mexico_time():
    return datetime.now(MEXICO_TZ)

def update_env_file(key: str, value: str):
    try:
        if os.path.exists(ENV_FILE_PATH):
            with open(ENV_FILE_PATH, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        else:
            lines = []
        
        key_found = False
        new_lines = []
        for line in lines:
            if line.strip().startswith(f"{key}="):
                new_lines.append(f"{key}={value}\n")
                key_found = True
            else:
                new_lines.append(line)
        
        if not key_found:
            new_lines.append(f"{key}={value}\n")
        
        with open(ENV_FILE_PATH, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        logger.info(f"Archivo .env actualizado: {key}={value}")
        return True
    except Exception as e:
        logger.error(f"Error actualizando .env: {e}")
        return False

from app.scheduler_service import scheduler_service

# Funciones para manejar metadata de whitelist
def load_whitelist_metadata():
    try:
        if os.path.exists(WHITELIST_METADATA_FILE):
            with open(WHITELIST_METADATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error("error {e}")
    return {}

def save_whitelist_metadata(metadata):
    try:
        with open(WHITELIST_METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        return False

def get_client_ip(request: Request) -> str:
    client_ip = request.client.host
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    return client_ip

# Whitelist de IPs permitidas
IP_WHITELIST_STR = os.getenv("IP_WHITELIST", "192.168.0.9,192.168.0.9")
IP_WHITELIST = [ip.strip() for ip in IP_WHITELIST_STR.split(",") if ip.strip()]

# IPs administradoras que pueden agregar/eliminar de la whitelist
ADMIN_IPS_STR = os.getenv("ADMIN_IPS", "192.168.0.9,192.168.0.10")
ADMIN_IPS = [ip.strip() for ip in ADMIN_IPS_STR.split(",") if ip.strip()]

# Si la whitelist está vacía, permitir todas las IPs
WHITELIST_ENABLED = len(IP_WHITELIST) > 0

# Configurar logging para la whitelist
LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "whitelist_blocks.log")
WHITELIST_METADATA_FILE = os.path.join(os.path.dirname(__file__), "..", "whitelist_metadata.json")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# Configurar el logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Handler para archivo
file_handler = logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# Handler para consola
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

# Agregar handlers
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Registrar inicio del sistema de logging
logger.info("=" * 60)
logger.info("Sistema de logging de whitelist iniciado")
logger.info(f"Archivo de log: {LOG_FILE}")
logger.info("=" * 60)

# Función para obtener MAC y vendor (primero de BD, luego nmap)
def get_mac_and_vendor(ip: str, db: Session = None) -> tuple[Optional[str], str]:
    try:
        if db:
            from app.crud import get_host_by_ip
            host = get_host_by_ip(db, ip)
            if host and host.mac:
                vendor = host.vendor if host.vendor else "Desconocido"
                return (host.mac, vendor)
        
        devices = nmap_mac_sync(ip)
        if devices and len(devices) > 0:
            device = devices[0]
            mac = device.get('mac')
            vendor = device.get('vendor') or "Desconocido"
            return (mac, vendor) if mac else (None, "Desconocido")
        
        return (None, "Desconocido")
    except Exception as e:
        logger.debug(f"Error obteniendo MAC/vendor para {ip}: {e}")
        return (None, "Desconocido")

def check_ip_whitelist(request: Request):
    client_ip = request.client.host
    
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    
    if client_ip not in IP_WHITELIST:
        raise HTTPException(
            status_code=403,
            detail=f"Acceso denegado. Tu IP ({client_ip}) no está autorizada para usar este servicio."
        )
    
    return client_ip

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    if WHITELIST_ENABLED:
        print("whitelist")
        print("=" * 60)
        for ip in IP_WHITELIST:
            print(f"{ip}")
    else:
        print("ip permitidas")
    print("=" * 60)
    asyncio.create_task(scheduler_service.start())

    yield
    scheduler_service.stop()

app = FastAPI(title="Network Scanner API",docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)


# Cache para evitar alertas duplicadas de la misma IP (cooldown de 5 minutos)
blocked_ips_cache = {}
ALERT_COOLDOWN = 300  # 5 minutos en segundos

# Middleware para verificar whitelist de IPs
@app.middleware("http")
async def verify_ip_whitelist(request: Request, call_next):
    if request.url.path in ["/api/get-client-ip", "/api/check-whitelist-status"]:
        logger.debug(f"Permitiendo acceso a {request.url.path} desde {request.client.host}")
        response = await call_next(request)
        return response
    
    if WHITELIST_ENABLED:
        client_ip = request.client.host
        
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        logger.debug(f"Verificando IP: {client_ip} | Whitelist: {IP_WHITELIST}")
        
        if client_ip not in IP_WHITELIST:
            current_time = datetime.now().timestamp()
            last_alert_time = blocked_ips_cache.get(client_ip, 0)
            
            should_alert = (current_time - last_alert_time) > ALERT_COOLDOWN
            
            if should_alert:
                blocked_ips_cache[client_ip] = current_time
                
                async def process_block():
                    try:
                        db = next(get_db())
                        try:
                            mac_address, vendor = get_mac_and_vendor(client_ip, db)
                        finally:
                            db.close()
                        
                        block_info = {
                            "timestamp": get_mexico_time().isoformat(),
                            "ip": client_ip,
                            "mac": mac_address or "No disponible",
                            "vendor": vendor,
                            "path": request.url.path,
                            "method": request.method,
                            "user_agent": request.headers.get('User-Agent', 'Unknown')
                        }
                        
                        logger.warning(f"BLOCKED_ACCESS {json.dumps(block_info, ensure_ascii=False)}")
                        
                        await ws_manager.broadcast("blocked_access", {"attempt": block_info})
                    except Exception as e:
                        logger.error(f"Error procesando bloqueo: {e}")
                
                asyncio.create_task(process_block())
            
            return JSONResponse(
                status_code=403,
                content={
                    "detail": f"Acceso denegado. Tu IP ({client_ip}) no está autorizada.",
                    "ip": client_ip
                }
            )
    
    response = await call_next(request)
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket específico para monitoreo de whitelist
@app.websocket("/ws/whitelist")
async def whitelist_websocket(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == 'ping':
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        ws_manager.disconnect(websocket)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == 'ping':
                await websocket.send_text("pong")
            else:
                try:
                    message = json.loads(data)
                    if message.get('type') == 'cancel_scan':
                        scan_id = message.get('scan_id')
                        if scan_id:
                            ws_manager.cancel_scan(scan_id)
                            await websocket.send_text(json.dumps({
                                "type": "scan_cancelled",
                                "scan_id": scan_id
                            }))
                            # Broadcast a todos los clientes
                            await ws_manager.broadcast("scan_progress", {
                                "scan_id": scan_id,
                                "status": "cancelled",
                                "message": "Scan cancelled by user"
                            })
                except json.JSONDecodeError:
                    pass
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception as e:
        await ws_manager.disconnect(websocket)

app.include_router(schedule_router)


#modelos

class HostsRequest(BaseModel):
    hosts: List[str]
    host_timeout: int = 2  # Timeout en segundos por host
    
    @field_validator('hosts')
    @classmethod
    def validate_hosts(cls, v):
        validated = []
        invalid_hosts = []
        
        for host in v:
            host = host.strip()
            if not host:
                continue
            
            # Solo validar como IP
            try:
                ipaddress.ip_address(host)
                validated.append(host)
            except ValueError:
                invalid_hosts.append(host)
        
        if invalid_hosts:
            raise ValueError(f'IPs inválidas: {", ".join(invalid_hosts[:5])}')
        
        if not validated:
            raise ValueError('Al menos una IP válida es requerida')
        
        return validated

class NetworkRequest(BaseModel):
    cidr: str
    host_timeout: int = 2  # Timeout en segundos por host 
    
    @field_validator('cidr')
    @classmethod
    def validate_cidr(cls, v):
        try:
            ipaddress.ip_network(v, strict=False)
            return v
        except ValueError:
            raise ValueError(f'CIDR inválido: {v}. Formato esperado: 192.168.0.0/24')

class PortScanRequest(BaseModel):
    host: str
    ports: str = "1-1024"
    
    @field_validator('host')
    @classmethod
    def validate_host(cls, v):
        v = v.strip()
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError(f'IP inválida: {v}. Solo se aceptan direcciones IP válidas')

class ServiceScanRequest(BaseModel):
    host: str
    ports: str = "1-1024"
    
    @field_validator('host')
    @classmethod
    def validate_host(cls, v):
        v = v.strip()
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError(f'IP inválida: {v}. Solo se aceptan direcciones IP válidas')

class VulnScanRequest(BaseModel):
    host: str
    
    @field_validator('host')
    @classmethod
    def validate_host(cls, v):
        v = v.strip()
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError(f'IP inválida: {v}. Solo se aceptan direcciones IP válidas')

class OSRequest(BaseModel):
    host: str
    
    @field_validator('host')
    @classmethod
    def validate_host(cls, v):
        v = v.strip()
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError(f'IP inválida: {v}. Solo se aceptan direcciones IP válidas')

class OSSegmentRequest(BaseModel):
    hosts: List[str]
    host_timeout: int = 60  
    
    @field_validator('hosts')
    @classmethod
    def validate_hosts(cls, v):
        validated = []
        invalid_hosts = []
        for host in v:
            host = host.strip()
            try:
                ipaddress.ip_address(host)
                validated.append(host)
                continue
            except ValueError:
                pass
            
            try:
                ipaddress.ip_network(host, strict=False)
                validated.append(host)
                continue
            except ValueError:
                invalid_hosts.append(host)
        
        if invalid_hosts:
            raise ValueError(f'IPs/CIDRs inválidos: {", ".join(invalid_hosts[:5])}')
        if not validated:
            raise ValueError('Al menos una IP o CIDR válido es requerido')
        return validated

class MacScanRequest(BaseModel):
    cidr: str
    host_timeout: int = 8 
    
    @field_validator('cidr')
    @classmethod
    def validate_cidr(cls, v):
        try:
            ipaddress.ip_network(v, strict=False)
            return v
        except ValueError:
            raise ValueError(f'CIDR inválido: {v}')

class PortSegmentScanRequest(BaseModel):
    hosts: List[str]
    ports: str = "1-1024"
    host_timeout: int = 45 
    
    @field_validator('hosts')
    @classmethod
    def validate_hosts(cls, v):
        validated = []
        invalid_hosts = []
        for host in v:
            host = host.strip()
            try:
                ipaddress.ip_address(host)
                validated.append(host)
                continue
            except ValueError:
                pass
            
            try:
                ipaddress.ip_network(host, strict=False)
                validated.append(host)
                continue
            except ValueError:
                invalid_hosts.append(host)
        
        if invalid_hosts:
            raise ValueError(f'IPs/CIDRs inválidos: {", ".join(invalid_hosts[:5])}')
        if not validated:
            raise ValueError('Al menos una IP o CIDR válido es requerido')
        return validated

class ServiceSegmentScanRequest(BaseModel):
    hosts: List[str]
    ports: str = "1-1024"
    host_timeout: int = 120
    
    @field_validator('hosts')
    @classmethod
    def validate_hosts(cls, v):
        validated = []
        invalid_hosts = []
        for host in v:
            host = host.strip()
            try:
                ipaddress.ip_address(host)
                validated.append(host)
                continue
            except ValueError:
                pass
            
            try:
                ipaddress.ip_network(host, strict=False)
                validated.append(host)
                continue
            except ValueError:
                invalid_hosts.append(host)
        
        if invalid_hosts:
            raise ValueError(f'IPs/CIDRs inválidos: {", ".join(invalid_hosts[:5])}')
        if not validated:
            raise ValueError('Al menos una IP o CIDR válido es requerido')
        return validated

class FullScanRequest(BaseModel):
    host: str
    save_to_db: bool = True
    host_timeout: int = 120   
    
    @field_validator('host')
    @classmethod
    def validate_host(cls, v):
        v = v.strip()
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError(f'IP inválida: {v}. Solo se aceptan direcciones IP válidas')

class SSHShutdownRequest(BaseModel):
    host: str
    username: str
    password: Optional[str] = None
    key_file: Optional[str] = None
    sudo_password: Optional[str] = None
    os_type: str = "linux"
    
    @field_validator('host')
    @classmethod
    def validate_host(cls, v):
        v = v.strip()
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError(f'IP inválida: {v}. Se requiere una dirección IP válida')

class SSHRangeShutdownRequest(BaseModel):
    start_ip: str
    end_ip: str
    username: str
    password: Optional[str] = None
    key_file: Optional[str] = None
    sudo_password: Optional[str] = None
    os_type: str = "linux"
    
    @field_validator('start_ip', 'end_ip')
    @classmethod
    def validate_ip(cls, v):
        v = v.strip()
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError(f'IP inválida: {v}. Se requiere una dirección IP válida')

class IPRangeFilter(BaseModel):
    start_ip: str
    end_ip: str

class SubnetFilter(BaseModel):
    subnet: str


#endpoints

@app.get("/api/get-client-ip")
async def get_client_ip_endpoint(request: Request):
    client_ip = request.client.host
    
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    
    return {"ip": client_ip}

@app.get("/api/check-whitelist-status")
async def check_whitelist_status(request: Request):
    client_ip = request.client.host
    
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    
    is_whitelisted = client_ip in IP_WHITELIST
    
    return {
        "ip": client_ip,
        "is_whitelisted": is_whitelisted,
        "whitelist_enabled": WHITELIST_ENABLED
    }

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Network Scanner API is running"}

@app.post("/ping")
async def ping_hosts(data: HostsRequest):
    import uuid
    scan_id = str(uuid.uuid4())
    results = await ping_multiple(data.hosts, emit_progress=True, scan_id=scan_id, resolve_hostname=False, host_timeout=data.host_timeout)
    return {"scan_id": scan_id, "results": results}


@app.post("/scan/network")
async def scan_network(data: NetworkRequest):
    import uuid
    scan_id = str(uuid.uuid4())
    hosts = expand_network(data.cidr)
    results = await ping_multiple(hosts, emit_progress=True, scan_id=scan_id, resolve_hostname = False, host_timeout=data.host_timeout)
    return {"scan_id": scan_id, "network": data.cidr, "results": results}


@app.post("/scan/ports")
async def scan_ports_endpoint(data: PortScanRequest):
    ports = await scan_ports(data.host, data.ports)
    return {"host": data.host, "ports": ports}


    
@app.post("/scan/ports/segment")
async def scan_ports_by_segment(data: PortSegmentScanRequest):
    import uuid
    scan_id = str(uuid.uuid4())
    
    expanded_hosts = []
    for host in data.hosts:
        if '/' in host:  # Es un CIDR
            expanded = expand_network(host)
            expanded_hosts.extend(expanded)
        else:  # Es una IP individual
            expanded_hosts.append(host)
    
    results = await scan_ports_segment(
        hosts=expanded_hosts,
        ports=data.ports,
        emit_progress=True,
        scan_id=scan_id,
        host_timeout=data.host_timeout
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
    
    # Expandir todos los hosts (incluye CIDRs)
    expanded_hosts = []
    for host in data.hosts:
        if '/' in host:  # Es un CIDR
            expanded = expand_network(host)
            expanded_hosts.extend(expanded)
        else:  # Es una IP individual
            expanded_hosts.append(host)
    
    results = await scan_services_segment(
        hosts=expanded_hosts,
        ports=data.ports,
        emit_progress=True,
        scan_id=scan_id,
        host_timeout=data.host_timeout
    )
    return {"scan_id": scan_id, "results": results}
    return {"scan_id": scan_id, "results": results}


@app.post("/scan/vulnerabilities")
async def scan_vulnerabilities_endpoint(data: VulnScanRequest):
    vulns = await scan_vulnerabilities(data.host)
    return {"host": data.host, "vulnerabilities": vulns}


@app.post("/scan/os")
async def detect_os_endpoint(data: OSRequest):
    os_data = await detect_os(data.host)
    return {"host": data.host, "os": os_data}

@app.post("/scan/os/segment")
async def detect_os_segment_endpoint(data: OSSegmentRequest):
    import uuid
    scan_id = str(uuid.uuid4())
    
    expanded_hosts = []
    for host in data.hosts:
        if '/' in host:  # Es un CIDR
            expanded = expand_network(host)
            expanded_hosts.extend(expanded)
        else:  # Es una IP individual
            expanded_hosts.append(host)
    
    results = await detect_os_segment(expanded_hosts, emit_progress=True, scan_id=scan_id, host_timeout=data.host_timeout)
    return {"scan_id": scan_id, "results": results}


@app.post("/scan/mac")
async def scan_mac_endpoint(data: MacScanRequest):
    import uuid
    scan_id = str(uuid.uuid4())
    devices = await scan_mac(data.cidr, emit_progress=True, scan_id=scan_id, host_timeout=data.host_timeout)
    return {"scan_id": scan_id, "network": data.cidr, "devices": devices}

@app.post("/scan/full")
async def full_scan_endpoint(data: FullScanRequest, db: Session = Depends(get_db)):
    import uuid
    scan_id = str(uuid.uuid4())
    result = await full_host_scan(data.host, emit_progress=True, scan_id=scan_id, host_timeout=data.host_timeout)
    
    if data.save_to_db:
        crud.create_or_update_host(db, result)
    
    return {"scan_id": scan_id, "result": result}

@app.get("/hosts")
async def get_hosts(skip: int = 0, limit: int = 1000, db: Session = Depends(get_db)):
    hosts = crud.get_all_hosts(db, skip, limit)
    return [host_to_dict(host) for host in hosts]

@app.get("/hosts/{ip}")
async def get_host(ip: str, db: Session = Depends(get_db)):
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
    hosts = crud.search_hosts(db, query)
    return [host_to_dict(host) for host in hosts]

@app.delete("/hosts/{ip}")
async def delete_host(ip: str, db: Session = Depends(get_db)):
    success = crud.delete_host(db, ip)
    if not success:
        raise HTTPException(status_code=404, detail="Host not found")
    return {"message": "Host deleted successfully"}

@app.get("/statistics")
async def get_statistics(db: Session = Depends(get_db)):
    return crud.get_host_statistics(db)

# ssh endpoints
@app.post("/ssh/shutdown")
async def shutdown_host(data: SSHShutdownRequest,db: Session = Depends(get_db)):
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
async def shutdown_range(data: SSHRangeShutdownRequest, db: Session = Depends(get_db)):
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
    result = await reboot_host_ssh(
        data.host,
        data.username,
        data.password,
        data.key_file
    )
    return result


@app.post("/ssh/execute")
async def execute_ssh_command(
    host: str = Body(...),
    command: str = Body(...),
    username: str = Body(...),
    password: str = Body(...)
):
    result = await execute_command_ssh(host, command, username, password)
    return result


@app.post("/ssh/execute/multiple")
async def execute_ssh_command_multiple(
    hosts: List[str] = Body(...),
    command: str = Body(...),
    username: str = Body(...),
    password: str = Body(...)
):
    tasks = [execute_command_ssh(host, command, username, password) for host in hosts]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Formatear resultados
    formatted_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            formatted_results.append({
                "host": hosts[i],
                "success": False,
                "error": str(result)
            })
        else:
            formatted_results.append({
                "host": hosts[i],
                **result
            })
    
    return {"results": formatted_results}


# export csv
@app.get("/export/csv")
async def export_csv(db: Session = Depends(get_db)):
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

# utils
def host_to_dict(host: Host) -> dict:
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

#ssh terminal
@app.websocket("/ws/ssh/{session_id}")
async def ssh_terminal_websocket(websocket: WebSocket, session_id: str):
    await websocket.accept()
    
    session = None
    
    try:
        initial_data = await websocket.receive_text()
        initial_msg = json.loads(initial_data)
        
        if initial_msg.get('type') != 'connect':
            await websocket.send_json({
                'type': 'error',
                'message': 'Expected connect message'
            })
            await websocket.close()
            return
        
        host = initial_msg.get('host')
        username = initial_msg.get('username')
        password = initial_msg.get('password')
        port = initial_msg.get('port', 22)
        
        if not all([host, username, password]):
            await websocket.send_json({
                'type': 'error',
                'message': 'Missing credentials'
            })
            await websocket.close()
            return
        
        if not ssh_manager.create_session(session_id, host, username, password, port):
            await websocket.send_json({
                'type': 'error',
                'message': 'Failed to connect to SSH server'
            })
            await websocket.close()
            return
        
        session = ssh_manager.get_session(session_id)
        
        # Enviar confirmación de conexión
        await websocket.send_json({
            'type': 'connected',
            'message': f'Connected to {host}'
        })
        
        await asyncio.sleep(1.0)  # Dar más tiempo para el banner inicial
        initial_output = session.read_output(timeout=0.5)
        if initial_output:
            await websocket.send_json({
                'type': 'output',
                'data': initial_output
            })
        else:
            print("no iniciado")
        
        async def read_ssh_output():
            while session and session.connected:
                try:
                    output = await asyncio.to_thread(session.read_output, 0.3)
                    if output:
                        await websocket.send_json({
                            'type': 'output',
                            'data': output
                        })
                    await asyncio.sleep(0.2)  # Delay para no saturar
                except Exception as e:
                    print(f"❌ Error reading SSH output: {e}")
                    break
        
        read_task = asyncio.create_task(read_ssh_output())
        
        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                msg_type = message.get('type')
                
                if msg_type == 'input':
                    input_data = message.get('data', '')
                    session.write_input(input_data)
                    
                    await asyncio.sleep(0.3)
                    
                    immediate_output = await asyncio.to_thread(session.read_output, 0.5)
                    if immediate_output:
                        await websocket.send_json({
                            'type': 'output',
                            'data': immediate_output
                        })
                    
                elif msg_type == 'resize':
                    width = message.get('width', 120)
                    height = message.get('height', 30)
                    session.resize_pty(width, height)
                    
                elif msg_type == 'ping':
                    await websocket.send_json({'type': 'pong'})
                    
                elif msg_type == 'close':
                    break
                    
        finally:
            read_task.cancel()
            try:
                await read_task
            except asyncio.CancelledError:
                pass
                
    except WebSocketDisconnect:
        print("ssh diconected")
    except Exception as e:
        print(f"ssh websockekt error: {e}")
        try:
            await websocket.send_json({
                'type': 'error',
                'message': str(e)
            })
        except:
            pass
    finally:
        if session_id:
            ssh_manager.close_session(session_id)
        try:
            await websocket.close()
        except:
            pass


@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Backend running"}


#whitelist
@app.get("/api/whitelist")
async def get_whitelist(request: Request):
    metadata = load_whitelist_metadata()
    client_ip = get_client_ip(request)
    
    
    ips_with_metadata = []
    for ip in IP_WHITELIST:
        ip_info = metadata.get(ip, {})
        ips_with_metadata.append({
            "ip": ip,
            "added_by": ip_info.get("added_by", "Desconocido"),
            "added_at": ip_info.get("added_at", "Desconocido"),
            "is_admin": ip in ADMIN_IPS
        })
    
    return {
        "enabled": WHITELIST_ENABLED,
        "ips": IP_WHITELIST,
        "ips_metadata": ips_with_metadata,
        "total": len(IP_WHITELIST),
        "is_admin": client_ip in ADMIN_IPS,
        "admin_ips": ADMIN_IPS
    }


@app.post("/api/whitelist/add")
async def add_to_whitelist(request: Request, ip: str = Body(..., embed=True)):
    client_ip = get_client_ip(request)
    
    
    if client_ip not in ADMIN_IPS:
        logger.warning(f"Intento de agregar IP sin permisos desde: {client_ip}")
        raise HTTPException(
            status_code=403, 
            detail=f"Acceso denegado. Solo los administradores pueden agregar IPs a la whitelist. Tu IP: {client_ip}"
        )
    
    try:
        ipaddress.ip_address(ip)
        
        if ip in IP_WHITELIST:
            raise HTTPException(status_code=400, detail=f"La IP {ip} ya está en la whitelist")
        
        IP_WHITELIST.append(ip)
        
        metadata = load_whitelist_metadata()
        
        metadata[ip] = {
            "added_by": client_ip,
            "added_at": get_mexico_time().isoformat(),
            "is_admin": ip in ADMIN_IPS
        }
        
        save_whitelist_metadata(metadata)
        
        
        # Actualizar el archivo .env para que sea permanente
        whitelist_str = ",".join(IP_WHITELIST)
        update_env_file("IP_WHITELIST", whitelist_str)
        
        return {
            "success": True,
            "message": f"IP {ip} agregada correctamente por {client_ip}",
            "whitelist": IP_WHITELIST,
            "added_by": client_ip,
            "added_at": metadata[ip]["added_at"]
        }
    except ValueError:
        raise HTTPException(status_code=400, detail=f"{ip} no es una dirección IP válida")


@app.delete("/api/whitelist/remove/{ip}")
async def remove_from_whitelist(request: Request, ip: str):
    client_ip = get_client_ip(request)
    
    if client_ip not in ADMIN_IPS:
        raise HTTPException(
            status_code=403, 
            detail=f"Acceso denegado. Solo los administradores pueden eliminar IPs de la whitelist. Tu IP: {client_ip}"
        )
    
    if ip not in IP_WHITELIST:
        raise HTTPException(status_code=404, detail=f"La IP {ip} no está en la whitelist")
    
    if ip in ADMIN_IPS and ip == client_ip:
        admin_count = sum(1 for admin_ip in ADMIN_IPS if admin_ip in IP_WHITELIST)
        if admin_count <= 1:
            raise HTTPException(
                status_code=400, 
                detail="No puedes eliminarte a ti mismo si eres el único administrador en la whitelist"
            )
    
    IP_WHITELIST.remove(ip)
    
    metadata = load_whitelist_metadata()
    if ip in metadata:
        del metadata[ip]
        save_whitelist_metadata(metadata)
    
    
    whitelist_str = ",".join(IP_WHITELIST)
    update_env_file("IP_WHITELIST", whitelist_str)
    
    return {
        "success": True,
        "message": f"IP {ip} eliminada correctamente por {client_ip}",
        "whitelist": IP_WHITELIST
    }


@app.get("/api/whitelist/logs")
async def get_blocked_attempts():
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
            blocked_attempts = []
            for line in lines:
                if "BLOCKED_ACCESS" in line:
                    try:
                        json_start = line.index('{')
                        json_data = line[json_start:]
                        block_info = json.loads(json_data)
                        blocked_attempts.append(block_info)
                    except (ValueError, json.JSONDecodeError):
                        if "ACCESO BLOQUEADO" in line or "WARNING" in line:
                            blocked_attempts.append({
                                "timestamp": "N/A",
                                "ip": "N/A",
                                "mac": "N/A",
                                "vendor": "N/A",
                                "path": "N/A",
                                "method": "N/A",
                                "user_agent": "N/A",
                                "raw": line.strip()
                            })
            
            recent_attempts = blocked_attempts[-50:] if len(blocked_attempts) > 50 else blocked_attempts
            recent_attempts.reverse()
            
            return {
                "total_lines": len(lines),
                "total_blocked": len(blocked_attempts),
                "showing": len(recent_attempts),
                "attempts": recent_attempts,
                "log_file": LOG_FILE
            }
    except FileNotFoundError:
        return {
            "total_lines": 0,
            "total_blocked": 0,
            "showing": 0,
            "attempts": [],
            "message": f"Archivo de log no encontrado: {LOG_FILE}"
        }
    except Exception as e:
        return {
            "total_lines": 0,
            "total_blocked": 0,
            "showing": 0,
            "attempts": [],
            "error": str(e)
        }


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
