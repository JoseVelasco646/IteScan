import asyncio
import subprocess
import time
import ipaddress
import nmap
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import socket
import platform

IS_WINDOWS = platform.system().lower() == 'windows'

# Semáforo global para limitar operaciones nmap simultáneas
# Esto evita saturar el thread pool cuando hay muchos Full Scans
GLOBAL_NMAP_SEMAPHORE = asyncio.Semaphore(30)

def get_ws_manager():
    try:
        from app.websocket_manager import ws_manager
        return ws_manager
    except:
        return None

def get_hostname(ip: str) -> str:
    """Obtiene el hostname de una IP usando múltiples métodos"""
    hostname = None
    
    try:
        hostname = socket.gethostbyaddr(ip)[0]
        if hostname and hostname != ip:
            return hostname
    except:
        pass
    
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
    
    try:
        import subprocess
        if IS_WINDOWS:
            result = subprocess.run(
                ['nbtstat', '-A', ip],
                capture_output=True,
                text=True,
                timeout=2
            )
            for line in result.stdout.split('\n'):
                if '<00>' in line and 'UNIQUE' in line:
                    parts = line.split()
                    if parts and parts[0] != ip:
                        hostname = parts[0].strip()
                        if hostname and hostname != ip:
                            return hostname
        else:
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


def nmap_ports_sync(host: str, ports: str = "1-1024"):
    scanner = nmap.PortScanner()
    # Agregar timeout por host para evitar bloqueos
    scanner.scan(hosts=host, ports=ports, arguments="-sS --host-timeout 120s")

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
    # Agregar timeout general en asyncio por si nmap se cuelga
    # Usar semáforo global para evitar saturar el thread pool
    async with GLOBAL_NMAP_SEMAPHORE:
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(nmap_ports_sync, host, ports),
                timeout=45.0  # Timeout de 45 segundos total
            )
        except asyncio.TimeoutError:
            print(f"⚠️ Timeout scanning ports on {host}")
            return []  # Retornar lista vacía si hay timeout

async def scan_ports_segment(hosts: list[str], ports: str = "1-1024", emit_progress: bool = True, scan_id: str = None):
    results = []
    total = len(hosts)
    ws_manager = get_ws_manager() if emit_progress else None
    completed = 0
    
    # Usar semáforo para controlar concurrencia (50 simultáneos como ping/mac)
    semaphore = asyncio.Semaphore(50)
    lock = asyncio.Lock()
    
    # Optimización: actualizar cada 5% o mínimo cada 5 hosts
    update_interval = max(5, total // 20)
    last_broadcast = 0
    last_broadcast_time = time.time()
    min_broadcast_interval = 0.3  # Mínimo 300ms entre broadcasts
    
    if ws_manager and scan_id:
        await ws_manager.broadcast("scan_progress", {
            "scan_id": scan_id,
            "scan_type": "ports",
            "status": "started",
            "total": total,
            "completed": 0,
            "progress": 0
        })
    
    async def scan_single_port(host: str):
        nonlocal completed, last_broadcast, last_broadcast_time
        
        # Verificar si el scan fue cancelado antes de empezar
        if ws_manager and scan_id and ws_manager.is_scan_cancelled(scan_id):
            return None
        
        async with semaphore:
            # Verificar de nuevo dentro del semáforo
            if ws_manager and scan_id and ws_manager.is_scan_cancelled(scan_id):
                return None
            
            open_ports = await scan_ports(host, ports)
            
            result = None
            if open_ports:
                result = {"host": host, "ports": open_ports}
            
            async with lock:
                completed += 1
                current_completed = completed
                current_time = time.time()
                
                # Solo enviar actualización si:
                # 1. Han pasado suficientes hosts desde la última actualización
                # 2. Ha pasado suficiente tiempo desde la última actualización
                # 3. Es el último host
                should_broadcast = (
                    (current_completed - last_broadcast >= update_interval) or
                    (current_time - last_broadcast_time >= min_broadcast_interval and current_completed > last_broadcast) or
                    (current_completed == total)
                )
                
                if should_broadcast and ws_manager and scan_id:
                    last_broadcast = current_completed
                    last_broadcast_time = current_time
                    progress = round((current_completed / total) * 100, 2)
                    
                    broadcast_data = {
                        "scan_id": scan_id,
                        "scan_type": "ports",
                        "status": "scanning",
                        "total": total,
                        "completed": current_completed,
                        "progress": progress,
                        "current_host": host
                    }
                    
                    if result:
                        broadcast_data["result"] = result
                    
                    asyncio.create_task(ws_manager.broadcast("scan_progress", broadcast_data))
            
            return result
    
    # Ejecutar todos los escaneos simultáneamente con control de concurrencia
    scan_results = await asyncio.gather(*[scan_single_port(host) for host in hosts])
    
    # Filtrar resultados None
    results = [r for r in scan_results if r is not None]
    
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


def nmap_services_sync(host: str, ports: str = "1-1024"):
    scanner = nmap.PortScanner()
    # Agregar timeout por host para evitar bloqueos
    scanner.scan(hosts=host, ports=ports, arguments="-sS -sV --host-timeout 45s")

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
    # Agregar timeout general en asyncio
    # Usar semáforo global para evitar saturar el thread pool
    async with GLOBAL_NMAP_SEMAPHORE:
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(nmap_services_sync, host, ports),
                timeout=60.0  # Timeout de 60 segundos (services tarda más)
            )
        except asyncio.TimeoutError:
            print(f"⚠️ Timeout scanning services on {host}")
            return []

async def scan_services_segment(hosts: list[str], ports: str = "1-1024", emit_progress: bool = True, scan_id: str = None):
    results = []
    expanded_hosts = expand_targets(hosts)
    total = len(expanded_hosts)
    ws_manager = get_ws_manager() if emit_progress else None
    completed = 0
    
    # Usar semáforo para controlar concurrencia
    semaphore = asyncio.Semaphore(50)
    lock = asyncio.Lock()
    
    # Optimización: actualizar cada 5% o mínimo cada 5 hosts
    update_interval = max(5, total // 20)
    last_broadcast = 0
    last_broadcast_time = time.time()
    min_broadcast_interval = 0.3
    
    if ws_manager and scan_id:
        await ws_manager.broadcast("scan_progress", {
            "scan_id": scan_id,
            "scan_type": "services",
            "status": "started",
            "total": total,
            "completed": 0,
            "progress": 0
        })
    
    async def scan_single_service(host: str):
        nonlocal completed, last_broadcast, last_broadcast_time
        
        # Verificar cancelación
        if ws_manager and scan_id and ws_manager.is_scan_cancelled(scan_id):
            return None
        
        async with semaphore:
            if ws_manager and scan_id and ws_manager.is_scan_cancelled(scan_id):
                return None
            
            services = await scan_services(host, ports)
            result = {"host": host, "services": services}
            
            async with lock:
                completed += 1
                current_completed = completed
                current_time = time.time()
                
                should_broadcast = (
                    (current_completed - last_broadcast >= update_interval) or
                    (current_time - last_broadcast_time >= min_broadcast_interval and current_completed > last_broadcast) or
                    (current_completed == total)
                )
                
                if should_broadcast and ws_manager and scan_id:
                    last_broadcast = current_completed
                    last_broadcast_time = current_time
                    progress = round((current_completed / total) * 100, 2)
                    
                    asyncio.create_task(ws_manager.broadcast("scan_progress", {
                        "scan_id": scan_id,
                        "scan_type": "services",
                        "status": "scanning",
                        "total": total,
                        "completed": current_completed,
                        "progress": progress,
                        "current_host": host,
                        "result": result
                    }))
            
            return result
    
    # Ejecutar todos los escaneos simultáneamente
    scan_results = await asyncio.gather(*[scan_single_service(host) for host in expanded_hosts])
    
    # Filtrar resultados None
    results = [r for r in scan_results if r is not None]
    
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


def nmap_os_sync(host: str):
    scanner = nmap.PortScanner()
    # Agregar timeout para OS detection
    scanner.scan(hosts=host, arguments="-O --host-timeout 30s")

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
    # Agregar timeout general
    # Usar semáforo global para evitar saturar el thread pool
    async with GLOBAL_NMAP_SEMAPHORE:
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(nmap_os_sync, host),
                timeout=45.0  # Timeout de 45 segundos
            )
        except asyncio.TimeoutError:
            print(f"⚠️ Timeout detecting OS on {host}")
            return None

async def detect_os_segment(hosts: list[str], emit_progress: bool = True, scan_id: str = None):
    total = len(hosts)
    ws_manager = get_ws_manager() if emit_progress else None
    
    # Optimización: actualizar cada 5% o mínimo cada 3 hosts
    update_interval = max(3, total // 20)
    completed_count = 0
    last_broadcast = 0
    lock = asyncio.Lock()
    
    if ws_manager and scan_id:
        asyncio.create_task(ws_manager.broadcast("scan_progress", {
            "scan_id": scan_id,
            "scan_type": "os-detection",
            "status": "started",
            "total": total,
            "completed": 0,
            "progress": 0
        }))

    semaphore = asyncio.Semaphore(50)
    
    async def detect_os_single(host: str, index: int):
        nonlocal completed_count, last_broadcast
        
        # Verificar cancelación
        if ws_manager and scan_id and ws_manager.is_scan_cancelled(scan_id):
            return None
        
        async with semaphore:
            if ws_manager and scan_id and ws_manager.is_scan_cancelled(scan_id):
                return None
            
            try:
                # Usar detect_os que ya tiene timeout
                result = await detect_os(host)
                
                if result:
                    return {
                        "host": host,
                        "os": result
                    }
                else:
                    return {
                        "host": host,
                        "os": None
                    }
                    
            except Exception as e:
                print(f"❌ Error detecting OS on {host}: {e}")
                return {
                    "host": host,
                    "os": None
                }
            finally:
                async with lock:
                    completed_count += 1
                    current_completed = completed_count
                    should_broadcast = (
                        (current_completed - last_broadcast >= update_interval) or
                        (current_completed == total)
                    )
                    
                    if should_broadcast and ws_manager and scan_id:
                        last_broadcast = current_completed
                        progress = round((current_completed / total) * 100, 2)
                        asyncio.create_task(ws_manager.broadcast("scan_progress", {
                            "scan_id": scan_id,
                            "scan_type": "os-detection",
                            "status": "scanning",
                            "total": total,
                            "completed": current_completed,
                            "progress": progress,
                            "current_host": host
                        }))
    
    results = await asyncio.gather(*[detect_os_single(host, idx) for idx, host in enumerate(hosts)])
    
    await asyncio.sleep(0.1)
    
    if ws_manager and scan_id:
        await ws_manager.broadcast("scan_progress", {
            "scan_id": scan_id,
            "scan_type": "os-detection",
            "status": "completed",
            "total": total,
            "completed": total,
            "progress": 100
        })


    return results




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


def icmp_sync(host: str, timeout: float = 0.5):
    start = time.perf_counter()
    try:
        if IS_WINDOWS:
            cmd = ["ping", "-n", "1", "-w", str(int(timeout * 1000)), host]
        else:
            cmd = ["ping", "-c", "1", "-W", str(int(timeout)), host]
            
        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout + 1.0  # Timeout de seguridad para subprocess
        )
        latency = (time.perf_counter() - start) * 1000
        return result.returncode == 0, latency if result.returncode == 0 else None
    except subprocess.TimeoutExpired:
        return False, None
    except Exception as e:
        return False, None


async def ping_icmp(host: str):
    return await asyncio.to_thread(icmp_sync, host)


async def ping_tcp(host: str, port: int = 80, timeout: float = 1.0):
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


async def ping_auto(host: str, resolve_hostname: bool = False):
    hostname = None

    if resolve_hostname:
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


async def ping_multiple(hosts: list[str], emit_progress: bool = True, scan_id: str = None, resolve_hostname: bool = False, concurrency: int = 50):
    """
    Escanea múltiples hosts con actualizaciones de progreso optimizadas.
    Las actualizaciones WebSocket se envían cada 5% del progreso para evitar saturación.
    """
    total = len(hosts)
    completed = 0
    ws_manager = get_ws_manager() if emit_progress else None

    semaphore = asyncio.Semaphore(concurrency)
    lock = asyncio.Lock()
    
    # Optimización: actualizar cada 5% o mínimo cada 5 hosts
    update_interval = max(5, total // 20)
    last_broadcast = 0
    last_broadcast_time = time.time()
    min_broadcast_interval = 0.3  # Mínimo 300ms entre broadcasts

    if ws_manager and scan_id:
        asyncio.create_task(ws_manager.broadcast("scan_progress", {
            "scan_id": scan_id,
            "scan_type": "ping",
            "status": "started",
            "total": total,
            "completed": 0,
            "progress": 0
        }))
    
    async def ping_with_semaphore(host: str):
        nonlocal completed, last_broadcast, last_broadcast_time
        
        if ws_manager and scan_id and ws_manager.is_scan_cancelled(scan_id):
            return None
            
        async with semaphore:
            if ws_manager and scan_id and ws_manager.is_scan_cancelled(scan_id):
                return None
                
            try:
                result = await ping_auto(host, resolve_hostname=resolve_hostname)
            except Exception as e:
                result = {
                    "host": host,
                    "hostname": None,
                    "status": "down",
                    "latency_ms": None,
                    "method": "error"
                }

            async with lock:
                completed += 1
                current_completed = completed
                current_time = time.time()
                
                # Solo enviar actualización si:
                # 1. Han pasado suficientes hosts desde la última actualización
                # 2. Ha pasado suficiente tiempo desde la última actualización
                # 3. Es el último host
                should_broadcast = (
                    (current_completed - last_broadcast >= update_interval) or
                    (current_time - last_broadcast_time >= min_broadcast_interval and current_completed > last_broadcast) or
                    (current_completed == total)
                )
                
                if should_broadcast and ws_manager and scan_id:
                    last_broadcast = current_completed
                    last_broadcast_time = current_time
                    progress = round((current_completed / total) * 100, 2)
                    asyncio.create_task(ws_manager.broadcast("scan_progress", {
                        "scan_id": scan_id,
                        "scan_type": "ping",
                        "status": "scanning",
                        "total": total,
                        "completed": current_completed,
                        "progress": progress,
                        "current_host": host,
                        "result": result
                    }))

            return result

    results = await asyncio.gather(*[ping_with_semaphore(host) for host in hosts], return_exceptions=True)
    results = [r for r in results if r is not None and not isinstance(r, Exception)]

    if ws_manager and scan_id:
        if ws_manager.is_scan_cancelled(scan_id):
            asyncio.create_task(ws_manager.broadcast("scan_progress", {
                "scan_id": scan_id,
                "scan_type": "ping",
                "status": "cancelled",
                "total": total,
                "completed": completed,
                "progress": round((completed / total) * 100, 2)
            }))
            ws_manager.clear_scan(scan_id)
        else:
            asyncio.create_task(ws_manager.broadcast("scan_progress", {
                "scan_id": scan_id,
                "scan_type": "ping",
                "status": "completed",
                "total": total,
                "completed": total,
                "progress": 100,
                "results": results
            }))
    
    return results


def expand_hosts(start_ip: str, end_ip: str) -> list[str]:
    start = ipaddress.IPv4Address(start_ip)
    end = ipaddress.IPv4Address(end_ip)
    return [str(ip) for ip in range(int(start), int(end) + 1)]


def nmap_scan(network: str):
    scanner = nmap.PortScanner()
    scanner.scan(hosts=network, arguments="-sn")
    return scanner.all_hosts()


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
    
    import ipaddress
    network_obj = ipaddress.ip_network(network, strict=False)
    hosts = [str(ip) for ip in network_obj.hosts()]
    total = len(hosts)
    
    # Optimización: actualizar cada 5% o mínimo cada 5 hosts
    update_interval = max(5, total // 20)
    completed_count = 0
    last_broadcast = 0
    lock = asyncio.Lock()
    
    if ws_manager and scan_id:
        asyncio.create_task(ws_manager.broadcast("scan_progress", {
            "scan_id": scan_id,
            "scan_type": "mac",
            "status": "started",
            "network": network,
            "total": total,
            "completed": 0,
            "progress": 0
        }))
    
    devices = []
    semaphore = asyncio.Semaphore(50)
    
    async def scan_single_mac_fast(host: str, index: int):
        nonlocal completed_count, last_broadcast
        async with semaphore:
            try:
                proc = await asyncio.create_subprocess_exec(
                    'nmap', '-sn', '--host-timeout', '3s', host,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                try:
                    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=5.0)
                    output = stdout.decode()
                    
                    mac = None
                    vendor = None
                    hostname = None
                    
                    for line in output.split('\n'):
                        if 'MAC Address:' in line:
                            parts = line.split('MAC Address:')[1].strip().split('(')
                            mac = parts[0].strip()
                            if len(parts) > 1:
                                vendor = parts[1].rstrip(')')
                        elif 'Nmap scan report for' in line:
                            if '(' in line and ')' in line:
                                hostname = line.split('for')[1].split('(')[0].strip()
                    
                    result = None
                    if mac:
                        result = {
                            "ip": host,
                            "hostname": hostname,
                            "mac": mac,
                            "vendor": vendor
                        }
                        
                except asyncio.TimeoutError:
                    result = None
                    
            except Exception as e:
                result = None
            
            async with lock:
                completed_count += 1
                current_completed = completed_count
                should_broadcast = (
                    (current_completed - last_broadcast >= update_interval) or
                    (current_completed == total)
                )
                
                if should_broadcast and ws_manager and scan_id:
                    last_broadcast = current_completed
                    progress = round((current_completed / total) * 100, 2)
                    asyncio.create_task(ws_manager.broadcast("scan_progress", {
                        "scan_id": scan_id,
                        "scan_type": "mac",
                        "status": "scanning",
                        "network": network,
                        "current_host": host,
                        "total": total,
                        "completed": current_completed,
                        "progress": progress
                    }))
            
            return result
    
    results = await asyncio.gather(*[scan_single_mac_fast(host, idx) for idx, host in enumerate(hosts)])
    
    devices = [r for r in results if r is not None]
    
    if ws_manager and scan_id:
        asyncio.create_task(ws_manager.broadcast("scan_progress", {
            "scan_id": scan_id,
            "scan_type": "mac",
            "status": "completed",
            "network": network,
            "total": total,
            "completed": total,
            "progress": 100,
            "results": devices
        }))
    
    return devices


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
    
    ping_result = await ping_auto(host, resolve_hostname=True)
    
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