
import asyncio

scan_tasks: dict[str, asyncio.Event] = {}

def create_scan(scan_id: str):
    scan_tasks[scan_id] = asyncio.Event()

def cancel_scan(scan_id: str):
    if scan_id in scan_tasks:
        scan_tasks[scan_id].set()

def is_cancelled(scan_id: str) -> bool:
    return scan_tasks.get(scan_id, asyncio.Event()).is_set()

def remove_scan(scan_id: str):
    scan_tasks.pop(scan_id, None)
