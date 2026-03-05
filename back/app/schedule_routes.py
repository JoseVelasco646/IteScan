from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import os
import logging

import asyncio
import time

from app.database import get_db
from app.models import ScanSchedule, ScanHistory, AuditLog
from app.auth import require_role
from app.schedule_schemas import (
    ScanScheduleCreate,
    ScanScheduleUpdate,
    ScanScheduleResponse,
    ScanSchedulePublic
)
from app import crud
from app.scanners import (
    ping_multiple,
    expand_network,
    scan_ports_segment,
    scan_services_segment,
    detect_os,
    scan_mac,
    full_host_scan
)
from app.ssh_operations import shutdown_ip_range, shutdown_host_ssh

router = APIRouter(prefix="/api/schedules", tags=["schedules"])

logger = logging.getLogger(__name__)

try:
   
    LOCAL_TZ = ZoneInfo('America/Tijuana')  
except Exception:
    LOCAL_TZ = None

scan_result_cache = {}
_CACHE_MAX_SIZE = 100
_CACHE_TTL_SECONDS = 3600  # 1 hora


def _cache_set(schedule_id: int, data: dict):
    import time as _t
    now = _t.time()
    expired = [k for k, v in scan_result_cache.items() if now - v.get("_ts", 0) > _CACHE_TTL_SECONDS]
    for k in expired:
        scan_result_cache.pop(k, None)
    while len(scan_result_cache) >= _CACHE_MAX_SIZE:
        oldest = min(scan_result_cache, key=lambda k: scan_result_cache[k].get("_ts", 0))
        scan_result_cache.pop(oldest, None)
    data["_ts"] = now
    scan_result_cache[schedule_id] = data


def _cache_get(schedule_id: int):
    import time as _t
    entry = scan_result_cache.get(schedule_id)
    if entry is None:
        return None
    if _t.time() - entry.get("_ts", 0) > _CACHE_TTL_SECONDS:
        scan_result_cache.pop(schedule_id, None)
        return None
    # Retornar sin el campo interno _ts
    return {k: v for k, v in entry.items() if k != "_ts"}

def get_ws_manager():
    from app.websocket_manager import ws_manager
    return ws_manager

def get_user_info_from_request(request: Request) -> dict:
    try:
        from app.auth import decode_token
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            payload = decode_token(auth_header.split(" ")[1])
            return {"user_id": payload.get("user_id"), "username": payload.get("username")}
    except Exception:
        pass
    return {"user_id": None, "username": None}

def schedule_audit_log(db: Session, request: Request, action: str, description: str, details: dict = None):
    try:
        user_info = get_user_info_from_request(request)
        client_ip = request.client.host
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        entry = AuditLog(
            user_id=user_info["user_id"],
            username=user_info["username"],
            action=action,
            category="scheduler",
            description=description,
            details=details,
            ip_address=client_ip
        )
        db.add(entry)
        db.commit()
    except Exception as e:
        logger.error(f"Error guardando audit log: {e}")
        try:
            db.rollback()
        except:
            pass

def schedule_to_dict(schedule: ScanSchedule) -> dict:
    schedule_dict = ScanSchedulePublic.from_orm(schedule).dict()
    return serialize_for_json(schedule_dict)

def serialize_for_json(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: serialize_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]
    else:
        return obj

def calculate_next_run(schedule: ScanSchedule) -> datetime:
    if LOCAL_TZ:
        now = datetime.now(LOCAL_TZ)
    else:
        now = datetime.now().astimezone()
    
    if schedule.frequency == 'hourly':
        return now + timedelta(hours=1)
    
    elif schedule.frequency == 'daily':
        hour, minute = map(int, schedule.time.split(':'))
        
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if next_run <= now:
            next_run += timedelta(days=1)
        
        return next_run
    
    elif schedule.frequency == 'weekly':
        hour, minute = map(int, schedule.time.split(':'))
        
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        current_weekday = now.weekday()
        target_weekday = schedule.day_of_week if schedule.day_of_week != 0 else 7  
        target_weekday = target_weekday - 1 if target_weekday != 7 else 6  
        
        days_ahead = (target_weekday - current_weekday) % 7
        
       
        if days_ahead == 0 and next_run <= now:
            days_ahead = 7
        
        next_run += timedelta(days=days_ahead)
        return next_run
    
    elif schedule.frequency == 'monthly':
        hour, minute = map(int, schedule.time.split(':'))
        
        
        try:
            next_run = now.replace(
                day=schedule.day_of_month,
                hour=hour,
                minute=minute,
                second=0,
                microsecond=0
            )
            
           
            if next_run <= now:
                if now.month == 12:
                    next_run = next_run.replace(year=now.year + 1, month=1)
                else:
                    next_run = next_run.replace(month=now.month + 1)
        except ValueError:
            if now.month == 12:
                if LOCAL_TZ:
                    next_run = datetime(now.year + 1, 1, schedule.day_of_month, hour, minute, 0, 0, tzinfo=LOCAL_TZ)
                else:
                    next_run = datetime(now.year + 1, 1, schedule.day_of_month, hour, minute, 0, 0).astimezone()
            else:
                if LOCAL_TZ:
                    next_run = datetime(now.year, now.month + 1, schedule.day_of_month, hour, minute, 0, 0, tzinfo=LOCAL_TZ)
                else:
                    next_run = datetime(now.year, now.month + 1, schedule.day_of_month, hour, minute, 0, 0).astimezone()
        
        return next_run
    
    return now

@router.post("", response_model=ScanSchedulePublic, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule_data: ScanScheduleCreate,
    request: Request,
    db: Session = Depends(get_db),
    _role=Depends(require_role("mod"))
):
    user_info = get_user_info_from_request(request)
    
    schedule = ScanSchedule(**schedule_data.dict())
    schedule.created_by = user_info["username"]
    schedule.updated_by = user_info["username"]
   
    schedule.next_run = calculate_next_run(schedule)
    
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    schedule_audit_log(db, request, "create", f"Scheduler creado: {schedule.name}", {"schedule_id": schedule.id, "name": schedule.name, "scan_type": schedule.scan_type})
    ws_manager = get_ws_manager()
    await ws_manager.send_schedule_update({
        "action" : "created",
        "schedule": schedule_to_dict(schedule)
    })

    return schedule


@router.get("", response_model=List[ScanSchedulePublic])
def list_schedules(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    schedules = db.query(ScanSchedule).offset(skip).limit(limit).all()
    return schedules


@router.get("/{schedule_id}", response_model=ScanSchedulePublic)
def get_schedule(
    schedule_id: int,
    db: Session = Depends(get_db)
):
    schedule = db.query(ScanSchedule).filter(ScanSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Programación no encontrada")
    return schedule


@router.put("/{schedule_id}", response_model=ScanSchedulePublic)
async def update_schedule(
    schedule_id: int,
    schedule_data: ScanScheduleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    _role=Depends(require_role("mod"))
):
    schedule = db.query(ScanSchedule).filter(ScanSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Programación no encontrada")
    
    user_info = get_user_info_from_request(request)
    
    # Actualizar campos
    update_data = schedule_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(schedule, field, value)
    
    schedule.updated_by = user_info["username"]
    
    # Recalcular next_run
    schedule.next_run = calculate_next_run(schedule)
    if LOCAL_TZ:
        schedule.updated_at = datetime.now(LOCAL_TZ)
    else:
        schedule.updated_at = datetime.now().astimezone()
    
    db.commit()
    db.refresh(schedule)
    schedule_audit_log(db, request, "update", f"Scheduler actualizado: {schedule.name}", {"schedule_id": schedule_id, "changes": update_data})

    ws_manager = get_ws_manager()
    
    await ws_manager.send_schedule_update({
        "action" : "toggled",
        "schedule" : schedule_to_dict(schedule)
    }) 
   


    return schedule


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: int,
    request: Request,
    db: Session = Depends(get_db),
    _role=Depends(require_role("mod"))
):
    schedule = db.query(ScanSchedule).filter(ScanSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Programación no encontrada")
    
    schedule_name = schedule.name
    schedule_audit_log(db, request, "delete", f"Scheduler eliminado: {schedule_name}", {"schedule_id": schedule_id, "name": schedule_name})
    db.delete(schedule)
    db.commit()
    try:
        ws_manager = get_ws_manager()
        await ws_manager.send_schedule_update({
            "action": "deleted",
            "schedule_id": schedule_id 
        })

    except Exception as e:
        pass

    return None


@router.post("/{schedule_id}/toggle", response_model=ScanSchedulePublic)
async def toggle_schedule(
    schedule_id: int,
    request: Request,
    db: Session = Depends(get_db),
    _role=Depends(require_role("mod"))
):
    schedule = db.query(ScanSchedule).filter(ScanSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Programación no encontrada")
    
    user_info = get_user_info_from_request(request)
    
    # Toggle enabled
    schedule.enabled = not schedule.enabled
    schedule.updated_by = user_info["username"]
    
    if schedule.enabled:
        # Recalcular next_run
        schedule.next_run = calculate_next_run(schedule)
    else:
        schedule.next_run = None
    
    if LOCAL_TZ:
        schedule.updated_at = datetime.now(LOCAL_TZ)
    else:
        schedule.updated_at = datetime.now().astimezone()
    db.commit()
    db.refresh(schedule)
    schedule_audit_log(db, request, "update", f"Scheduler {'activado' if schedule.enabled else 'desactivado'}: {schedule.name}", {"schedule_id": schedule_id, "enabled": schedule.enabled})
    
    return schedule


@router.post("/{schedule_id}/run-now", status_code=status.HTTP_202_ACCEPTED)
async def run_schedule_now(
    schedule_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _role=Depends(require_role("op"))
):
    schedule = db.query(ScanSchedule).filter(ScanSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Programación no encontrada")
    
    schedule_audit_log(db, request, "scan", f"Ejecución manual de scheduler: {schedule.name}", {"schedule_id": schedule_id, "name": schedule.name})
    
    from app.database import SessionLocal
    background_tasks.add_task(execute_scheduled_scan, schedule_id, SessionLocal())
    
    return {"message": "Scan iniciado", "schedule_id": schedule_id}


@router.get("/{schedule_id}/results")
def get_schedule_result(schedule_id : int, db: Session = Depends(get_db)):
    schedule = db.query(ScanSchedule).filter(ScanSchedule.id== schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Programación no encontrada")

    # Primero buscar en cache (resultado más reciente en memoria)
    cached = _cache_get(schedule_id)
    if cached is not None:
        return { "schedule_id" : schedule_id, "has_results": True, "results": cached}

    # Si no está en cache, buscar el último resultado en la base de datos
    latest = db.query(ScanHistory).filter(
        ScanHistory.schedule_id == schedule_id
    ).order_by(ScanHistory.executed_at.desc()).first()
    
    if not latest:
        return {"schedule_id": schedule_id, "has_results": False, "message": "No se han ejecutado escaneos todavía"}

    return {
        "schedule_id": schedule_id,
        "has_results": True,
        "results": {
            "timestamp": latest.executed_at.isoformat() if latest.executed_at else None,
            "scan_type": latest.scan_type,
            "action_type": latest.action_type,
            "targets_count": latest.targets_count,
            "scan_results": latest.scan_results,
            "shutdown_results": latest.shutdown_results,
            "status": latest.status,
            "error": latest.error_message,
            "duration_seconds": latest.duration_seconds
        }
    }


@router.get("/history/all")
def get_all_scan_history(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    total = db.query(ScanHistory).count()
    entries = db.query(ScanHistory).order_by(
        ScanHistory.executed_at.desc()
    ).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "items": [
            {
                "id": e.id,
                "schedule_id": e.schedule_id,
                "schedule_name": e.schedule_name,
                "scan_type": e.scan_type,
                "action_type": e.action_type,
                "targets_count": e.targets_count,
                "status": e.status,
                "duration_seconds": e.duration_seconds,
                "error_message": e.error_message,
                "executed_at": e.executed_at.isoformat() if e.executed_at else None,
            }
            for e in entries
        ]
    }


@router.get("/{schedule_id}/history")
def get_schedule_history(
    schedule_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    schedule = db.query(ScanSchedule).filter(ScanSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Programación no encontrada")
    
    total = db.query(ScanHistory).filter(ScanHistory.schedule_id == schedule_id).count()
    entries = db.query(ScanHistory).filter(
        ScanHistory.schedule_id == schedule_id
    ).order_by(ScanHistory.executed_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "schedule_id": schedule_id,
        "schedule_name": schedule.name,
        "total": total,
        "items": [
            {
                "id": e.id,
                "schedule_id": e.schedule_id,
                "schedule_name": e.schedule_name,
                "scan_type": e.scan_type,
                "action_type": e.action_type,
                "targets_count": e.targets_count,
                "status": e.status,
                "duration_seconds": e.duration_seconds,
                "error_message": e.error_message,
                "executed_at": e.executed_at.isoformat() if e.executed_at else None,
            }
            for e in entries
        ]
    }


@router.get("/history/{history_id}/detail")
def get_history_detail(
    history_id: int,
    db: Session = Depends(get_db)
):
    entry = db.query(ScanHistory).filter(ScanHistory.id == history_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="History entry not found")
    
    return {
        "id": entry.id,
        "schedule_id": entry.schedule_id,
        "schedule_name": entry.schedule_name,
        "scan_type": entry.scan_type,
        "action_type": entry.action_type,
        "targets_count": entry.targets_count,
        "status": entry.status,
        "duration_seconds": entry.duration_seconds,
        "scan_results": entry.scan_results,
        "shutdown_results": entry.shutdown_results,
        "error_message": entry.error_message,
        "executed_at": entry.executed_at.isoformat() if entry.executed_at else None,
    }


@router.delete("/history/{history_id}")
def delete_history_entry(
    history_id: int,
    db: Session = Depends(get_db),
    _role=Depends(require_role("mod"))
):
    entry = db.query(ScanHistory).filter(ScanHistory.id == history_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="History entry not found")
    
    db.delete(entry)
    db.commit()
    return {"message": "Entrada eliminada"}


async def execute_scheduled_scan(schedule_id: int, db: Session):
    
    try:
        await _execute_scheduled_scan_inner(schedule_id, db)
    finally:
        try:
            db.close()
        except Exception:
            pass


async def _execute_scheduled_scan_inner(schedule_id: int, db: Session):
    schedule = db.query(ScanSchedule).filter(ScanSchedule.id == schedule_id).first()
    if not schedule or not schedule.enabled:
        return

    scan_results = []
    start_time = time.time()
    
    try:
        # Determinar targets
        targets = []
        if schedule.target_subnet:
            targets = expand_network(schedule.target_subnet)
        elif schedule.target_range:
            # Parsear rango (192.168.0.1-192.168.0.254)
            start_ip, end_ip = schedule.target_range.split('-')
            start_parts = start_ip.strip().split('.')
            end_parts = end_ip.strip().split('.')
            
            base = '.'.join(start_parts[:3])
            start_num = int(start_parts[3])
            end_num = int(end_parts[3]) if len(end_parts) == 4 else int(end_parts[0])
            
            targets = [f"{base}.{i}" for i in range(start_num, end_num + 1)]
        elif schedule.target_hosts:
            targets = [h.strip() for h in schedule.target_hosts.split(',')]
        else:
            targets = expand_network("192.168.0.0/24")  # Default
        
        # Solo ejecutar escaneo si action_type es 'scan' o 'both'
        if schedule.action_type in ['scan', 'both']:
            # Ejecutar escaneo según tipo
            if schedule.scan_type == 'ping':
                results = await ping_multiple(targets)
                scan_results = results
            
            elif schedule.scan_type == 'ports':
                results = await scan_ports_segment(targets, "1-1024")
                scan_results = results
            
            elif schedule.scan_type == 'services':
                results = await scan_services_segment(targets, "1-1024")
                scan_results = results
            
            elif schedule.scan_type == 'os':
                results = []
                for target in targets:
                    result = await detect_os(target)
                    results.append({"host": target, "os": result})
                scan_results = results
            
            elif schedule.scan_type == 'mac':
                if schedule.target_subnet:
                    results = await scan_mac(schedule.target_subnet)
                    scan_results = results

                else:
                    from app.scanners import get_mac_single_host
                    results = []
                    for target in targets:
                        mac, vendor = await asyncio.to_thread(get_mac_single_host, target)
                        results.append({"ip": target, "mac": mac, "vendor": vendor})
                    scan_results = results        

            elif schedule.scan_type == 'full':
                # Full scan con guardado en base de datos (solo IPs activas)
                from app import crud
                results = []
                for target in targets:
                    try:
                        result = await full_host_scan(target, emit_progress=True, scan_id=str(schedule_id))
                        host_status = result.get("status", "unknown")
                        if host_status == "up":
                            # Solo guardar hosts activos
                            crud.create_or_update_host(db, result)
                        else:
                            # Si ya existía, marcar como inactivo
                            existing = crud.get_host_by_ip(db, target)
                            if existing:
                                crud.mark_host_as_down(db, target)
                        results.append(result)
                    except Exception as e:
                        results.append({"host": target, "status": "error", "error": str(e)})
                scan_results = results
        # Ejecutar apagado si action_type es 'shutdown' o 'both'
        shutdown_results = []
        # Ejecutar apagado si action_type es 'shutdown' o 'both'
        if schedule.action_type in ['shutdown', 'both']:
            # Si es 'both', verificar si debe apagar después del escaneo
            if schedule.action_type == 'both' and not schedule.shutdown_after_scan:
                pass  # No apagar
            else:
                # Usar shutdown_targets o los targets del escaneo
                shutdown_targets = targets
                if schedule.shutdown_targets:
                    shutdown_targets = [ip.strip() for ip in schedule.shutdown_targets.split(',')]
                
                # Primero hacer ping para detectar cuáles están activas
                try:
                    ping_results = await ping_multiple(shutdown_targets)
                    active_ips = []
                    inactive_ips = []
                    for pr in ping_results:
                        ip = pr.get('host', pr.get('ip', ''))
                        if pr.get('status') == 'up' or pr.get('alive', False):
                            active_ips.append(ip)
                        else:
                            inactive_ips.append(ip)
                except Exception:
                    # Si falla el ping, intentar con todas
                    active_ips = shutdown_targets
                    inactive_ips = []
                
                # Solo intentar apagar IPs activas
                async def shutdown_single(target_ip):
                    try:
                        result = await shutdown_host_ssh(
                            host=target_ip,
                            username=schedule.ssh_username,
                            password=schedule.ssh_password,
                        )
                        # Verificar el resultado real de shutdown_host_ssh
                        if result.get('success', False):
                            return {"host": target_ip, "status": "success", "message": result.get("message", "")}
                        else:
                            return {"host": target_ip, "status": "error", "error": result.get("message", "Fallo en apagado")}
                    except Exception as e:
                        return {"host": target_ip, "status": "error", "error": str(e)}
                
                if active_ips:
                    # Ejecutar apagados en paralelo solo para IPs activas
                    raw_results = await asyncio.gather(
                        *[shutdown_single(ip) for ip in active_ips],
                        return_exceptions=True
                    )
                    
                    shutdown_results = [
                        r if isinstance(r, dict) else {"host": "unknown", "status": "error", "error": str(r)}
                        for r in raw_results
                    ]
                
                # Agregar metadata de IPs activas/inactivas al resultado
                success_ips = [r['host'] for r in shutdown_results if r.get('status') == 'success']
                failed_ips = [r for r in shutdown_results if r.get('status') == 'error']
                
                shutdown_results = {
                    "active_ips": active_ips,
                    "inactive_ips": inactive_ips,
                    "success_ips": success_ips,
                    "failed_ips": failed_ips,
                    "total_active": len(active_ips),
                    "total_inactive": len(inactive_ips),
                    "total_success": len(success_ips),
                    "total_failed": len(failed_ips)
                }
        
        # Actualizar last_run y next_run
        now_local = datetime.now(LOCAL_TZ) if LOCAL_TZ else datetime.now().astimezone()
        duration = time.time() - start_time
        
        # Guardar en cache (para compatibilidad) y en base de datos
        result_data = {
            "timestamp": now_local.isoformat(),
            "scan_type" : schedule.scan_type,
            "action_type": schedule.action_type,
            "targets_count" : len(targets),
            "scan_results" : serialize_for_json(scan_results),
            "shutdown_results": serialize_for_json(shutdown_results) if shutdown_results else None,
            "status": "success"
        }
        _cache_set(schedule_id, result_data)
        
        # Persistir en base de datos
        history_entry = ScanHistory(
            schedule_id=schedule_id,
            schedule_name=schedule.name,
            scan_type=schedule.scan_type,
            action_type=schedule.action_type,
            targets_count=len(targets),
            status="success",
            duration_seconds=round(duration, 2),
            scan_results=serialize_for_json(scan_results),
            shutdown_results=serialize_for_json(shutdown_results) if shutdown_results else None,
            executed_at=now_local
        )
        db.add(history_entry)


        schedule.last_run = now_local
        schedule.next_run = calculate_next_run(schedule)
        db.commit()
        db.refresh(schedule)

        ws_manager = get_ws_manager()
        await ws_manager.send_schedule_update({
            "action" : "executed",
            "schedule": schedule_to_dict(schedule),
            "shutdown_results": serialize_for_json(shutdown_results) if shutdown_results else None
        })


    except Exception as e:
        now_local = datetime.now(LOCAL_TZ) if LOCAL_TZ else datetime.now().astimezone()
        duration = time.time() - start_time
        
        error_data = {
            "timestamp" : now_local.isoformat(),
            "scan_type" : schedule.scan_type if schedule else None,
            "action_type": schedule.action_type if schedule else None,
            "targets_count": 0,
            "scan_results": [],
            "shutdown_results" : None,
            "status" : "error",
            "error" : str(e)
        }
        _cache_set(schedule_id, error_data)
        
        # Persistir error en base de datos
        try:
            history_entry = ScanHistory(
                schedule_id=schedule_id,
                schedule_name=schedule.name if schedule else None,
                scan_type=schedule.scan_type if schedule else None,
                action_type=schedule.action_type if schedule else None,
                targets_count=0,
                status="error",
                duration_seconds=round(duration, 2),
                scan_results=None,
                shutdown_results=None,
                error_message=str(e),
                executed_at=now_local
            )
            db.add(history_entry)
            db.commit()
        except Exception:
            db.rollback()

async def execute_shutdown(schedule: ScanSchedule):
    
    if not schedule.shutdown_targets or not schedule.ssh_username:
        return
    
    targets = [ip.strip() for ip in schedule.shutdown_targets.split(',')]
    
    async def shutdown_single(target_ip):
        try:
            await shutdown_host_ssh(
                host=target_ip,
                username=schedule.ssh_username,
                password=schedule.ssh_password,
            )
            return {"host": target_ip, "status": "success"}
        except Exception as e:
            return {"host": target_ip, "status": "error", "error": str(e)}
    
    # Ejecutar todos los apagados en paralelo
    results = await asyncio.gather(
        *[shutdown_single(ip) for ip in targets],
        return_exceptions=True
    )
    
    return results


# Endpoint adicional para apagar segmento de red
@router.post("/shutdown/segment", status_code=status.HTTP_202_ACCEPTED)
async def shutdown_network_segment(
    target_subnet: str,
    ssh_username: str,
    ssh_password: str,
    
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    _role=Depends(require_role("op"))
):
   
    try:
        # Expandir red a lista de IPs
        targets = expand_network(target_subnet)
        
        # Ejecutar apagado en background
        if background_tasks:
            background_tasks.add_task(
                shutdown_segment_background,
                targets,
                ssh_username,
                ssh_password,
    
            )
        else:
            await shutdown_segment_background(
                targets,
                ssh_username,
                ssh_password,
                
            )
        
        return {
            "message": f"Apagando {len(targets)} hosts en {target_subnet} (en paralelo)",
            "targets_count": len(targets)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def shutdown_segment_background(
    targets: List[str],
    username: str,
    password: str,
    
):
   
    async def shutdown_single(target_ip):
        try:
            await shutdown_host_ssh(
                host=target_ip,
                username=username,
                password=password,
            )
            return {"ip": target_ip, "status": "success"}
        except Exception as e:
            return {"ip": target_ip, "status": "failed", "error": str(e)}
    
    # Ejecutar todos los apagados en paralelo con semáforo para limitar concurrencia
    semaphore = asyncio.Semaphore(50)  # Máximo 50 conexiones simultáneas
    
    async def shutdown_with_semaphore(target_ip):
        async with semaphore:
            return await shutdown_single(target_ip)
    
    results = await asyncio.gather(
        *[shutdown_with_semaphore(ip) for ip in targets],
        return_exceptions=True
    )
    
    # Procesar resultados
    success_list = []
    failed_list = []
    
    for r in results:
        if isinstance(r, dict):
            if r.get("status") == "success":
                success_list.append(r["ip"])
            else:
                failed_list.append(r)
        else:
            failed_list.append({"ip": "unknown", "error": str(r)})
    
    return {"success": success_list, "failed": failed_list}

