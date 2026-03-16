from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AdminUser
from app.auth import (
    hash_password, verify_password, create_token, decode_token,
    get_current_user, check_rate_limit, record_failed_login,
    clear_login_attempts, require_role, VALID_ROLES, verify_token_version
)
from app.schemas import (
    LoginRequest, ChangePasswordRequest,
    CreateAdminRequest, UpdateAdminRequest
)
from app.utils import audit_log, get_client_ip, logger
from app.websocket_manager import ws_manager

router = APIRouter()



@router.post("/api/auth/login")
async def login(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()

    # Verificar rate limiting
    if check_rate_limit(client_ip, db):
        logger.warning(f"Login bloqueado por rate limit para IP: {client_ip}")
        raise HTTPException(
            status_code=429,
            detail="Demasiados intentos fallidos. Espera 5 minutos antes de intentar de nuevo."
        )

    user = db.query(AdminUser).filter(AdminUser.username == data.username).first()

    if not user or not verify_password(data.password, user.password_hash):
        record_failed_login(client_ip, data.username, db)
        logger.warning(f"Intento de login fallido para: {data.username} desde {client_ip}")
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Cuenta desactivada")

    # Login exitoso - limpiar intentos
    clear_login_attempts(client_ip, db)
    token = create_token(user.id, user.username, user.role or "viewer", user.token_version or 0)
    logger.info(f"Login exitoso: {user.username} (rol: {user.role}) desde {client_ip}")

    audit_log(db, request, "login", "auth", f"Inicio de sesión: {user.username}", {"user_id": user.id, "role": user.role})

    return {
        "token": token,
        "must_change_password": bool(user.must_change_password),
        "user": {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name or user.username,
            "role": user.role or "viewer",
            "is_super_admin": user.is_super_admin or False
        }
    }


@router.get("/api/auth/check")
async def check_auth(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return {"authenticated": False}

    try:
        token = auth_header.split(" ")[1]
        payload = decode_token(token)
        db = next(get_db())
        try:
            user = db.query(AdminUser).filter(AdminUser.id == payload["user_id"]).first()
            if user and user.is_active and verify_token_version(payload, db):
                return {
                    "authenticated": True,
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "display_name": user.display_name or user.username,
                        "role": user.role or "viewer",
                        "is_super_admin": user.is_super_admin or False
                    }
                }
        finally:
            db.close()
    except Exception:
        pass

    return {"authenticated": False}


@router.get("/api/auth/me")
async def get_me(request: Request, db: Session = Depends(get_db)):
    user_data = get_current_user(request)
    user = db.query(AdminUser).filter(AdminUser.id == user_data["user_id"]).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name or user.username,
        "role": user.role or "viewer",
        "is_super_admin": user.is_super_admin or False,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }


@router.post("/api/auth/refresh")
async def refresh_token(request: Request, db: Session = Depends(get_db)):
    user_data = get_current_user(request)
    user = db.query(AdminUser).filter(AdminUser.id == user_data["user_id"]).first()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Usuario no válido")

    new_token = create_token(user.id, user.username, user.role or "viewer", user.token_version or 0)
    return {
        "token": new_token,
        "user": {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name or user.username,
            "role": user.role or "viewer",
            "is_super_admin": user.is_super_admin or False
        }
    }


@router.put("/api/auth/change-password")
async def change_password(data: ChangePasswordRequest, request: Request, db: Session = Depends(get_db)):
    user_data = get_current_user(request)
    user = db.query(AdminUser).filter(AdminUser.id == user_data["user_id"]).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")

    user.password_hash = hash_password(data.new_password)
    user.must_change_password = False
    # Incrementar token_version para invalidar todos los tokens anteriores
    user.token_version = (user.token_version or 0) + 1
    db.commit()

    # Generar nuevo token con la nueva versión
    new_token = create_token(user.id, user.username, user.role or "viewer", user.token_version)

    audit_log(db, request, "update", "auth", f"Contraseña cambiada para: {user.username}", {"target_user_id": user.id})
    logger.info(f"Contraseña cambiada para: {user.username}")
    return {
        "message": "Contraseña actualizada correctamente",
        "token": new_token,
        "user": {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name or user.username,
            "role": user.role or "viewer",
            "is_super_admin": user.is_super_admin or False
        }
    }



@router.get("/api/admin/users")
async def list_admin_users(request: Request, db: Session = Depends(get_db), _role=Depends(require_role("admin"))):
    users = db.query(AdminUser).order_by(AdminUser.created_at.asc()).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "display_name": u.display_name or u.username,
            "is_active": u.is_active,
            "role": u.role or "viewer",
            "is_super_admin": u.is_super_admin or False,
            "created_at": u.created_at.isoformat() if u.created_at else None
        }
        for u in users
    ]


@router.post("/api/admin/users")
async def create_admin_user(data: CreateAdminRequest, request: Request, db: Session = Depends(get_db), _role=Depends(require_role("admin"))):
    current_user = get_current_user(request)
    requesting_user = db.query(AdminUser).filter(AdminUser.id == current_user["user_id"]).first()
    if not requesting_user or not requesting_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Solo el administrador principal puede crear usuarios")

    existing = db.query(AdminUser).filter(AdminUser.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"El usuario '{data.username}' ya existe")

    if data.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"Rol inválido. Roles válidos: {', '.join(VALID_ROLES)}")

    new_user = AdminUser(
        username=data.username,
        password_hash=hash_password(data.password),
        display_name=data.display_name or data.username,
        role=data.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    current_user = get_current_user(request)
    audit_log(db, request, "create", "admin", f"Admin '{data.username}' creado por '{current_user['username']}'", {"new_user_id": new_user.id, "new_username": data.username})
    logger.info(f"Admin '{data.username}' creado por '{current_user['username']}'")

    return {
        "id": new_user.id,
        "username": new_user.username,
        "display_name": new_user.display_name,
        "message": f"Administrador '{data.username}' creado correctamente"
    }


@router.put("/api/admin/users/{user_id}")
async def update_admin_user(user_id: int, data: UpdateAdminRequest, request: Request, db: Session = Depends(get_db), _role=Depends(require_role("admin"))):
    user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    current_user = get_current_user(request)
    requesting_user = db.query(AdminUser).filter(AdminUser.id == current_user["user_id"]).first()
    previous_role = user.role or "viewer"
    role_changed = False
    deactivated = False

    
    if user.is_super_admin and (not requesting_user or not requesting_user.is_super_admin):
        raise HTTPException(status_code=403, detail="No puedes modificar al administrador principal")

    if data.display_name is not None:
        user.display_name = data.display_name

    if data.is_active is not None:
        if user.id == current_user["user_id"] and not data.is_active:
            raise HTTPException(status_code=400, detail="No puedes desactivar tu propia cuenta")

        if not data.is_active:
            active_count = db.query(AdminUser).filter(AdminUser.is_active == True, AdminUser.id != user_id).count()
            if active_count == 0:
                raise HTTPException(status_code=400, detail="Debe haber al menos un administrador activo")

        user.is_active = data.is_active
        deactivated = data.is_active is False

    if data.new_password:
        user.password_hash = hash_password(data.new_password)
        # Invalidar tokens anteriores del usuario
        user.token_version = (user.token_version or 0) + 1

    if data.role is not None:
        if data.role not in VALID_ROLES:
            raise HTTPException(status_code=400, detail=f"Rol inválido. Roles válidos: {', '.join(VALID_ROLES)}")
        if user.id == current_user["user_id"] and data.role != "admin":
            raise HTTPException(status_code=400, detail="No puedes cambiar tu propio rol")
        role_changed = (previous_role != data.role)
        user.role = data.role

    db.commit()

    if role_changed:
        await ws_manager.send_to_user(
            user.id,
            "auth_permissions_updated",
            {
                "user_id": user.id,
                "role": user.role or "viewer"
            }
        )

    if deactivated:
        await ws_manager.send_to_user(
            user.id,
            "auth_force_logout",
            {
                "reason": "Tu cuenta fue desactivada por un administrador."
            }
        )

    changes = {}
    if data.display_name is not None:
        changes["display_name"] = data.display_name
    if data.is_active is not None:
        changes["is_active"] = data.is_active
    if data.new_password:
        changes["password_changed"] = True
    if data.role is not None:
        changes["role"] = data.role
    audit_log(db, request, "update", "admin", f"Admin '{user.username}' actualizado por '{current_user['username']}'", {"target_user_id": user_id, "changes": changes})
    logger.info(f"Admin '{user.username}' actualizado por '{current_user['username']}'")
    return {"message": f"Administrador '{user.username}' actualizado correctamente"}


@router.delete("/api/admin/users/{user_id}")
async def delete_admin_user(user_id: int, request: Request, db: Session = Depends(get_db), _role=Depends(require_role("admin"))):
    user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    current_user = get_current_user(request)

    requesting_user = db.query(AdminUser).filter(AdminUser.id == current_user["user_id"]).first()
    if not requesting_user or not requesting_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Solo el administrador principal puede eliminar usuarios")

    if user.id == current_user["user_id"]:
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propia cuenta")

    if user.is_super_admin:
        raise HTTPException(status_code=400, detail="No se puede eliminar al administrador principal del sistema")

    total_admins = db.query(AdminUser).count()
    if total_admins <= 1:
        raise HTTPException(status_code=400, detail="Debe haber al menos un administrador")

    username = user.username
    target_user_id = user.id
    audit_log(db, request, "delete", "admin", f"Admin '{username}' eliminado por '{current_user['username']}'", {"deleted_user_id": user_id, "deleted_username": username})
    db.delete(user)
    db.commit()

    await ws_manager.send_to_user(
        target_user_id,
        "auth_force_logout",
        {
            "reason": "Tu cuenta fue eliminada por un administrador."
        }
    )

    logger.info(f"Admin '{username}' eliminado por '{current_user['username']}'")
    return {"message": f"Administrador '{username}' eliminado correctamente"}
