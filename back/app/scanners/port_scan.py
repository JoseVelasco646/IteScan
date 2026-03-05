import asyncio
import time
import nmap

from app.scanners.common import GLOBAL_NMAP_SEMAPHORE, get_ws_manager


def nmap_ports_sync(host: str, ports: str = "1-1024"):
    scanner = nmap.PortScanner()
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


async def scan_ports(host: str, ports: str = "1-1024", host_timeout: int = 45):
    async with GLOBAL_NMAP_SEMAPHORE:
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(nmap_ports_sync, host, ports),
                timeout=float(host_timeout)
            )
        except asyncio.TimeoutError:
            return []


async def scan_ports_segment(hosts: list[str], ports: str = "1-1024", emit_progress: bool = True, scan_id: str = None, host_timeout: int = 45, concurrency: int = 50):
    results = []
    total = len(hosts)
    ws_manager = get_ws_manager() if emit_progress else None
    completed = 0

    semaphore = asyncio.Semaphore(max(1, min(concurrency, 200)))
    lock = asyncio.Lock()

    update_interval = max(5, total // 20)
    last_broadcast = 0
    last_broadcast_time = time.time()
    min_broadcast_interval = 0.3

    if ws_manager and scan_id:
        await ws_manager.broadcast("scan_progress", {
            "scan_id": scan_id,
            "scan_type": "ports",
            "status": "started",
            "total": total,
            "completed": 0,
            "progress": 0,
            "host_timeout": host_timeout
        })

    async def scan_single_port(host: str):
        nonlocal completed, last_broadcast, last_broadcast_time

        if ws_manager and scan_id and ws_manager.is_scan_cancelled(scan_id):
            return None

        async with semaphore:
            if ws_manager and scan_id and ws_manager.is_scan_cancelled(scan_id):
                return None

            open_ports = await scan_ports(host, ports, host_timeout=host_timeout)

            result = None
            if open_ports:
                result = {"host": host, "ports": open_ports}

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

                    broadcast_data = {
                        "scan_id": scan_id,
                        "scan_type": "ports",
                        "status": "scanning",
                        "total": total,
                        "completed": current_completed,
                        "progress": progress,
                        "current_host": host,
                        "host_timeout": host_timeout
                    }

                    if result:
                        broadcast_data["result"] = result

                    asyncio.create_task(ws_manager.broadcast("scan_progress", broadcast_data))

            return result

    scan_results = await asyncio.gather(*[scan_single_port(host) for host in hosts])

    results = [r for r in scan_results if r is not None]

    if ws_manager and scan_id:
        await ws_manager.broadcast("scan_progress", {
            "scan_id": scan_id,
            "scan_type": "ports",
            "status": "completed",
            "total": total,
            "completed": total,
            "progress": 100,
            "results": results,
            "host_timeout": host_timeout
        })

    return results
