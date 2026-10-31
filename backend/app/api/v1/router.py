from fastapi import APIRouter

from app.api.health import ready_router

router = APIRouter(prefix="/api/v1")
router.include_router(ready_router)
