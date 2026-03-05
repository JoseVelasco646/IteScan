import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, Body, Request, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List

from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models import AdminUser, SSHCredential
from app import crud
from app.auth import require_role, decode_token
from app.ssh_operations import shutdown_host_ssh, shutdown_ip_range, execute_command_ssh, reboot_host_ssh, test_ssh_connection
from app.ssh_terminal_manager import ssh_manager
from app.schemas import SSHShutdownRequest, SSHRangeShutdownRequest
from app.utils import audit_log, get_user_info, logger

router = APIRouter()


# schemas for SSH credentials management

class SSHCredentialCreate(BaseModel):
    name: str
    username: str
    password: str


class SSHCredentialUpdate(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


# ssh credentials management endpoints

@router.get("/ssh/credentials")
async def list_ssh_credentials(db: Session = Depends(get_db), _role=Depends(require_role("op"))):
    creds = db.query(SSHCredential).order_by(SSHCredential.name).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "username": c.username,
            "created_by": c.created_by,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in creds
    ]


@router.get("/ssh/credentials/{cred_id}")
async def get_ssh_credential(cred_id: int, db: Session = Depends(get_db), _role=Depends(require_role("op"))):
    cred = db.query(SSHCredential).filter(SSHCredential.id == cred_id).first()
    if not cred:
        raise HTTPException(status_code=404, detail="Credencial no encontrada")
    return {
        "id": cred.id,
        "name": cred.name,
        "username": cred.username,
        "password": cred.password,
        "created_by": cred.created_by,
    }


@router.post("/ssh/credentials")
async def create_ssh_credential(data: SSHCredentialCreate, request: Request, db: Session = Depends(get_db), _role=Depends(require_role("op"))):
    user_info = get_user_info(request)
    cred = SSHCredential(
        name=data.name,
        username=data.username,
        created_by=user_info.get("username"),
    )
    cred.password = data.password
    db.add(cred)
    db.commit()
    db.refresh(cred)
    audit_log(db, request, "create", "ssh", f"Credencial SSH creada: {data.name}", {"name": data.name, "username": data.username})
    return {"id": cred.id, "name": cred.name, "username": cred.username, "message": "Credencial guardada"}


@router.put("/ssh/credentials/{cred_id}")
async def update_ssh_credential(cred_id: int, data: SSHCredentialUpdate, request: Request, db: Session = Depends(get_db), _role=Depends(require_role("op"))):
    cred = db.query(SSHCredential).filter(SSHCredential.id == cred_id).first()
    if not cred:
        raise HTTPException(status_code=404, detail="Credencial no encontrada")
    if data.name is not None:
        cred.name = data.name
    if data.username is not None:
        cred.username = data.username
    if data.password is not None:
        cred.password = data.password
    db.commit()
    audit_log(db, request, "update", "ssh", f"Credencial SSH actualizada: {cred.name}", {"id": cred_id})
    return {"message": "Credencial actualizada"}


@router.delete("/ssh/credentials/{cred_id}")
async def delete_ssh_credential(cred_id: int, request: Request, db: Session = Depends(get_db), _role=Depends(require_role("op"))):
    cred = db.query(SSHCredential).filter(SSHCredential.id == cred_id).first()
    if not cred:
        raise HTTPException(status_code=404, detail="Credencial no encontrada")
    name = cred.name
    db.delete(cred)
    db.commit()
    audit_log(db, request, "delete", "ssh", f"Credencial SSH eliminada: {name}", {"id": cred_id, "name": name})
    return {"message": "Credencial eliminada"}


# SSH operations endpoints

@router.post("/ssh/shutdown")
async def shutdown_host(data: SSHShutdownRequest, request: Request, db: Session = Depends(get_db), _role=Depends(require_role("op"))):
    audit_log(db, request, "scan", "ssh", f"SSH shutdown: {data.host}", {"host": data.host, "username": data.username})
    result = await shutdown_host_ssh(
        data.host,
        data.username,
        data.password,
        data.key_file
    )
    if result.get("success"):
        crud.mark_host_as_down(db, data.host)
    return result


@router.post("/ssh/shutdown/range")
async def shutdown_range(data: SSHRangeShutdownRequest, db: Session = Depends(get_db), _role=Depends(require_role("op"))):
    results = await shutdown_ip_range(
        data.start_ip,
        data.end_ip,
        data.username,
        data.password,
        data.key_file
    )
    successful_hosts = [r["host"] for r in results if r.get("success")]
    if successful_hosts:
        crud.mark_multiple_hosts_as_down(db, successful_hosts)
    return {"results": results}


@router.post("/ssh/test")
async def test_ssh(data: SSHShutdownRequest, _role=Depends(require_role("op"))):
    result = await asyncio.to_thread(
        test_ssh_connection,
        data.host,
        data.username,
        data.password,
        data.key_file
    )
    return result


@router.post("/ssh/reboot")
async def reboot_host(data: SSHShutdownRequest, request: Request, db: Session = Depends(get_db), _role=Depends(require_role("op"))):
    audit_log(db, request, "scan", "ssh", f"SSH reboot: {data.host}", {"host": data.host, "username": data.username})
    result = await reboot_host_ssh(
        data.host,
        data.username,
        data.password,
        data.key_file
    )
    return result


@router.post("/ssh/execute")
async def execute_ssh_command(
    request: Request,
    host: str = Body(...),
    command: str = Body(...),
    username: str = Body(...),
    password: str = Body(...),
    db: Session = Depends(get_db),
    _role=Depends(require_role("op"))
):
    audit_log(db, request, "scan", "ssh", f"SSH comando en {host}: {command[:100]}", {"host": host, "command": command, "username": username})
    result = await execute_command_ssh(host, command, username, password)
    return result


@router.post("/ssh/execute/multiple")
async def execute_ssh_command_multiple(
    request: Request,
    hosts: List[str] = Body(...),
    command: str = Body(...),
    username: str = Body(...),
    password: str = Body(...),
    db: Session = Depends(get_db),
    _role=Depends(require_role("op"))
):
    audit_log(db, request, "scan", "ssh", f"SSH comando múltiple en {len(hosts)} hosts: {command[:100]}", {"hosts": hosts, "command": command, "username": username})
    tasks = [execute_command_ssh(host, command, username, password) for host in hosts]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    formatted_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            formatted_results.append({
                "host": hosts[i],
                "success": False,
                "error": str(result)
            })
        else:
            formatted_results.append({
                "host": hosts[i],
                **result
            })
    # 
    return {"results": formatted_results}


# WebSocket endpoint for SSH terminal sessions

@router.websocket("/ws/ssh/{session_id}")
async def ssh_terminal_websocket(websocket: WebSocket, session_id: str):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Token requerido")
        return

    user_id = None
    username_audit = None
    try:
        payload = decode_token(token)
        user_id = payload.get("user_id")
        username_audit = payload.get("username")
        db = next(get_db())
        try:
            user = db.query(AdminUser).filter(AdminUser.id == payload["user_id"]).first()
            if not user or not user.is_active:
                await websocket.close(code=4001, reason="No autorizado")
                return
        finally:
            db.close()
    except Exception:
        await websocket.close(code=4001, reason="Token inválido")
        return

    await websocket.accept()
    
    session = None
    read_task = None
    ssh_host = None
    ssh_username = None

    try:
        initial_data = await websocket.receive_text()
        initial_msg = json.loads(initial_data)

        if initial_msg.get("type") != "connect":
            await websocket.send_json({"type": "error", "message": "Expected connect message"})
            await websocket.close()
            return

        ssh_host = initial_msg.get("host")
        ssh_username = initial_msg.get("username")
        password = initial_msg.get("password")
        port = initial_msg.get("port", 22)
        cols = initial_msg.get("cols", 120)
        rows = initial_msg.get("rows", 30)

        if not all([ssh_host, ssh_username, password]):
            await websocket.send_json({"type": "error", "message": "Credenciales faltantes"})
            await websocket.close()
            return

        ok = ssh_manager.create_session(session_id, ssh_host, ssh_username, password, port, cols, rows)
        if not ok:
            _audit_ssh(user_id, username_audit, "ssh_connect_failed", ssh_host, ssh_username, session_id)
            await websocket.send_json({"type": "error", "message": "Error al conectar con el servidor SSH"})
            await websocket.close()
            return

        session = ssh_manager.get_session(session_id)
        await websocket.send_json({"type": "connected", "message": f"Connected to {ssh_host}"})

        
        _audit_ssh(user_id, username_audit, "ssh_connect", ssh_host, ssh_username, session_id)

        
        async def reader_loop():
            while session and session.is_alive():
                try:
                    data = await asyncio.to_thread(session.read)
                    if data:
                        await websocket.send_bytes(data)
                    else:
                        await asyncio.sleep(0.02)  
                except Exception:
                    break

          
            try:
                await websocket.send_json({"type": "disconnected", "message": "SSH session ended"})
            except Exception:
                pass

        read_task = asyncio.create_task(reader_loop())

        
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            msg_type = msg.get("type")

            if msg_type == "input":
                input_data = msg.get("data", "")
                if input_data:
                    await asyncio.to_thread(session.write, input_data.encode("utf-8", errors="ignore"))

            elif msg_type == "resize":
                c = msg.get("cols", 120)
                r = msg.get("rows", 30)
                session.resize(c, r)

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            elif msg_type == "close":
                break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        if read_task:
            read_task.cancel()
            try:
                await read_task
            except asyncio.CancelledError:
                pass
        ssh_manager.close_session(session_id)
        if ssh_host:
            _audit_ssh(user_id, username_audit, "ssh_disconnect", ssh_host, ssh_username, session_id)
        try:
            await websocket.close()
        except Exception:
            pass


def _audit_ssh(user_id, username, action, ssh_host, ssh_user, session_id):
    from app.models import AuditLog
    try:
        db = next(get_db())
        descriptions = {
            "ssh_connect": f"Terminal SSH conectada a {ssh_host} como {ssh_user}",
            "ssh_connect_failed": f"Fallo al conectar terminal SSH a {ssh_host} como {ssh_user}",
            "ssh_disconnect": f"Terminal SSH desconectada de {ssh_host}",
        }
        entry = AuditLog(
            user_id=user_id,
            username=username,
            action=action,
            category="ssh",
            description=descriptions.get(action, action),
            details={"host": ssh_host, "ssh_user": ssh_user, "session_id": session_id},
            ip_address=None,
        )
        db.add(entry)
        db.commit()
        db.close()
    except Exception as e:
        logger.error(f"Error guardando audit SSH: {e}")
