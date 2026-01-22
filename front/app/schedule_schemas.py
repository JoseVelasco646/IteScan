from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ScanScheduleBase(BaseModel):
    name: str = Field(..., min_length=1)
    action_type: str = Field(default='scan', pattern=r'^(scan|shutdown|both)$')
    scan_type: Optional[str] = Field(None, pattern=r'^(ping|ports|services|os|mac|full)$')
    frequency: str = Field(..., pattern="^(hourly|daily|weekly|monthly)$")
    time: Optional[str] = Field(None, pattern="^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    day_of_month: Optional[int] = Field(None, ge=1, le=31)
    enabled: bool = True
    target_range: Optional[str] = None
    target_subnet: Optional[str] = None
    target_hosts: Optional[str] = None
    
    # Apagado automático
    auto_shutdown: bool = False
    shutdown_after_scan: bool = False
    shutdown_time: Optional[str] = None
    shutdown_targets: Optional[str] = None
    ssh_username: Optional[str] = None
    ssh_password: Optional[str] = None
    ssh_sudo_password: Optional[str] = None

class ScanScheduleCreate(ScanScheduleBase):
    pass

class ScanScheduleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    scan_type: Optional[str] = Field(None, pattern="^(ping|ports|services|os|mac|full)$")
    frequency: Optional[str] = Field(None, pattern="^(hourly|daily|weekly|monthly)$")
    time: Optional[str] = Field(None, pattern="^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    day_of_month: Optional[int] = Field(None, ge=1, le=31)
    enabled: Optional[bool] = None
    target_range: Optional[str] = None
    target_subnet: Optional[str] = None
    target_hosts: Optional[str] = None
    auto_shutdown: Optional[bool] = None
    shutdown_after_scan: Optional[bool] = None
    shutdown_time: Optional[str] = None
    shutdown_targets: Optional[str] = None
    ssh_username: Optional[str] = None
    ssh_password: Optional[str] = None
    ssh_sudo_password: Optional[str] = None

class ScanScheduleResponse(ScanScheduleBase):
    id: int
    next_run: Optional[datetime]
    last_run: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
