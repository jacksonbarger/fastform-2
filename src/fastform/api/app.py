from fastapi import FastAPI

from fastform.settings import settings

from .routes import health

app = FastAPI(title=settings.app_name)
app.include_router(health.router, prefix="/v1")
