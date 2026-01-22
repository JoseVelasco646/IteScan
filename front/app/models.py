from sqlalchemy import (
    Column, Integer, String, Float, DateTime, JSON, Boolean
)
from sqlalchemy.sql import func
from app.database import Base

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
    scan_type = Column(String)  # 'ping', 'ports', 'services', 'os', 'mac', 'full'
    frequency = Column(String, nullable=False)  # 'hourly', 'daily', 'weekly', 'monthly'
    time = Column(String)  # "HH:MM" format
    day_of_week = Column(Integer)  # 0-6 (for weekly)
    day_of_month = Column(Integer)  # 1-31 (for monthly)
    enabled = Column(Boolean, default=True)
    next_run = Column(DateTime(timezone=True))
    last_run = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Opciones adicionales de escaneo
    target_range = Column(String)  # "192.168.0.1-192.168.0.254"
    target_subnet = Column(String)  # "192.168.0.0/24"
    target_hosts = Column(String)  # Lista de hosts separados por comas
    
    # Apagado automático
    auto_shutdown = Column(Boolean, default=False)  # Si se activa apagado automático
    shutdown_after_scan = Column(Boolean, default=False)  # Apagar después del escaneo
    shutdown_time = Column(String)  # Hora de apagado "HH:MM"
    shutdown_targets = Column(String)  # IPs a apagar (separadas por comas)
    ssh_username = Column(String)  # Usuario SSH para apagado
    ssh_password = Column(String)  # Contraseña SSH (debería encriptarse en producción)
    ssh_sudo_password = Column(String)  # Contraseña sudo para apagado