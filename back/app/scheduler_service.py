import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import ScanSchedule
from app.schedule_routes import execute_scheduled_scan, calculate_next_run


class SchedulerService:
    
    def __init__(self):
        self.running = False
        self.check_interval = 60
        try:
            self.tz = ZoneInfo('America/Tijuana')
        except Exception:
            self.tz = None
    
    async def start(self):
        self.running = True
        
        while self.running:
            try:
                await self.check_and_execute_schedules()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                await asyncio.sleep(self.check_interval)
    
    async def check_and_execute_schedules(self):
        db = SessionLocal()
        try:
            if self.tz:
                now = datetime.now(self.tz)
            else:
                now = datetime.now().astimezone()
            
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


scheduler_service = SchedulerService()


async def start_scheduler_service():
    await scheduler_service.start()


def stop_scheduler_service():
    scheduler_service.stop()
