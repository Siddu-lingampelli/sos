from fastapi import APIRouter
from .endpoints import auth, locations, cameras, incidents, stream, ws, users, alerts, history

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(locations.router, prefix="/locations", tags=["locations"])
api_router.include_router(cameras.router, prefix="/cameras", tags=["cameras"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(history.router, prefix="/history", tags=["history"])
api_router.include_router(stream.router, prefix="/stream", tags=["stream"])
api_router.include_router(ws.router, prefix="/ws", tags=["stream"])
