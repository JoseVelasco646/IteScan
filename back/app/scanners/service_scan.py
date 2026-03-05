import asyncio
import time
import nmap

from app.scanners.common import GLOBAL_NMAP_SEMAPHORE, get_ws_manager, expand_targets


def nmap_services_sync(host: str, ports: str = "1-1024", timeout: int = 120):
    scanner = nmap.PortScanner()
    scanner.scan(hosts=host, ports=ports, arguments=f"-sS -sV --host-timeout {timeout}s")

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


async def scan_services(host: str, ports: str = "1-1024", timeout: int = 120):
    async with GLOBAL_NMAP_SEMAPHORE:
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(nmap_services_sync, host, ports, timeout),
                timeout=timeout + 10.0
            )
        except asyncio.TimeoutError:
            return []


async def scan_services_segment(hosts: list[str], ports: str = "1-1024", emit_progress: bool = True, scan_id: str = None, host_timeout: int = 120, concurrency: int = 50):
    results = []
    expanded_hosts = expand_targets(hosts)
    total = len(expanded_hosts)
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
            "scan_type": "services",
            "status": "started",
            "total": total,
            "completed": 0,
            "progress": 0,
            "host_timeout": host_timeout
        })

    async def scan_single_service(host: str):
        nonlocal completed, last_broadcast, last_broadcast_time

        if ws_manager and scan_id and ws_manager.is_scan_cancelled(scan_id):
            return None

        async with semaphore:
            if ws_manager and scan_id and ws_manager.is_scan_cancelled(scan_id):
                return None

            services = await scan_services(host, ports, timeout=host_timeout)
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
                        "result": result,
                        "host_timeout": host_timeout
                    }))

            return result

    scan_results = await asyncio.gather(*[scan_single_service(host) for host in expanded_hosts])

    results = [r for r in scan_results if r is not None]

    if ws_manager and scan_id:
        await ws_manager.broadcast("scan_progress", {
            "scan_id": scan_id,
            "scan_type": "services",
            "status": "completed",
            "total": total,
            "completed": total,
            "progress": 100,
            "results": results,
            "host_timeout": host_timeout
        })

    return results
