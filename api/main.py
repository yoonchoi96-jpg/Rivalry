from fastapi import FastAPI
from api.routes.health import router as health_router
from api.routes.competitors import router as competitors_router
from api.routes.changes import router as changes_router
app=FastAPI(title="Rivalry",version="0.1.0")
app.include_router(health_router)
app.include_router(competitors_router,prefix="/api/v1")
app.include_router(changes_router,prefix="/api/v1")
