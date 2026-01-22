"""
Servicio de ejecución automática de scans programados.
Este servicio revisa periódicamente los schedules y ejecuta los que deben correr.
"""
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import ScanSchedule
from app.schedule_routes import execute_scheduled_scan, calculate_next_run


class SchedulerService:
    """Servicio que ejecuta automáticamente los scans programados"""
    
    def __init__(self):
        self.running = False
        self.check_interval = 60  # Revisar cada 60 segundos
        self.tz = ZoneInfo('America/Tijuana')
    
    async def start(self):
        """Inicia el servicio de scheduling"""
        self.running = True
        
        while self.running:
            try:
                await self.check_and_execute_schedules()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                await asyncio.sleep(self.check_interval)
    
    async def check_and_execute_schedules(self):
        """Revisa y ejecuta los schedules que deben correr. Si un schedule está vencido, solo se reprograma su next_run sin ejecutarlo."""
        db = SessionLocal()
        try:
            now = datetime.now(self.tz)
            # Obtener todos los schedules activos
            schedules = db.query(ScanSchedule).filter(
                ScanSchedule.enabled == True
            ).all()
            for schedule in schedules:
                if schedule.next_run:
                    if schedule.next_run <= now:
                        # Si el next_run está vencido, solo reprográmalo, NO ejecutar el scan
                        schedule.next_run = calculate_next_run(schedule)
                        schedule.last_run = now
                        db.commit()
        except Exception as e:
            db.rollback()
        finally:
            db.close()
    
    def stop(self):
        """Detiene el servicio"""
        self.running = False


# Instancia global del servicio
scheduler_service = SchedulerService()


async def start_scheduler_service():
    """Inicia el servicio de scheduler (para usar en lifespan)"""
    await scheduler_service.start()


def stop_scheduler_service():
    """Detiene el servicio de scheduler"""
    scheduler_service.stop()
