
import asyncio
import nmap


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


async def scan_vulnerabilities_segment(hosts: list[str], concurrency: int = 5):
    results = []
    semaphore = asyncio.Semaphore(max(1, min(concurrency, 20)))

    async def scan_single(host: str):
        async with semaphore:
            vulns = await scan_vulnerabilities(host)
            if vulns:
                return {"host": host, "vulnerabilities": vulns}
            return None

    scan_results = await asyncio.gather(*[scan_single(h) for h in hosts])
    results = [r for r in scan_results if r is not None]
    return results
