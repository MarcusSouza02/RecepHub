from fastapi import APIRouter

from app.api.health import ready_router
from app.api.v1.absences import router as absences_router
from app.api.v1.assistant import router as assistant_router
from app.api.v1.auth import router as auth_router
from app.api.v1.communications import router as communications_router
from app.api.v1.coverage import router as coverage_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.employees import router as employees_router
from app.api.v1.exports import router as exports_router
from app.api.v1.operational_alerts import router as operational_alerts_router
from app.api.v1.schedules import router as schedules_router
from app.api.v1.units import router as units_router
from app.api.v1.work_patterns import router as work_patterns_router

router = APIRouter(prefix="/api/v1")
router.include_router(ready_router)
router.include_router(auth_router)
router.include_router(units_router)
router.include_router(employees_router)
router.include_router(work_patterns_router)
router.include_router(dashboard_router)
router.include_router(schedules_router)
router.include_router(absences_router)
router.include_router(coverage_router)
router.include_router(operational_alerts_router)
router.include_router(communications_router)
router.include_router(exports_router)
router.include_router(assistant_router)
