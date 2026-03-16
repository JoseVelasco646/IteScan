import os
import logging
import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db

_logger = logging.getLogger("app")

_jwt_secret_env = os.getenv("JWT_SECRET")
if not _jwt_secret_env:
    import secrets
    _jwt_secret_env = secrets.token_hex(32)

    _env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    _written = False
    try:
        with open(_env_path, 'a', encoding='utf-8') as f:
            f.write(f"\nJWT_SECRET={_jwt_secret_env}\n")
        _written = True
    except Exception:
        pass

    if _written:
        _logger.warning(
            "JWT_SECRET no estaba definido. Se generó uno nuevo y se guardó en .env. "
            "Configúralo como variable de entorno para evitar invalidar tokens al reiniciar."
        )
    else:
        _logger.critical(
            "JWT_SECRET no está definido y no se pudo escribir en .env. "
            "Todos los tokens se invalidarán al reiniciar el servidor. "
            "Define JWT_SECRET como variable de entorno."
        )

JWT_SECRET = _jwt_secret_env
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))


MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 300


def check_rate_limit(client_ip: str, db: Session = None) -> bool:
    if db is None:
        db = next(get_db())
    from app.models import LoginAttempt
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=LOGIN_LOCKOUT_SECONDS)
    count = db.query(LoginAttempt).filter(
        LoginAttempt.ip_address == client_ip,
        LoginAttempt.attempted_at >= cutoff
    ).count()
    return count >= MAX_LOGIN_ATTEMPTS


def record_failed_login(client_ip: str, username: str = None, db: Session = None):
    if db is None:
        db = next(get_db())
    from app.models import LoginAttempt
    attempt = LoginAttempt(ip_address=client_ip, username=username)
    db.add(attempt)
    db.commit()


def clear_login_attempts(client_ip: str, db: Session = None):
    if db is None:
        db = next(get_db())
    from app.models import LoginAttempt
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=LOGIN_LOCKOUT_SECONDS)
    db.query(LoginAttempt).filter(
        LoginAttempt.ip_address == client_ip,
        LoginAttempt.attempted_at >= cutoff
    ).delete(synchronize_session='fetch')
    db.commit()


def cleanup_old_login_attempts(db: Session):
    from app.models import LoginAttempt
    cutoff = datetime.now(timezone.utc) - timedelta(days=1)
    db.query(LoginAttempt).filter(
        LoginAttempt.attempted_at < cutoff
    ).delete(synchronize_session='fetch')
    db.commit()


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def create_token(user_id: int, username: str, role: str = "viewer", token_version: int = 0) -> str:
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "token_version": token_version,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")


def verify_token_version(payload: dict, db: Session) -> bool:
    from app.models import AdminUser
    user = db.query(AdminUser).filter(AdminUser.id == payload.get("user_id")).first()
    if not user:
        return False
    # Tokens sin token_version (legacy) se consideran inválidos
    token_ver = payload.get("token_version", -1)
    return token_ver == (user.token_version or 0)


def get_token_from_request(request: Request) -> str:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No autenticado")
    return auth_header.split(" ")[1]


def get_current_user(request: Request) -> dict:
    token = get_token_from_request(request)
    return decode_token(token)


def create_default_admin(db: Session):
    from app.models import AdminUser
    
    admin_count = db.query(AdminUser).count()
    if admin_count == 0:
        default_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin")
        default_user = AdminUser(
            username="admin",
            password_hash=hash_password(default_password),
            display_name="Administrador",
            role="admin",
            is_super_admin=True,
            must_change_password=True,
            token_version=0
        )
        db.add(default_user)
        db.commit()
        return True
    return False



ROLE_HIERARCHY = {
    "admin": 4,
    "mod": 3,
    "op": 2,
    "viewer": 1,
}

VALID_ROLES = list(ROLE_HIERARCHY.keys())


def get_user_role(request: Request) -> str:
    try:
        token = get_token_from_request(request)
        payload = decode_token(token)
        return payload.get("role", "viewer")
    except Exception:
        return "viewer"


def require_role(minimum_role: str):
    min_level = ROLE_HIERARCHY.get(minimum_role, 0)

    def checker(request: Request, db: Session = Depends(get_db)):
        user_data = get_current_user(request)
        from app.models import AdminUser

        user = db.query(AdminUser).filter(AdminUser.id == user_data.get("user_id")).first()
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="Usuario no válido o desactivado")

        user_role = user.role or "viewer"
        user_level = ROLE_HIERARCHY.get(user_role, 0)

        if user_level < min_level:
            raise HTTPException(
                status_code=403,
                detail=f"Permiso insuficiente. Se requiere rol '{minimum_role}' o superior. Tu rol: '{user_role}'"
            )
        return user_data
    
    return checker
