import asyncio
from datetime import datetime
import nmap

from app.scanners.common import get_ws_manager
from app.scanners.ping_scan import ping_auto
from app.scanners.port_scan import scan_ports
from app.scanners.service_scan import scan_services
from app.scanners.os_scan import detect_os
from app.scanners.vuln_scan import scan_vulnerabilities


async def full_host_scan(host: str, include_vulns: bool = False, emit_progress: bool = True, scan_id: str = None, host_timeout: int = 120):
    ws_manager = get_ws_manager() if emit_progress else None

    if ws_manager and scan_id:
        await ws_manager.broadcast("scan_progress", {
            "scan_id": scan_id,
            "scan_type": "full",
            "status": "started",
            "host": host,
            "progress": 0,
            "stage": "ping",
            "host_timeout": host_timeout,
            "total": 1,
            "completed": 0
        })

    ping_result = await ping_auto(host, resolve_hostname=True, timeout=host_timeout)

    if ws_manager and scan_id:
        await ws_manager.broadcast("scan_progress", {
            "scan_id": scan_id,
            "scan_type": "full",
            "status": "scanning",
            "host": host,
            "progress": 20,
            "stage": "mac",
            "host_timeout": host_timeout
        })

    if ping_result["status"] != "up":
        if ws_manager and scan_id:
            await ws_manager.broadcast("scan_progress", {
                "scan_id": scan_id,
                "scan_type": "full",
                "status": "completed",
                "host": host,
                "progress": 100,
                "result": {"status": "down"},
                "host_timeout": host_timeout
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
        await asyncio.to_thread(scanner.scan, hosts=host, arguments="-sn")
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
            "stage": "ports",
            "host_timeout": host_timeout
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
            "stage": "services & os",
            "host_timeout": host_timeout
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
                "stage": "vulnerabilities",
                "host_timeout": host_timeout
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
            "result": result,
            "host_timeout": host_timeout
        })
    
    return result
