from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta, timezone


import asyncio

from app.database import get_db
from app.models import ScanSchedule
from app.schedule_schemas import (
    ScanScheduleCreate,
    ScanScheduleUpdate,
    ScanScheduleResponse
)
from app import crud
from app.ping import (
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


scan_result_cache = {}

def get_ws_manager():
    from app.websocket_manager import ws_manager
    return ws_manager

def schedule_to_dict(schedule: ScanSchedule) -> dict:
    """Convierte un schedule a un dict serializable a JSON"""
    schedule_dict = ScanScheduleResponse.from_orm(schedule).dict()
    # Convertir datetime a strings ISO
    
    return serialize_for_json(schedule_dict)

def serialize_for_json(obj):
    """Serializa recursivamente objetos para JSON, convirtiendo datetime a strings"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: serialize_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]
    else:
        return obj

def calculate_next_run(schedule: ScanSchedule) -> datetime:
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
        
        days_ahead = schedule.day_of_week - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        next_run += timedelta(days=days_ahead)
        return next_run
    
    elif schedule.frequency == 'monthly':
        hour, minute = map(int, schedule.time.split(':'))
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
        return next_run
    
    return now

@router.post("", response_model=ScanScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule_data: ScanScheduleCreate,
    db: Session = Depends(get_db)
):
    """Crear un nuevo schedule"""
    # Crear el schedule en la DB
    schedule = ScanSchedule(**schedule_data.dict())
    
    # Calcular next_run
    schedule.next_run = calculate_next_run(schedule)
    
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    ws_manager = get_ws_manager()
    await ws_manager.send_schedule_update({
        "action" : "created",
        "schedule": schedule_to_dict(schedule)
    })

    return schedule


@router.get("", response_model=List[ScanScheduleResponse])
def list_schedules(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Listar todos los schedules"""
    schedules = db.query(ScanSchedule).offset(skip).limit(limit).all()
    return schedules


@router.get("/{schedule_id}", response_model=ScanScheduleResponse)
def get_schedule(
    schedule_id: int,
    db: Session = Depends(get_db)
):
    """Obtener un schedule por ID"""
    schedule = db.query(ScanSchedule).filter(ScanSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule


@router.put("/{schedule_id}", response_model=ScanScheduleResponse)
async def update_schedule(
    schedule_id: int,
    schedule_data: ScanScheduleUpdate,
    db: Session = Depends(get_db)
):
    """Actualizar un schedule"""
    schedule = db.query(ScanSchedule).filter(ScanSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    # Actualizar campos
    update_data = schedule_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(schedule, field, value)
    
    # Recalcular next_run
    schedule.next_run = calculate_next_run(schedule)
    schedule.updated_at = datetime.now()
    
    db.commit()
    db.refresh(schedule)

    ws_manager = get_ws_manager()
    
    await ws_manager.send_schedule_update({
        "action" : "toggled",
        "schedule" : schedule_to_dict(schedule)
    }) 
   


    return schedule


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db)
):
    """Eliminar un schedule"""
    schedule = db.query(ScanSchedule).filter(ScanSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
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


@router.post("/{schedule_id}/toggle", response_model=ScanScheduleResponse)
async def toggle_schedule(
    schedule_id: int,
    db: Session = Depends(get_db)
):
    """Activar/Desactivar un schedule"""
    schedule = db.query(ScanSchedule).filter(ScanSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    # Toggle enabled
    schedule.enabled = not schedule.enabled
    
    if schedule.enabled:
        # Recalcular next_run
        schedule.next_run = calculate_next_run(schedule)
    else:
        schedule.next_run = None
    
    schedule.updated_at = datetime.now()
    db.commit()
    db.refresh(schedule)
    
    return schedule


@router.post("/{schedule_id}/run-now", status_code=status.HTTP_202_ACCEPTED)
async def run_schedule_now(
    schedule_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Ejecutar un schedule inmediatamente"""
    schedule = db.query(ScanSchedule).filter(ScanSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    # Ejecutar en background
    background_tasks.add_task(execute_scheduled_scan, schedule_id, db)
    
    return {"message": "Scan iniciado", "schedule_id": schedule_id}


@router.get("/{schedule_id}/results")
def get_schedule_result(schedule_id : int, db: Session = Depends(get_db)):
    schedule = db.query(ScanSchedule).filter(ScanSchedule.id== schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    if schedule_id not in scan_result_cache:
        return {"schedule_id": schedule_id,
        "has_results": False, "message": "No se ha ejecutado scans odvia"}

    return { "schedule_id" : schedule_id, "has_results": True, "results": scan_result_cache[schedule_id]}


async def execute_scheduled_scan(schedule_id: int, db: Session):
    """Ejecuta un escaneo programado"""
    schedule = db.query(ScanSchedule).filter(ScanSchedule.id == schedule_id).first()
    if not schedule or not schedule.enabled:
        return

    scan_results = []
    scan_status = 'sucess'
    
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
                    from app.ping import get_mac_single_host
                    results = []
                    for target in targets:
                        mac, vendor = await asyncio.to_thread(get_mac_single_host, target)
                        results.append({"ip":target, "mac":target, "vendor": vendor})
                    scan_results = results        

            elif schedule.scan_type == 'full':
                # Full scan con guardado en base de datos
                from app import crud
                results = []
                for target in targets:
                    try:
                        result = await full_host_scan(target, emit_progress=True, scan_id=str(schedule_id))
                        # Guardar en la base de datos
                        crud.create_or_update_host(db, result)
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
                
                # Ejecutar apagado en PARALELO para todos los hosts
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
                shutdown_results = await asyncio.gather(
                    *[shutdown_single(ip) for ip in shutdown_targets],
                    return_exceptions=True
                )
                
                # Procesar resultados que podrían ser excepciones
                shutdown_results = [
                    r if isinstance(r, dict) else {"host": "unknown", "status": "error", "error": str(r)}
                    for r in shutdown_results
                ]
        
        # Actualizar last_run y next_run
        
        scan_result_cache[schedule_id] = {
            "timestamp": datetime.now().astimezone().isoformat(),
            "scan_type" : schedule.scan_type,
            "action_type": schedule.action_type,
            "targets_count" : len(targets),
            "scan_results" : serialize_for_json(scan_results),
            "shutdown_results": serialize_for_json(shutdown_results) if shutdown_results else None,
            "status": "success"
        }


        schedule.last_run = datetime.now().astimezone()
        schedule.next_run = calculate_next_run(schedule)
        db.commit()
        db.refresh(schedule)

        ws_manager = get_ws_manager()
        await ws_manager.send_schedule_update({
            "action" : "executed",
            "schedule": schedule_to_dict(schedule)
        })


    except Exception as e:
        scan_result_cache[schedule_id] = {
            "timestamp" : datetime.now().astimezone().isoformat(),
            "scan_type" : schedule.scan_type if schedule else None,
            "action_type": schedule.action_type if schedule else None,
            "targets_count": 0,
            "scan_results": [],
            "shutdown_results" : None,
            "status" : "error",
            "error" : str(e)
        }
        db.rollback()

async def execute_shutdown(schedule: ScanSchedule):
    """Ejecuta el apagado automático de hosts en PARALELO"""
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
    db: Session = Depends(get_db)
):
    """Apagar todos los hosts en un segmento de red (en PARALELO)"""
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
    """Apaga múltiples hosts en PARALELO"""
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

