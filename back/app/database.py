from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import INET
from datetime import datetime, timezone
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://scanner:scanner123@192.168.0.11:5432/network_scanner"
)

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Modelos
class Host(Base):
    __tablename__ = "hosts"

    id = Column(Integer, primary_key=True, index=True)
    ip = Column(INET, unique=True, nullable=False, index=True)
    hostname = Column(String(255))
    nickname = Column(String(255))
    mac = Column(String(17))
    vendor = Column(String(255))
    os_name = Column(String(255))
    os_accuracy = Column(Integer)
    status = Column(String(20), default="unknown")
    latency_ms = Column(Float)
    last_seen = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relaciones
    ports = relationship("Port", back_populates="host", cascade="all, delete-orphan")
    services = relationship("Service", back_populates="host", cascade="all, delete-orphan")
    vulnerabilities = relationship("Vulnerability", back_populates="host", cascade="all, delete-orphan")
    connection_history = relationship("ConnectionHistory", back_populates="host", cascade="all, delete-orphan")


class Port(Base):
    __tablename__ = "ports"

    id = Column(Integer, primary_key=True, index=True)
    host_id = Column(Integer, ForeignKey("hosts.id", ondelete="CASCADE"))
    port = Column(Integer, nullable=False)
    protocol = Column(String(10))
    service = Column(String(100))
    state = Column(String(20))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    host = relationship("Host", back_populates="ports")


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    host_id = Column(Integer, ForeignKey("hosts.id", ondelete="CASCADE"))
    port = Column(Integer, nullable=False)
    protocol = Column(String(10))
    service_name = Column(String(100))
    product = Column(String(255))
    version = Column(String(100))
    extra_info = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    host = relationship("Host", back_populates="services")


class Vulnerability(Base):
    __tablename__ = "vulnerabilities"

    id = Column(Integer, primary_key=True, index=True)
    host_id = Column(Integer, ForeignKey("hosts.id", ondelete="CASCADE"))
    port = Column(Integer)
    script_name = Column(String(255))
    severity = Column(String(20))
    description = Column(Text)
    output = Column(Text)
    discovered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    host = relationship("Host", back_populates="vulnerabilities")


class ConnectionHistory(Base):
    __tablename__ = "connection_history"

    id = Column(Integer, primary_key=True, index=True)
    host_id = Column(Integer, ForeignKey("hosts.id", ondelete="CASCADE"))
    status = Column(String(20))
    latency_ms = Column(Float)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    host = relationship("Host", back_populates="connection_history")


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Crear todas las tablas
def create_tables():
    Base.metadata.create_all(bind=engine)
