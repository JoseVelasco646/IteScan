import asyncio
import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from app.database import SessionLocal, ConnectionHistory
from app.models import ScanSchedule, AuditLog
from app.schedule_routes import execute_scheduled_scan, calculate_next_run

logger = logging.getLogger("app")

HISTORY_RETENTION_DAYS = int(__import__("os").getenv("HISTORY_RETENTION_DAYS", "90"))


class SchedulerService:
    
    def __init__(self):
        self.running = False
        self.check_interval = 60
        self._cleanup_counter = 0
        self._cleanup_every = 1440
        try:
            self.tz = ZoneInfo('America/Tijuana')
        except Exception:
            self.tz = None
    
    async def start(self):
        self.running = True
        
        while self.running:
            try:
                await self.check_and_execute_schedules()
                self._cleanup_counter += 1
                if self._cleanup_counter >= self._cleanup_every:
                    self._cleanup_counter = 0
                    await self._cleanup_old_history()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error en scheduler loop: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def check_and_execute_schedules(self):
        db = SessionLocal()
        try:
            if self.tz:
                now = datetime.now(self.tz)
            else:
                now = datetime.now().astimezone()
            

            EXPIRED_THRESHOLD_MINUTES = 10
            
            schedules = db.query(ScanSchedule).filter(
                ScanSchedule.enabled == True
            ).all()
            
            for schedule in schedules:
                if schedule.next_run:
                    next_run = schedule.next_run
                    
                    if next_run.tzinfo is None:
                        if self.tz:
                            next_run = next_run.replace(tzinfo=self.tz)
                        else:
                            next_run = next_run.astimezone()
                    
                    if next_run <= now:
                        from datetime import timedelta
                        time_diff = now - next_run
                        if time_diff > timedelta(minutes=EXPIRED_THRESHOLD_MINUTES):
                            schedule.next_run = calculate_next_run(schedule)
                            db.commit()
                            continue
                        
                        await execute_scheduled_scan(schedule.id, db)
                        
                        schedule.next_run = calculate_next_run(schedule)
                        schedule.last_run = now
                        db.commit()
        except Exception as e:
            db.rollback()
        finally:
            db.close()
    
    def stop(self):
        self.running = False

    async def _cleanup_old_history(self):
        db = SessionLocal()
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=HISTORY_RETENTION_DAYS)
            deleted_conn = db.query(ConnectionHistory).filter(
                ConnectionHistory.timestamp < cutoff
            ).delete(synchronize_session="fetch")
            deleted_audit = db.query(AuditLog).filter(
                AuditLog.created_at < cutoff
            ).delete(synchronize_session="fetch")

            # Limpiar intentos de login antiguos
            from app.auth import cleanup_old_login_attempts
            cleanup_old_login_attempts(db)

            db.commit()
            if deleted_conn or deleted_audit:
                logger.info(
                    f"Cleanup: eliminados {deleted_conn} registros de connection_history "
                    f"y {deleted_audit} de audit_log (>{HISTORY_RETENTION_DAYS} días)"
                )
        except Exception as e:
            logger.error(f"Error en cleanup de historial: {e}")
            db.rollback()
        finally:
            db.close()


scheduler_service = SchedulerService()


async def start_scheduler_service():
    await scheduler_service.start()


def stop_scheduler_service():
    scheduler_service.stop()
