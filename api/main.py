from fastapi import Depends, FastAPI
from api.auth import require_api_key
from api.routes.health import router as health_router
from api.routes.competitors import router as competitors_router
from api.routes.changes import router as changes_router
from api.routes.onboarding import router as onboarding_router
from api.routes.ai import router as ai_router
from api.routes.jobs import router as jobs_router
from api.routes.businesses import router as businesses_router
from api.routes.intent import router as intent_router
from api.routes.research import router as research_router
from api.routes.measurements import router as measurements_router
from api.routes.qa import router as qa_router
from api.routes.signals import router as signals_router

app=FastAPI(title="Rivalry",version="0.2.1")
app.include_router(health_router)
for router in [competitors_router,changes_router,onboarding_router,ai_router,jobs_router,businesses_router,intent_router,research_router,measurements_router,qa_router,signals_router]:
    app.include_router(router,prefix="/api/v1",dependencies=[Depends(require_api_key)])
