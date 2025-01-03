from fastapi import APIRouter

from app.api.routes import actor, address, auth, movie

api_router = APIRouter()
api_router.include_router(actor.router, prefix="/actors", tags=["actors"])
api_router.include_router(address.router, prefix="/addresses", tags=["addresses"])
api_router.include_router(movie.router, prefix="/movies", tags=["movies"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
