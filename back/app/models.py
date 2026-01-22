from sqlalchemy import (
    Column, Integer, String, Float, DateTime, JSON, Boolean
)
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property
from app.database import Base
from app.encryption import encrypt_password, decrypt_password

class PingResult(Base):
    __tablename__ = "ping_results"

    id = Column(Integer, primary_key=True)
    host = Column(String, index=True)
    status = Column(String)
    latency_ms = Column(Float)
    method = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PortScan(Base):
    __tablename__ = "port_scans"

    id = Column(Integer, primary_key=True)
    host = Column(String, index=True)
    ports = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ServiceScan(Base):
    __tablename__ = "service_scans"

    id = Column(Integer, primary_key=True)
    host = Column(String, index=True)
    services = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class VulnerabilityScan(Base):
    __tablename__ = "vulnerability_scans"

    id = Column(Integer, primary_key=True)
    host = Column(String, index=True)
    vulnerabilities = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class OSScan(Base):
    __tablename__ = "os_scans"

    id = Column(Integer, primary_key=True)
    host = Column(String, index=True)
    os = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MacScan(Base):
    __tablename__ = "mac_scans"

    id = Column(Integer, primary_key=True)
    ip = Column(String, index=True)
    mac = Column(String)
    vendor = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ScanSchedule(Base):
    __tablename__ = "scan_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    action_type = Column(String, default='scan')
    scan_type = Column(String)  
    frequency = Column(String, nullable=False)  
    time = Column(String)  
    day_of_week = Column(Integer)  
    day_of_month = Column(Integer)  
    enabled = Column(Boolean, default=True)
    next_run = Column(DateTime(timezone=True))
    last_run = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    
    target_range = Column(String)  
    target_subnet = Column(String)  
    target_hosts = Column(String)  
    
    auto_shutdown = Column(Boolean, default=False)
    shutdown_after_scan = Column(Boolean, default=False)
    shutdown_time = Column(String)  
    shutdown_targets = Column(String)  
    ssh_username = Column(String)
    _ssh_password = Column("ssh_password", String)  
    _ssh_sudo_password = Column("ssh_sudo_password", String)  
    
    @hybrid_property
    def ssh_password(self):
        if self._ssh_password:
            try:
                return decrypt_password(self._ssh_password)
            except Exception:
                return self._ssh_password  
        return None
    
    @ssh_password.setter
    def ssh_password(self, value):
        if value:
            self._ssh_password = encrypt_password(value)
        else:
            self._ssh_password = None
    
    @hybrid_property
    def ssh_sudo_password(self):
        if self._ssh_sudo_password:
            try:
                return decrypt_password(self._ssh_sudo_password)
            except Exception:
                return self._ssh_sudo_password  
        return None
    
    @ssh_sudo_password.setter
    def ssh_sudo_password(self, value):
        if value:
            self._ssh_sudo_password = encrypt_password(value)
        else:
            self._ssh_sudo_password = None
