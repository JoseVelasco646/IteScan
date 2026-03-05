
import asyncio
import nmap

from app.scanners.common import GLOBAL_NMAP_SEMAPHORE, get_ws_manager


def nmap_os_sync(host: str):
    scanner = nmap.PortScanner()
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
    async with GLOBAL_NMAP_SEMAPHORE:
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(nmap_os_sync, host),
                timeout=45.0
            )
        except asyncio.TimeoutError:
            return None


async def detect_os_segment(hosts: list[str], emit_progress: bool = True, scan_id: str = None, host_timeout: int = 60, concurrency: int = 50):
    total = len(hosts)
    ws_manager = get_ws_manager() if emit_progress else None

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
            "progress": 0,
            "host_timeout": host_timeout
        }))

    semaphore = asyncio.Semaphore(max(1, min(concurrency, 200)))

    async def detect_os_single(host: str, index: int):
        nonlocal completed_count, last_broadcast

        if ws_manager and scan_id and ws_manager.is_scan_cancelled(scan_id):
            return None

        async with semaphore:
            if ws_manager and scan_id and ws_manager.is_scan_cancelled(scan_id):
                return None

            try:
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

            except Exception:
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
                            "current_host": host,
                            "host_timeout": host_timeout
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
            "progress": 100,
            "host_timeout": host_timeout
        })

    return results
