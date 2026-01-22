import asyncio
import subprocess
import time
import ipaddress
import nmap
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import socket

# Import del WebSocket manager
def get_ws_manager():
    try:
        from app.websocket_manager import ws_manager
        return ws_manager
    except:
        return None

# ================== HOSTNAME RESOLUTION ==================
def get_hostname(ip: str) -> str:
    """Obtiene el hostname de una IP usando múltiples métodos"""
    hostname = None
    
    # Método 1: gethostbyaddr
    try:
        hostname = socket.gethostbyaddr(ip)[0]
        if hostname and hostname != ip:
            return hostname
    except:
        pass
    
    # Método 2: nmap hostname detection
    try:
        scanner = nmap.PortScanner()
        scanner.scan(hosts=ip, arguments="-sn")
        if ip in scanner.all_hosts():
            for hostname_entry in scanner[ip].get('hostnames', []):
                name = hostname_entry.get('name', '')
                if name and name != ip:
                    return name
    except:
        pass
    
    # Método 3: NetBIOS name (Windows)
    try:
        import subprocess
        result = subprocess.run(
            ['nmblookup', '-A', ip],
            capture_output=True,
            text=True,
            timeout=2
        )
        for line in result.stdout.split('\n'):
            if '<00>' in line and 'GROUP' not in line:
                hostname = line.split()[0].strip()
                if hostname and hostname != ip:
                    return hostname
    except:
        pass
    
    return None


async def get_hostname_async(ip: str):
    """Versión async de get_hostname"""
    return await asyncio.to_thread(get_hostname, ip)



def expand_targets(hosts: list[str]) -> list[str]:
    expanded = []

    for h in hosts:
        if "/" in h:
            net = ipaddress.ip_network(h, strict=False)
            expanded.extend([str(ip) for ip in net.hosts()])
        else:
            expanded.append(h)

    return expanded



def expand_network(cidr: str) -> list[str]:
    net = ipaddress.ip_network(cidr, strict=False)
    return [str(ip) for ip in net.hosts()]

# ================== PORT SCAN ==================
def nmap_ports_sync(host: str, ports: str = "1-1024"):
    scanner = nmap.PortScanner()
    scanner.scan(hosts=host, ports=ports, arguments="-sS")

    open_ports = []

    if host in scanner.all_hosts():
        for proto in scanner[host].all_protocols():
            for port, data in scanner[host][proto].items():
                if data.get("state") == "open":
                    open_ports.append({
                        "port": port,
                        "protocol": proto,
                        "service": data.get("name")
                    })

    return open_ports


async def scan_ports(host: str, ports: str = "1-1024"):
    return await asyncio.to_thread(nmap_ports_sync, host, ports)

async def scan_ports_segment(hosts: list[str], ports: str = "1-1024", emit_progress: bool = True, scan_id: str = None):
    results = []
    total = len(hosts)
    ws_manager = get_ws_manager() if emit_progress else None
    
    if ws_manager and scan_id:
        await ws_manager.broadcast("scan_progress", {
            "scan_id": scan_id,
            "scan_type": "ports",
            "status": "started",
            "total": total,
            "completed": 0,
            "progress": 0
        })
    
    for index, host in enumerate(hosts):
        open_ports = await scan_ports(host, ports)
        if open_ports:
            result = {"host": host, "ports": open_ports}
            results.append(result)
            
            if ws_manager and scan_id:
                completed = index + 1
                progress = round((completed / total) * 100, 2)
                await ws_manager.broadcast("scan_progress", {
                    "scan_id": scan_id,
                    "scan_type": "ports",
                    "status": "scanning",
                    "total": total,
                    "completed": completed,
                    "progress": progress,
                    "current_host": host,
                    "result": result
                })
    
    if ws_manager and scan_id:
        await ws_manager.broadcast("scan_progress", {
            "scan_id": scan_id,
            "scan_type": "ports",
            "status": "completed",
            "total": total,
            "completed": total,
            "progress": 100,
            "results": results
        })

    return results



# ================== SERVICES & VERSIONS (-sV) ==================
def nmap_services_sync(host: str, ports: str = "1-1024"):
    scanner = nmap.PortScanner()
    scanner.scan(hosts=host, ports=ports, arguments="-sS -sV")

    services = []

    if host in scanner.all_hosts():
        for proto in scanner[host].all_protocols():
            for port, data in scanner[host][proto].items():
                if data.get("state") == "open":
                    services.append({
                        "port": port,
                        "protocol": proto,
                        "service": data.get("name"),
                        "product": data.get("product"),
                        "version": data.get("version"),
                        "extra": data.get("extrainfo")
                    })

    return services


async def scan_services(host: str, ports: str = "1-1024"):
    return await asyncio.to_thread(nmap_services_sync, host, ports)

async def scan_services_segment(hosts: list[str], ports: str = "1-1024", emit_progress: bool = True, scan_id: str = None):
    results = []
    expanded_hosts = expand_targets(hosts)
    total = len(expanded_hosts)
    ws_manager = get_ws_manager() if emit_progress else None
    
    if ws_manager and scan_id:
        await ws_manager.broadcast("scan_progress", {
            "scan_id": scan_id,
            "scan_type": "services",
            "status": "started",
            "total": total,
            "completed": 0,
            "progress": 0
        })

    for index, host in enumerate(expanded_hosts):
        services = await scan_services(host, ports)
        result = {"host": host, "services": services}
        results.append(result)
        
        if ws_manager and scan_id:
            completed = index + 1
            progress = round((completed / total) * 100, 2)
            await ws_manager.broadcast("scan_progress", {
                "scan_id": scan_id,
                "scan_type": "services",
                "status": "scanning",
                "total": total,
                "completed": completed,
                "progress": progress,
                "current_host": host,
                "result": result
            })
    
    if ws_manager and scan_id:
        await ws_manager.broadcast("scan_progress", {
            "scan_id": scan_id,
            "scan_type": "services",
            "status": "completed",
            "total": total,
            "completed": total,
            "progress": 100,
            "results": results
        })

    return results



# ================== OS DETECTION ==================
def nmap_os_sync(host: str):
    scanner = nmap.PortScanner()
    scanner.scan(hosts=host, arguments="-O")

    if host in scanner.all_hosts():
        matches = scanner[host].get("osmatch", [])
        if matches:
            best = matches[0]
            return {
                "name": best.get("name"),
                "accuracy": best.get("accuracy")
            }

    return None


async def detect_os(host: str):
    return await asyncio.to_thread(nmap_os_sync, host)

async def detect_os_segment(hosts: list[str], emit_progress: bool = True, scan_id: str = None):
    results = []
    total = len(hosts)
    ws_manager = get_ws_manager() if emit_progress else None
    
    if ws_manager and scan_id:
        await ws_manager.broadcast("scan_progress", {
            "scan_id": scan_id,
            "scan_type": "os",
            "status": "started",
            "total": total,
            "completed": 0,
            "progress": 0
        })

    for index, host in enumerate(hosts):
        os_data = await detect_os(host)

        if os_data:
            result = {"host": host, "os": os_data}
            results.append(result)
            
            if ws_manager and scan_id:
                completed = index + 1
                progress = round((completed / total) * 100, 2)
                await ws_manager.broadcast("scan_progress", {
                    "scan_id": scan_id,
                    "scan_type": "os",
                    "status": "scanning",
                    "total": total,
                    "completed": completed,
                    "progress": progress,
                    "current_host": host,
                    "result": result
                })
    
    if ws_manager and scan_id:
        await ws_manager.broadcast("scan_progress", {
            "scan_id": scan_id,
            "scan_type": "os",
            "status": "completed",
            "total": total,
            "completed": total,
            "progress": 100,
            "results": results
        })

    return results



# ================== VULNERABILITY SCAN ==================
def nmap_vuln_sync(host: str):
    scanner = nmap.PortScanner()
    scanner.scan(hosts=host, arguments="--script vuln")

    vulns = []

    if host in scanner.all_hosts():
        for proto in scanner[host].all_protocols():
            for port, data in scanner[host][proto].items():
                scripts = data.get("script", {})
                for script, output in scripts.items():
                    vulns.append({
                        "port": port,
                        "script": script,
                        "output": output
                    })

    return vulns


async def scan_vulnerabilities(host: str):
    return await asyncio.to_thread(nmap_vuln_sync, host)

async def scan_vulnerabilities_segment(hosts: list[str]):
    results = []

    for host in hosts:
        vulns = await scan_vulnerabilities(host)

        if vulns:
            results.append({
                "host": host,
                "vulnerabilities": vulns
            })

    return results



# ================== ICMP PING ==================
def icmp_sync(host: str, timeout: int = 1):
    start = time.perf_counter()
    result = subprocess.run(
        ["ping", "-c", "1", "-W", str(timeout), host],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    latency = (time.perf_counter() - start) * 1000
    return result.returncode == 0, latency if result.returncode == 0 else None


async def ping_icmp(host: str):
    return await asyncio.to_thread(icmp_sync, host)


# ================== TCP PING ==================
async def ping_tcp(host: str, port: int = 80, timeout: int = 2):
    start = time.perf_counter()
    try:
        await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout
        )
        latency = (time.perf_counter() - start) * 1000
        return True, latency
    except:
        return False, None


# ================== AUTO PING ==================
async def ping_auto(host: str):
    hostname = await get_hostname_async(host)

    try:
        ok, latency = await ping_icmp(host)
        if ok:
            return {
                "host": host,
                "hostname": hostname,
                "status": "up",
                "latency_ms": round(latency, 2),
                "method": "icmp"
            }
    except:
        pass

    ok, latency = await ping_tcp(host)
    return {
        "host": host,
        "hostname": hostname,
        "status": "up" if ok else "down",
        "latency_ms": round(latency, 2) if latency else None,
        "method": "tcp"
    }


async def ping_multiple(hosts: list[str], emit_progress: bool = True, scan_id: str = None):
    """
    Escanea múltiples hosts con soporte para actualizaciones en tiempo real vía WebSocket
    
    Args:
        hosts: Lista de IPs a escanear
        emit_progress: Si debe emitir eventos de progreso por WebSocket
        scan_id: Identificador único del escaneo para tracking
    """
    results = []
    total = len(hosts)
    ws_manager = get_ws_manager() if emit_progress else None
    
    # Emitir inicio del escaneo
    if ws_manager and scan_id:
        await ws_manager.broadcast("scan_progress", {
            "scan_id": scan_id,
            "status": "started",
            "total": total,
            "completed": 0,
            "progress": 0
        })
    
    for index, host in enumerate(hosts):
        result = await ping_auto(host)
        results.append(result)
        
        # Emitir progreso y resultado individual
        if ws_manager and scan_id:
            completed = index + 1
            progress = round((completed / total) * 100, 2)
            
            await ws_manager.broadcast("scan_progress", {
                "scan_id": scan_id,
                "status": "scanning",
                "total": total,
                "completed": completed,
                "progress": progress,
                "current_host": host,
                "result": result
            })
    
    # Emitir finalización
    if ws_manager and scan_id:
        await ws_manager.broadcast("scan_progress", {
            "scan_id": scan_id,
            "status": "completed",
            "total": total,
            "completed": total,
            "progress": 100,
            "results": results
        })
    
    return results


# ================== NETWORK EXPANSION ==================


def expand_hosts(start_ip: str, end_ip: str) -> list[str]:
    start = ipaddress.IPv4Address(start_ip)
    end = ipaddress.IPv4Address(end_ip)
    return [str(ip) for ip in range(int(start), int(end) + 1)]



# ================== HOST DISCOVERY ==================
def nmap_scan(network: str):
    scanner = nmap.PortScanner()
    scanner.scan(hosts=network, arguments="-sn")
    return scanner.all_hosts()


# ================== MAC & VENDOR (LAN ONLY) ==================
def nmap_mac_sync(network: str):
    scanner = nmap.PortScanner()
    scanner.scan(hosts=network, arguments="-sn")

    devices = []

    for host in scanner.all_hosts():
        mac = None
        vendor = None

        try:
            hostname = socket.gethostbyaddr(host)[0]
        except:
            hostname = None

        addresses = scanner[host].get("addresses", {})
        if "mac" in addresses:
            mac = addresses["mac"]
            vendor = scanner[host].get("vendor", {}).get(mac)

        devices.append({
            "ip": host,
            "hostname": hostname,
            "mac": mac,
            "vendor": vendor
        })

    return devices



async def scan_mac(network: str, emit_progress: bool = True, scan_id: str = None):
    ws_manager = get_ws_manager() if emit_progress else None
    
    if ws_manager and scan_id:
        await ws_manager.broadcast("scan_progress", {
            "scan_id": scan_id,
            "scan_type": "mac",
            "status": "started",
            "network": network,
            "progress": 0
        })
    
    result = await asyncio.to_thread(nmap_mac_sync, network)
    
    if ws_manager and scan_id:
        await ws_manager.broadcast("scan_progress", {
            "scan_id": scan_id,
            "scan_type": "mac",
            "status": "completed",
            "network": network,
            "progress": 100,
            "results": result
        })
    
    return result

def get_mac_single_host(host: str):
    scanner = nmap.PortScanner()
    scanner.scan(hosts=host, arguments="-sn")

    if host not in scanner.all_hosts():
        return None, None

    addresses = scanner[host].get("addresses", {})
    mac = addresses.get("mac")
    vendor = scanner[host].get("vendor", {}).get(mac) if mac else None

    return mac, vendor



async def full_host_scan(host: str, include_vulns: bool = False, emit_progress: bool = True, scan_id: str = None):

    from datetime import datetime
    ws_manager = get_ws_manager() if emit_progress else None
    
    if ws_manager and scan_id:
        await ws_manager.broadcast("scan_progress", {
            "scan_id": scan_id,
            "scan_type": "full",
            "status": "started",
            "host": host,
            "progress": 0,
            "stage": "ping"
        })
    
    # Ping y hostname
    ping_result = await ping_auto(host)
    
    if ws_manager and scan_id:
        await ws_manager.broadcast("scan_progress", {
            "scan_id": scan_id,
            "scan_type": "full",
            "status": "scanning",
            "host": host,
            "progress": 20,
            "stage": "mac"
        })
    
    if ping_result["status"] != "up":
        if ws_manager and scan_id:
            await ws_manager.broadcast("scan_progress", {
                "scan_id": scan_id,
                "scan_type": "full",
                "status": "completed",
                "host": host,
                "progress": 100,
                "result": {"status": "down"}
            })
        return {
            "host": host,
            "hostname": ping_result.get("hostname"),
            "mac": None,
            "vendor": None,
            "status": "down",
            "latency_ms": None,
            "ports": [],
            "services": [],
            "os": None,
            "vulnerabilities": [],
            "last_seen": datetime.utcnow().isoformat() + "Z"
        }
    
    # Intentar obtener MAC (solo funciona en LAN local)
    mac = None
    vendor = None
    try:
        scanner = nmap.PortScanner()
        result = await asyncio.to_thread(
            scanner.scan,
            hosts=host,
            arguments="-sn"
        )
        if host in scanner.all_hosts():
            addresses = scanner[host].get("addresses", {})
            if "mac" in addresses:
                mac = addresses["mac"]
                vendor = scanner[host].get("vendor", {}).get(mac)
    except:
        pass
    
    if ws_manager and scan_id:
        await ws_manager.broadcast("scan_progress", {
            "scan_id": scan_id,
            "scan_type": "full",
            "status": "scanning",
            "host": host,
            "progress": 40,
            "stage": "ports"
        })
    
    # Ejecutar escaneos en paralelo
    ports_task = scan_ports(host, "1-1024")
    services_task = scan_services(host, "1-1024")
    os_task = detect_os(host)
    
    if ws_manager and scan_id:
        await ws_manager.broadcast("scan_progress", {
            "scan_id": scan_id,
            "scan_type": "full",
            "status": "scanning",
            "host": host,
            "progress": 60,
            "stage": "services & os"
        })
    
    ports, services, os_info = await asyncio.gather(
        ports_task, services_task, os_task
    )
    
    # Vulnerabilidades (opcional, muy lento)
    vulnerabilities = []
    if include_vulns:
        if ws_manager and scan_id:
            await ws_manager.broadcast("scan_progress", {
                "scan_id": scan_id,
                "scan_type": "full",
                "status": "scanning",
                "host": host,
                "progress": 80,
                "stage": "vulnerabilities"
            })
        vulnerabilities = await scan_vulnerabilities(host)
    
    result = {
        "host": host,
        "hostname": ping_result.get("hostname"),
        "mac": mac,
        "vendor": vendor,
        "status": "up",
        "latency_ms": ping_result.get("latency_ms"),
        "ports": ports,
        "services": services,
        "os": os_info,
        "vulnerabilities": vulnerabilities,
        "last_seen": datetime.utcnow().isoformat() + "Z"
    }
    
    if ws_manager and scan_id:
        await ws_manager.broadcast("scan_progress", {
            "scan_id": scan_id,
            "scan_type": "full",
            "status": "completed",
            "host": host,
            "progress": 100,
            "result": result
        })
    
    return result