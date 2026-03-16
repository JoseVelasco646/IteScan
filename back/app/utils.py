import os
import logging
import json
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from fastapi import Request

from app.database import Host
from app.models import AuditLog
from app.auth import decode_token


MEXICO_TZ = ZoneInfo("America/Mexico_City")

ENV_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', '.env')


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False)



LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "app.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logger = logging.getLogger("app")
logger.setLevel(logging.INFO)

if not logger.handlers:

    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(JSONFormatter())


    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

logger.info("Sistema de autenticación admin iniciado")


def get_mexico_time():
    return datetime.now(MEXICO_TZ)


def update_env_file(key: str, value: str):
    try:
        if os.path.exists(ENV_FILE_PATH):
            with open(ENV_FILE_PATH, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        else:
            lines = []

        key_found = False
        new_lines = []
        for line in lines:
            if line.strip().startswith(f"{key}="):
                new_lines.append(f"{key}={value}\n")
                key_found = True
            else:
                new_lines.append(line)

        if not key_found:
            new_lines.append(f"{key}={value}\n")

        with open(ENV_FILE_PATH, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

        logger.info(f"Archivo .env actualizado: {key}={value}")
        return True
    except Exception as e:
        logger.error(f"Error actualizando .env: {e}")
        return False


def get_user_id(request: Request) -> int:
    try:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            payload = decode_token(auth_header.split(" ")[1])
            return payload.get("user_id")
    except Exception:
        pass
    return None


def get_user_info(request: Request) -> dict:
    try:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            payload = decode_token(auth_header.split(" ")[1])
            return {"user_id": payload.get("user_id"), "username": payload.get("username")}
    except Exception:
        pass
    return {"user_id": None, "username": None}


def get_client_ip(request: Request) -> str:
    client_ip = request.client.host
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    return client_ip


def audit_log(db: Session, request: Request, action: str, category: str, description: str, details: dict = None):
    try:
        user_info = get_user_info(request)
        entry = AuditLog(
            user_id=user_info["user_id"],
            username=user_info["username"],
            action=action,
            category=category,
            description=description,
            details=details,
            ip_address=get_client_ip(request)
        )
        db.add(entry)
        db.commit()
    except Exception as e:
        logger.error(f"Error guardando audit log: {e}")
        try:
            db.rollback()
        except:
            pass


def clean_ip(ip_str):
    if ip_str and '/' in str(ip_str):
        return str(ip_str).split('/')[0]
    return str(ip_str) if ip_str else ip_str


def host_to_dict(host: Host) -> dict:
    return {
        "id": host.id,
        "ip": clean_ip(host.ip),
        "hostname": host.hostname,
        "nickname": host.nickname,
        "mac": host.mac,
        "vendor": host.vendor,
        "os_name": host.os_name,
        "os_accuracy": host.os_accuracy,
        "status": host.status,
        "latency_ms": host.latency_ms,
        "last_seen": host.last_seen.isoformat() if host.last_seen else None,
        "ports": [
            {
                "port": p.port,
                "protocol": p.protocol,
                "service": p.service,
                "state": p.state
            }
            for p in host.ports
        ],
        "services": [
            {
                "port": s.port,
                "service": s.service_name,
                "product": s.product,
                "version": s.version
            }
            for s in host.services
        ],
        "vulnerabilities": [
            {
                "port": v.port,
                "script": v.script_name,
                "severity": v.severity,
                "output": v.output
            }
            for v in host.vulnerabilities
        ]
    }
