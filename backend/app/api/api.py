from fastapi import APIRouter
from .endpoints import auth, locations, cameras, incidents, stream

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(locations.router, prefix="/locations", tags=["locations"])
api_router.include_router(cameras.router, prefix="/cameras", tags=["cameras"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
api_router.include_router(stream.router, prefix="/stream", tags=["stream"])
