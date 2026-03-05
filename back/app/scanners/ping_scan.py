
import asyncio
import subprocess
import time

from app.scanners.common import (
    IS_WINDOWS, get_ws_manager, get_hostname_async
)


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
            timeout=timeout + 1.0
        )
        latency = (time.perf_counter() - start) * 1000
        return result.returncode == 0, latency if result.returncode == 0 else None
    except subprocess.TimeoutExpired:
        return False, None
    except Exception:
        return False, None


async def ping_icmp(host: str, timeout: float = 2.0):
    return await asyncio.to_thread(icmp_sync, host, timeout)


async def ping_tcp(host: str, port: int = 80, timeout: float = 1.0):
    start = time.perf_counter()
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout
        )
        latency = (time.perf_counter() - start) * 1000
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        return True, latency
    except:
        return False, None


async def ping_auto(host: str, resolve_hostname: bool = False, timeout: float = 2.0):
    hostname = None

    if resolve_hostname:
        hostname = await get_hostname_async(host)

    try:
        ok, latency = await ping_icmp(host, timeout=timeout)
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

    ok, latency = await ping_tcp(host, timeout=timeout)
    return {
        "host": host,
        "hostname": hostname,
        "status": "up" if ok else "down",
        "latency_ms": round(latency, 2) if latency else None,
        "method": "tcp"
    }


async def ping_multiple(hosts: list[str], emit_progress: bool = True, scan_id: str = None, resolve_hostname: bool = False, concurrency: int = 50, host_timeout: int = 2):
    total = len(hosts)
    completed = 0
    ws_manager = get_ws_manager() if emit_progress else None

    semaphore = asyncio.Semaphore(concurrency)
    lock = asyncio.Lock()

    update_interval = max(5, total // 20)
    last_broadcast = 0
    last_broadcast_time = time.time()
    min_broadcast_interval = 0.3

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
                result = await ping_auto(host, resolve_hostname=resolve_hostname, timeout=host_timeout)
            except Exception:
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
