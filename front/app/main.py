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
from app.schedule_routes import calculate_next_run, create_schedule, list_schedules, get_schedule, update_schedule, delete_schedule, toggle_schedule, run_schedule_now, execute_scheduled_scan, execute_shutdown,shutdown_network_segment, shutdown_segment_background
from app.schedule_routes import router as schedule_router
from app.websocket_manager import ws_manager
from app.ssh_terminal_manager import ssh_manager
import json

# Ruta al archivo .env
ENV_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', '.env')

def update_env_file(key: str, value: str):
    """Actualizar una variable en el archivo .env"""
    try:
        # Leer el contenido actual del .env
        if os.path.exists(ENV_FILE_PATH):
            with open(ENV_FILE_PATH, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        else:
            lines = []
        
        # Buscar y actualizar la línea correspondiente
        key_found = False
        new_lines = []
        for line in lines:
            if line.strip().startswith(f"{key}="):
                new_lines.append(f"{key}={value}\n")
                key_found = True
            else:
                new_lines.append(line)
        
        # Si no se encontró, agregar al final
        if not key_found:
            new_lines.append(f"{key}={value}\n")
        
        # Escribir de vuelta al archivo
        with open(ENV_FILE_PATH, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        logger.info(f"✅ Archivo .env actualizado: {key}={value}")
        return True
    except Exception as e:
        logger.error(f"❌ Error actualizando .env: {e}")
        return False

from app.scheduler_service import scheduler_service

# Whitelist de IPs permitidas
IP_WHITELIST_STR = os.getenv("IP_WHITELIST", "192.168.0.5,192.168.0.6")
IP_WHITELIST = [ip.strip() for ip in IP_WHITELIST_STR.split(",") if ip.strip()]

# Si la whitelist está vacía, permitir todas las IPs
WHITELIST_ENABLED = len(IP_WHITELIST) > 0

# Configurar logging para la whitelist
LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "whitelist_blocks.log")
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
    """Obtiene MAC address y fabricante desde la BD o usando nmap"""
    try:
        # Primero intentar obtener de la base de datos (de escaneos previos)
        if db:
            from app.crud import get_host_by_ip
            host = get_host_by_ip(db, ip)
            if host and host.mac:
                vendor = host.vendor if host.vendor else "Desconocido"
                return (host.mac, vendor)
        
        # Si no está en BD, intentar con nmap
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

# Función para verificar si una IP está en la whitelist
def check_ip_whitelist(request: Request):
    """Verifica si la IP del cliente está en la whitelist"""
    # Obtener IP del cliente
    client_ip = request.client.host
    
    # Si está detrás de un proxy, obtener la IP real
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    
    # Verificar si está en la whitelist
    if client_ip not in IP_WHITELIST:
        raise HTTPException(
            status_code=403,
            detail=f"Acceso denegado. Tu IP ({client_ip}) no está autorizada para usar este servicio."
        )
    
    return client_ip

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    
    # Mostrar configuración de whitelist al iniciar
    print("=" * 60)
    if WHITELIST_ENABLED:
        print("🔒 WHITELIST DE IPs ACTIVADA")
        print("=" * 60)
        print("IPs autorizadas:")
        for ip in IP_WHITELIST:
            print(f"  ✓ {ip}")
    else:
        print("⚠️  WHITELIST DESACTIVADA - TODAS LAS IPs PERMITIDAS")
        print("=" * 60)
        print("Para activar la whitelist, configura IP_WHITELIST en .env")
    print("=" * 60)

    asyncio.create_task(scheduler_service.start())

    yield
    scheduler_service.stop()

app = FastAPI(title="Network Scanner API", lifespan=lifespan)

# Cache para evitar alertas duplicadas de la misma IP (cooldown de 5 minutos)
blocked_ips_cache = {}
ALERT_COOLDOWN = 300  # 5 minutos en segundos

# Middleware para verificar whitelist de IPs
@app.middleware("http")
async def verify_ip_whitelist(request: Request, call_next):
    """Middleware que verifica si la IP del cliente está en la whitelist"""
    
    # Permitir acceso al endpoint de obtener IP sin verificar whitelist (incluso para IPs bloqueadas)
    if request.url.path == "/api/get-client-ip":
        logger.debug(f"Permitiendo acceso a /api/get-client-ip desde {request.client.host}")
        response = await call_next(request)
        return response
    
    # Si la whitelist está habilitada, verificar TODAS las peticiones
    if WHITELIST_ENABLED:
        # Obtener IP del cliente
        client_ip = request.client.host
        
        # Si está detrás de un proxy, obtener la IP real
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        # Verificar si está en la whitelist
        if client_ip not in IP_WHITELIST:
            # Verificar si ya alertamos sobre esta IP recientemente
            current_time = datetime.now().timestamp()
            last_alert_time = blocked_ips_cache.get(client_ip, 0)
            
            # Solo generar alerta si han pasado más de ALERT_COOLDOWN segundos
            should_alert = (current_time - last_alert_time) > ALERT_COOLDOWN
            
            if should_alert:
                # Actualizar el tiempo de última alerta para esta IP
                blocked_ips_cache[client_ip] = current_time
                
                # Procesar el bloqueo de forma asíncrona para no trabar el servidor
                async def process_block():
                    try:
                        db = next(get_db())
                        try:
                            # Obtener información adicional del dispositivo (solo de BD, sin nmap para ser más rápido)
                            mac_address, vendor = get_mac_and_vendor(client_ip, db)
                        finally:
                            db.close()
                        
                        # Crear objeto JSON con toda la información
                        block_info = {
                            "timestamp": datetime.now().isoformat(),
                            "ip": client_ip,
                            "mac": mac_address or "No disponible",
                            "vendor": vendor,
                            "path": request.url.path,
                            "method": request.method,
                            "user_agent": request.headers.get('User-Agent', 'Unknown')
                        }
                        
                        # Registrar intento bloqueado en formato JSON
                        logger.warning(f"BLOCKED_ACCESS {json.dumps(block_info, ensure_ascii=False)}")
                        
                        # Enviar notificación en tiempo real a través de WebSocket
                        await ws_manager.broadcast("blocked_access", {"attempt": block_info})
                    except Exception as e:
                        logger.error(f"Error procesando bloqueo: {e}")
                
                # Ejecutar el procesamiento en segundo plano sin esperar
                asyncio.create_task(process_block())
            
            # Devolver respuesta inmediata sin esperar el procesamiento (siempre bloquear)
            # Mostrar página HTML personalizada de acceso denegado
            html_content = f"""
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Acceso Denegado - Network Scanner</title>
                <style>
                    * {{
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                    }}
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        min-height: 100vh;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        padding: 20px;
                    }}
                    .container {{
                        background: white;
                        border-radius: 20px;
                        padding: 60px 40px;
                        max-width: 600px;
                        text-align: center;
                        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                        animation: fadeIn 0.5s ease;
                    }}
                    @keyframes fadeIn {{
                        from {{ opacity: 0; transform: translateY(-20px); }}
                        to {{ opacity: 1; transform: translateY(0); }}
                    }}
                    .icon {{
                        font-size: 80px;
                        margin-bottom: 20px;
                        animation: shake 0.5s ease;
                    }}
                    @keyframes shake {{
                        0%, 100% {{ transform: rotate(0deg); }}
                        25% {{ transform: rotate(-10deg); }}
                        75% {{ transform: rotate(10deg); }}
                    }}
                    h1 {{
                        color: #dc2626;
                        font-size: 36px;
                        margin-bottom: 20px;
                        font-weight: 700;
                    }}
                    p {{
                        color: #4b5563;
                        font-size: 18px;
                        line-height: 1.6;
                        margin-bottom: 30px;
                    }}
                    .info-box {{
                        background: #f3f4f6;
                        border-left: 4px solid #dc2626;
                        padding: 20px;
                        margin: 30px 0;
                        text-align: left;
                        border-radius: 8px;
                    }}
                    .info-box strong {{
                        color: #1f2937;
                        display: block;
                        margin-bottom: 5px;
                    }}
                    .info-box code {{
                        background: #e5e7eb;
                        padding: 2px 8px;
                        border-radius: 4px;
                        font-family: 'Courier New', monospace;
                        color: #dc2626;
                    }}
                    .footer {{
                        margin-top: 30px;
                        color: #9ca3af;
                        font-size: 14px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="icon">🚫</div>
                    <h1>Acceso Denegado</h1>
                    <p>Tu dirección IP no está autorizada para acceder a este servicio.</p>
                    
                    <div class="info-box">
                        <strong>Tu IP:</strong>
                        <code>{client_ip}</code>
                        <br><br>
                        <strong>Razón:</strong>
                        Esta aplicación utiliza una lista blanca de IPs autorizadas. Tu dirección IP no se encuentra en la lista de dispositivos permitidos.
                    </div>
                    
                    <p>Si crees que deberías tener acceso, contacta al administrador del sistema.</p>
                    
                    <div class="footer">
                        Network Scanner © 2026 - Acceso Protegido
                    </div>
                </div>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content, status_code=403)
    
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
        print(f"Error en WebSocket whitelist: {e}")
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
                # Intentar parsear como JSON para otros mensajes
                try:
                    message = json.loads(data)
                    if message.get('type') == 'cancel_scan':
                        scan_id = message.get('scan_id')
                        if scan_id:
                            ws_manager.cancel_scan(scan_id)
                            # Enviar confirmación y broadcast de cancelación
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
            except ValueError:
                invalid_hosts.append(host)
        if invalid_hosts:
            raise ValueError(f'IPs inválidas: {", ".join(invalid_hosts[:5])}')
        if not validated:
            raise ValueError('Al menos una IP válida es requerida')
        return validated

class MacScanRequest(BaseModel):
    cidr: str
    
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
            except ValueError:
                invalid_hosts.append(host)
        if invalid_hosts:
            raise ValueError(f'IPs inválidas: {", ".join(invalid_hosts[:5])}')
        if not validated:
            raise ValueError('Al menos una IP válida es requerida')
        return validated

class ServiceSegmentScanRequest(BaseModel):
    hosts: List[str]
    ports: str = "1-1024"
    
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
            except ValueError:
                invalid_hosts.append(host)
        if invalid_hosts:
            raise ValueError(f'IPs inválidas: {", ".join(invalid_hosts[:5])}')
        if not validated:
            raise ValueError('Al menos una IP válida es requerida')
        return validated

class FullScanRequest(BaseModel):
    host: str
    save_to_db: bool = True
    
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
async def get_client_ip(request: Request):
    """Endpoint para obtener la IP del cliente (accesible incluso si está bloqueado)"""
    client_ip = request.client.host
    
    # Si está detrás de un proxy, obtener la IP real
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    
    return {"ip": client_ip}

@app.get("/health")
async def health_check():
    """Endpoint de health check - protegido por whitelist"""
    return {"status": "ok", "message": "Network Scanner API is running"}

@app.post("/ping")
async def ping_hosts(data: HostsRequest):
    import uuid
    scan_id = str(uuid.uuid4())
    results = await ping_multiple(data.hosts, emit_progress=True, scan_id=scan_id, resolve_hostname=False)
    return {"scan_id": scan_id, "results": results}


@app.post("/scan/network")
async def scan_network(data: NetworkRequest):
    import uuid
    scan_id = str(uuid.uuid4())
    hosts = expand_network(data.cidr)
    results = await ping_multiple(hosts, emit_progress=True, scan_id=scan_id, resolve_hostname = False)
    return {"scan_id": scan_id, "network": data.cidr, "results": results}


@app.post("/scan/ports")
async def scan_ports_endpoint(data: PortScanRequest):
    ports = await scan_ports(data.host, data.ports)
    return {"host": data.host, "ports": ports}


    
@app.post("/scan/ports/segment")
async def scan_ports_by_segment(data: PortSegmentScanRequest):
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
    
    results = await scan_ports_segment(
        hosts=expanded_hosts,
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
        scan_id=scan_id
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
    
    # Expandir todos los hosts (incluye CIDRs)
    expanded_hosts = []
    for host in data.hosts:
        if '/' in host:  # Es un CIDR
            expanded = expand_network(host)
            expanded_hosts.extend(expanded)
        else:  # Es una IP individual
            expanded_hosts.append(host)
    
    results = await detect_os_segment(expanded_hosts, emit_progress=True, scan_id=scan_id)
    return {"scan_id": scan_id, "results": results}


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
        crud.create_or_update_host(db, result)
    
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
async def shutdown_range(data: SSHRangeShutdownRequest, db: Session = Depends(get_db)):
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


@app.post("/ssh/execute")
async def execute_ssh_command(
    host: str = Body(...),
    command: str = Body(...),
    username: str = Body(...),
    password: str = Body(...)
):
    """Ejecuta un comando SSH en un host"""
    result = await execute_command_ssh(host, command, username, password)
    return result


@app.post("/ssh/execute/multiple")
async def execute_ssh_command_multiple(
    hosts: List[str] = Body(...),
    command: str = Body(...),
    username: str = Body(...),
    password: str = Body(...)
):
    """Ejecuta un comando SSH en múltiples hosts en paralelo"""
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

# ==================== SSH TERMINAL WEBSOCKET ====================

@app.websocket("/ws/ssh/{session_id}")
async def ssh_terminal_websocket(websocket: WebSocket, session_id: str):
    """WebSocket endpoint para terminal SSH interactiva en tiempo real"""
    await websocket.accept()
    
    session = None
    
    try:
        # Esperar mensaje de conexión inicial con credenciales
        initial_data = await websocket.receive_text()
        initial_msg = json.loads(initial_data)
        
        if initial_msg.get('type') != 'connect':
            await websocket.send_json({
                'type': 'error',
                'message': 'Expected connect message'
            })
            await websocket.close()
            return
        
        # Extraer credenciales
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
        
        # Crear sesión SSH
        print(f"🔌 Creating SSH session to {host}:{port} as {username}")
        if not ssh_manager.create_session(session_id, host, username, password, port):
            print(f"❌ Failed to connect to SSH server {host}")
            await websocket.send_json({
                'type': 'error',
                'message': 'Failed to connect to SSH server'
            })
            await websocket.close()
            return
        
        session = ssh_manager.get_session(session_id)
        print(f"✅ SSH session created successfully for {host}")
        
        # Enviar confirmación de conexión
        await websocket.send_json({
            'type': 'connected',
            'message': f'Connected to {host}'
        })
        
        # Enviar output inicial (banner, prompt, etc.)
        print(f"⏳ Waiting for initial output...")
        await asyncio.sleep(1.0)  # Dar más tiempo para el banner inicial
        initial_output = session.read_output(timeout=0.5)
        if initial_output:
            print(f"📤 Sending initial output: {initial_output[:100]}...")
            await websocket.send_json({
                'type': 'output',
                'data': initial_output
            })
        else:
            print("⚠️ No initial output received")
        
        # Loop principal: recibir input del cliente y enviar output
        async def read_ssh_output():
            """Tarea para leer continuamente el output SSH"""
            while session and session.connected:
                try:
                    output = await asyncio.to_thread(session.read_output, 0.3)
                    if output:
                        print(f"📤 Sending output: {output[:100]}...")
                        await websocket.send_json({
                            'type': 'output',
                            'data': output
                        })
                    await asyncio.sleep(0.2)  # Delay para no saturar
                except Exception as e:
                    print(f"❌ Error reading SSH output: {e}")
                    break
        
        # Iniciar tarea de lectura en background
        read_task = asyncio.create_task(read_ssh_output())
        
        try:
            while True:
                # Recibir comandos del cliente
                data = await websocket.receive_text()
                message = json.loads(data)
                
                msg_type = message.get('type')
                
                if msg_type == 'input':
                    # Enviar input al servidor SSH
                    input_data = message.get('data', '')
                    print(f"⌨️ Received input: {input_data.replace(chr(10), '\\n')[:50]}")
                    session.write_input(input_data)
                    
                    # Dar tiempo para que el comando se ejecute antes de leer
                    await asyncio.sleep(0.3)
                    
                    # Leer output inmediatamente después del comando
                    immediate_output = await asyncio.to_thread(session.read_output, 0.5)
                    if immediate_output:
                        print(f"📤 Sending immediate output: {immediate_output[:100]}...")
                        await websocket.send_json({
                            'type': 'output',
                            'data': immediate_output
                        })
                    
                elif msg_type == 'resize':
                    # Redimensionar terminal
                    width = message.get('width', 120)
                    height = message.get('height', 30)
                    session.resize_pty(width, height)
                    
                elif msg_type == 'ping':
                    await websocket.send_json({'type': 'pong'})
                    
                elif msg_type == 'close':
                    break
                    
        finally:
            # Cancelar tarea de lectura
            read_task.cancel()
            try:
                await read_task
            except asyncio.CancelledError:
                pass
                
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        print(f"Error in SSH WebSocket: {e}")
        try:
            await websocket.send_json({
                'type': 'error',
                'message': str(e)
            })
        except:
            pass
    finally:
        # Cerrar sesión SSH
        if session_id:
            ssh_manager.close_session(session_id)
        try:
            await websocket.close()
        except:
            pass


@app.get("/health")
async def health_check():
    """Endpoint de verificación de salud del servidor."""
    return {"status": "ok", "message": "Backend running"}


# ==================== Endpoints de Gestión de Whitelist ====================

@app.get("/api/whitelist")
async def get_whitelist(request: Request):
    """Obtener lista de IPs autorizadas."""
    return {
        "enabled": WHITELIST_ENABLED,
        "ips": IP_WHITELIST,
        "total": len(IP_WHITELIST)
    }


@app.post("/api/whitelist/add")
async def add_to_whitelist(request: Request, ip: str = Body(..., embed=True)):
    """Agregar una IP a la whitelist."""
    try:
        # Validar que sea una IP válida
        ipaddress.ip_address(ip)
        
        if ip in IP_WHITELIST:
            raise HTTPException(status_code=400, detail=f"La IP {ip} ya está en la whitelist")
        
        # Agregar a la lista en memoria
        IP_WHITELIST.append(ip)
        logger.info(f"✅ IP agregada a whitelist: {ip} por {request.client.host}")
        
        # Actualizar el archivo .env para que sea permanente
        whitelist_str = ",".join(IP_WHITELIST)
        update_env_file("IP_WHITELIST", whitelist_str)
        
        return {
            "success": True,
            "message": f"IP {ip} agregada correctamente y guardada en .env",
            "whitelist": IP_WHITELIST
        }
    except ValueError:
        raise HTTPException(status_code=400, detail=f"{ip} no es una dirección IP válida")


@app.delete("/api/whitelist/remove/{ip}")
async def remove_from_whitelist(request: Request, ip: str):
    """Eliminar una IP de la whitelist."""
    if ip not in IP_WHITELIST:
        raise HTTPException(status_code=404, detail=f"La IP {ip} no está en la whitelist")
    
    # Eliminar de la lista en memoria
    IP_WHITELIST.remove(ip)
    logger.info(f"🗑️ IP eliminada de whitelist: {ip} por {request.client.host}")
    
    # Actualizar el archivo .env para que sea permanente
    whitelist_str = ",".join(IP_WHITELIST)
    update_env_file("IP_WHITELIST", whitelist_str)
    
    return {
        "success": True,
        "message": f"IP {ip} eliminada correctamente y actualizada en .env",
        "whitelist": IP_WHITELIST
    }


@app.get("/api/whitelist/logs")
async def get_blocked_attempts():
    """Obtener últimos intentos bloqueados del log."""
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
            # Procesar las líneas y extraer información estructurada
            blocked_attempts = []
            for line in lines:
                if "BLOCKED_ACCESS" in line:
                    try:
                        # Extraer el JSON del log
                        json_start = line.index('{')
                        json_data = line[json_start:]
                        block_info = json.loads(json_data)
                        blocked_attempts.append(block_info)
                    except (ValueError, json.JSONDecodeError):
                        # Si no se puede parsear como JSON, mantener formato antiguo
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
            
            # Obtener los últimos 50 intentos
            recent_attempts = blocked_attempts[-50:] if len(blocked_attempts) > 50 else blocked_attempts
            # Invertir para mostrar los más recientes primero
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