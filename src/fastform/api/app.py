from fastapi import FastAPI

from fastform.settings import settings

from .routes.ai_drugs import router as ai_drugs_router
from .routes.drugs import router as drugs_router
from .routes.formularies import router as formularies_router
from .routes.health import router as health_router

app = FastAPI(title=settings.app_name)
app.include_router(health_router, prefix="/v1")
app.include_router(drugs_router, prefix="/v1/drugs", tags=["drugs"])
app.include_router(ai_drugs_router, prefix="/v1/drugs", tags=["ai-drugs"])
app.include_router(formularies_router, prefix="/v1/formularies", tags=["formularies"])
