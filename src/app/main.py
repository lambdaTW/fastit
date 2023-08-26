import fastapi

from app.api.v1 import routers as v1_routers
from app.models import health_check

app = fastapi.FastAPI()
app.include_router(v1_routers.v1_router, prefix="/v1")


@app.get("/", response_model=health_check.HealthResponse)
async def root():
    return {"api": "fastit"}
