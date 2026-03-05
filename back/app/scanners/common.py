
import asyncio
import subprocess
import time
import ipaddress
import socket
import platform
import nmap

IS_WINDOWS = platform.system().lower() == 'windows'

GLOBAL_NMAP_SEMAPHORE = asyncio.Semaphore(30)


def get_ws_manager():
    try:
        from app.websocket_manager import ws_manager
        return ws_manager
    except:
        return None


def get_hostname(ip: str) -> str:
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


def expand_hosts(start_ip: str, end_ip: str) -> list[str]:
    start = ipaddress.IPv4Address(start_ip)
    end = ipaddress.IPv4Address(end_ip)
    return [str(ip) for ip in range(int(start), int(end) + 1)]
