
import asyncio
import time
import socket
import nmap

from app.scanners.common import get_ws_manager


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


async def scan_mac(network: str, emit_progress: bool = True, scan_id: str = None, host_timeout: int = 8, concurrency: int = 30):
    ws_manager = get_ws_manager() if emit_progress else None

    import ipaddress
    network_obj = ipaddress.ip_network(network, strict=False)
    hosts = [str(ip) for ip in network_obj.hosts()]
    total = len(hosts)

    completed = 0
    semaphore = asyncio.Semaphore(max(1, min(concurrency, 200)))
    lock = asyncio.Lock()

    update_interval = max(5, total // 20)
    last_broadcast = 0
    last_broadcast_time = time.time()
    min_broadcast_interval = 0.5

    if ws_manager and scan_id:
        asyncio.create_task(ws_manager.broadcast("scan_progress", {
            "scan_id": scan_id,
            "scan_type": "mac",
            "status": "started",
            "network": network,
            "total": total,
            "completed": 0,
            "progress": 0,
            "host_timeout": host_timeout
        }))

    async def scan_single_mac(host: str):
        nonlocal completed, last_broadcast, last_broadcast_time

        async with semaphore:
            try:
                proc = await asyncio.create_subprocess_exec(
                    'nmap', '-sn', '-PR', host,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=float(host_timeout))
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
            except Exception:
                result = None

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
                        "scan_type": "mac",
                        "status": "scanning",
                        "network": network,
                        "current_host": host,
                        "total": total,
                        "completed": current_completed,
                        "progress": progress,
                        "host_timeout": host_timeout
                    }))

            return result

    results = await asyncio.gather(*[scan_single_mac(host) for host in hosts])
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
            "host_timeout": host_timeout,
            "results": devices
        }))

    return devices


def get_mac_single_host(host: str):
    scanner = nmap.PortScanner()
    scanner.scan(hosts=host, arguments="-sn")

    if host not in scanner.all_hosts():
        return None, None

    addresses = scanner[host].get("addresses", {})
    mac = addresses.get("mac")
    vendor = scanner[host].get("vendor", {}).get(mac) if mac else None

    return mac, vendor
