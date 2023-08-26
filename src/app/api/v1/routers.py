import fastapi

from app.api.v1.endpoints.auth.users import tokens as token_endpoints

v1_router = fastapi.APIRouter()
v1_router.include_router(token_endpoints.router, prefix="/auth/users/tokens")
