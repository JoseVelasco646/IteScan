

import asyncio
import json
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import get_db, create_tables
from app.models import AdminUser
from app.auth import decode_token, create_default_admin
from app.websocket_manager import ws_manager
from app.scheduler_service import scheduler_service
from app.utils import logger


from app.routers.auth import router as auth_router
from app.routers.scan import router as scan_router
from app.routers.hosts import router as hosts_router
from app.routers.ssh import router as ssh_router
from app.routers.audit import router as audit_router
from app.schedule_routes import router as schedule_router
from app.routers.subnets import router as subnets_router



PUBLIC_PATHS = [
    "/api/auth/login",
    "/api/auth/check",
    "/health",
    "/",
    "/docs",
    "/openapi.json",
]



@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    db = next(get_db())
    try:
        created = create_default_admin(db)
        if created:
            logger.info("Usuario admin por defecto creado (usuario: admin, contraseña: admin)")
    finally:
        db.close()
    asyncio.create_task(scheduler_service.start())
    yield
    scheduler_service.stop()



app = FastAPI(
    title="Network Scanner API",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan,
)



@app.middleware("http")
async def verify_auth(request: Request, call_next):
    path = request.url.path

    if any(path.startswith(p) for p in PUBLIC_PATHS):
        return await call_next(request)

    if path.startswith("/ws"):
        return await call_next(request)

    if request.method == "OPTIONS":
        return await call_next(request)

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"detail": "No autenticado. Inicia sesión para continuar."},
        )

    try:
        token = auth_header.split(" ")[1]
        payload = decode_token(token)
        db = next(get_db())
        try:
            user = db.query(AdminUser).filter(AdminUser.id == payload["user_id"]).first()
            if not user or not user.is_active:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Usuario no válido o desactivado."},
                )
            request.state.user_id = payload["user_id"]
        finally:
            db.close()
    except Exception:
        return JSONResponse(
            status_code=401,
            content={"detail": "Token inválido o expirado. Inicia sesión nuevamente."},
        )

    return await call_next(request)



CORS_DEFAULT = os.getenv(
    "CORS_ORIGINS",
    "http://192.168.0.11:3000,http://localhost:3000,http://127.0.0.1:3000",
)
ALLOWED_ORIGINS = [o.strip() for o in CORS_DEFAULT.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Token requerido")
        return

    user_id = None
    try:
        payload = decode_token(token)
        user_id = payload["user_id"]
        db = next(get_db())
        try:
            user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
            if not user or not user.is_active:
                await websocket.close(code=4001, reason="No autorizado")
                return
        finally:
            db.close()
    except Exception:
        await websocket.close(code=4001, reason="Token inválido")
        return

    await ws_manager.connect(websocket, user_id=user_id)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
            else:
                try:
                    message = json.loads(data)
                    if message.get("type") == "cancel_scan":
                        scan_id = message.get("scan_id")
                        if scan_id:
                            ws_manager.cancel_scan(scan_id)
                            await websocket.send_text(
                                json.dumps({"type": "scan_cancelled", "scan_id": scan_id})
                            )
                            await ws_manager.broadcast(
                                "scan_progress",
                                {
                                    "scan_id": scan_id,
                                    "status": "cancelled",
                                    "message": "Escaneo cancelado por el usuario",
                                },
                            )
                except json.JSONDecodeError:
                    pass
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception:
        await ws_manager.disconnect(websocket)


@app.get("/")
async def root():
    return {
        "message": "Network Scanner API",
        "version": "2.1",
        "features": [
            "Descubrimiento de hosts",
            "Escaneo de puertos",
            "Detección de servicios",
            "Detección de sistema operativo",
            "Escaneo de vulnerabilidades",
            "Almacenamiento en base de datos",
            "Apagado remoto SSH",
            "Exportación de datos (CSV)",
            "Registro de auditoría",
            "Control de acceso basado en roles",
            "Actualización de token",
        ],
    }



app.include_router(auth_router)
app.include_router(scan_router)
app.include_router(hosts_router)
app.include_router(ssh_router)
app.include_router(audit_router)
app.include_router(schedule_router)
app.include_router(subnets_router)
