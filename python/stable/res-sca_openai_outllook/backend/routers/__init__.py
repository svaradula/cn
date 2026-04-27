from fastapi import APIRouter

router = APIRouter()

# Import route modules here
# from .users import router as users_router
# from .items import router as items_router

# Include routers
# router.include_router(users_router, prefix="/users", tags=["users"])
# router.include_router(items_router, prefix="/items", tags=["items"])

__all__ = ["router"]