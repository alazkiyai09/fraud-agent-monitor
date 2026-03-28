from app.routers.agents import router as agents_router
from app.routers.health import router as health_router
from app.routers.monitor import router as monitor_router

__all__ = ["agents_router", "health_router", "monitor_router"]
