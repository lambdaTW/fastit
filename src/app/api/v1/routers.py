import fastapi

from app.api.v1.endpoints.auth.users import hashes as hashes_endpoints
from app.api.v1.endpoints.auth.users import tokens as token_endpoints

v1_router = fastapi.APIRouter()
v1_router.include_router(token_endpoints.router, prefix="/auth/users/tokens")
v1_router.include_router(hashes_endpoints.router, prefix="/auth/users/hashes")
