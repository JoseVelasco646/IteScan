import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db


_jwt_secret_env = os.getenv("JWT_SECRET")
if not _jwt_secret_env:
    import secrets
    _jwt_secret_env = secrets.token_hex(32)
   
    _env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    try:
        with open(_env_path, 'a', encoding='utf-8') as f:
            f.write(f"\nJWT_SECRET={_jwt_secret_env}\n")
    except Exception:
        pass  

JWT_SECRET = _jwt_secret_env
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))


LOGIN_ATTEMPTS = {}  
MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 300  

def check_rate_limit(client_ip: str) -> bool:
    import time
    now = time.time()
    attempts = LOGIN_ATTEMPTS.get(client_ip, [])
    # Limpiar intentos viejos
    attempts = [a for a in attempts if now - a < LOGIN_LOCKOUT_SECONDS]
    LOGIN_ATTEMPTS[client_ip] = attempts
    return len(attempts) >= MAX_LOGIN_ATTEMPTS

def record_failed_login(client_ip: str):
    import time
    if client_ip not in LOGIN_ATTEMPTS:
        LOGIN_ATTEMPTS[client_ip] = []
    LOGIN_ATTEMPTS[client_ip].append(time.time())

def clear_login_attempts(client_ip: str):
    LOGIN_ATTEMPTS.pop(client_ip, None)


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def create_token(user_id: int, username: str, role: str = "viewer") -> str:
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow()
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
            must_change_password=True
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
    
    def checker(request: Request):
        user_data = get_current_user(request)
        user_role = user_data.get("role", "viewer")
        user_level = ROLE_HIERARCHY.get(user_role, 0)
        
        if user_level < min_level:
            raise HTTPException(
                status_code=403,
                detail=f"Permiso insuficiente. Se requiere rol '{minimum_role}' o superior. Tu rol: '{user_role}'"
            )
        return user_data
    
    return checker
