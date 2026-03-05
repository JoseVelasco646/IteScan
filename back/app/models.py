from sqlalchemy import (
    Column, Integer, String, Float, DateTime, JSON, Boolean, ForeignKey, Text
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
    created_by = Column(String(100))
    updated_by = Column(String(100))
    
    
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


class ScanHistory(Base):
    __tablename__ = "scan_history"
    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("scan_schedules.id", ondelete="SET NULL"), nullable=True, index=True)
    schedule_name = Column(String)
    scan_type = Column(String)
    action_type = Column(String)
    targets_count = Column(Integer, default=0)
    status = Column(String, default="success")  
    duration_seconds = Column(Float)
    scan_results = Column(JSON)
    shutdown_results = Column(JSON)
    error_message = Column(Text)
    executed_at = Column(DateTime(timezone=True), server_default=func.now())


class AdminUser(Base):
   
    __tablename__ = "admin_users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(255))
    role = Column(String(20), nullable=False, default='viewer')  
    is_super_admin = Column(Boolean, default=False)  
    is_active = Column(Boolean, default=True)
    must_change_password = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class FullScanHistory(Base):
    __tablename__ = "fullscan_history"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_type = Column(String, nullable=False)  
    target = Column(String, nullable=False)  
    hosts_scanned = Column(Integer, default=0)
    hosts_active = Column(Integer, default=0)
    total_ports = Column(Integer, default=0)
    total_services = Column(Integer, default=0)
    status = Column(String, default="success")  
    duration_seconds = Column(Float)
    scan_results = Column(JSON)  
    error_message = Column(Text)
    user_id = Column(Integer)
    username = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_log"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    username = Column(String(100), index=True)
    action = Column(String(50), nullable=False, index=True)  
    category = Column(String(50), nullable=False, index=True)  
    description = Column(Text, nullable=False)
    details = Column(JSON)  
    ip_address = Column(String(45))  
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class Subnet(Base):
    __tablename__ = "subnets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    start_ip = Column(String(45), nullable=False)
    end_ip = Column(String(45), nullable=False)
    created_by = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class SubnetDevice(Base):
    __tablename__ = "subnet_devices"

    id = Column(Integer, primary_key=True, index=True)
    subnet_id = Column(Integer, ForeignKey("subnets.id", ondelete="CASCADE"), nullable=False, index=True)
    ip = Column(String(45), nullable=False)
    label = Column(String(255))          
    device_type = Column(String(50), default="pc")  
    status = Column(String(20), default="grey")      
    last_scan_at = Column(DateTime(timezone=True))
    scan_data = Column(JSON)              
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class SSHCredential(Base):
    __tablename__ = "ssh_credentials"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    username = Column(String(255), nullable=False)
    _password = Column("password", String, nullable=False)
    created_by = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    @hybrid_property
    def password(self):
        if self._password:
            try:
                return decrypt_password(self._password)
            except Exception:
                return self._password
        return None

    @password.setter
    def password(self, value):
        if value:
            self._password = encrypt_password(value)
        else:
            self._password = None
