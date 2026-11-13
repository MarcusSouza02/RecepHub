from fastapi import APIRouter

from app.api.health import ready_router
from app.api.v1.auth import router as auth_router
from app.api.v1.employees import router as employees_router
from app.api.v1.units import router as units_router

router = APIRouter(prefix="/api/v1")
router.include_router(ready_router)
router.include_router(auth_router)
router.include_router(units_router)
router.include_router(employees_router)
