import fastapi
from sqlalchemy.ext import asyncio as sqlalchemy_asyncio

from app.api import dependencies
from app.crud import auth as auth_crud
from app.schemas import users as user_schemas

router = fastapi.APIRouter()


@router.get("", response_model=user_schemas.HashInfo)
async def get_hash_parameters(
    username: str,
    db: sqlalchemy_asyncio.AsyncSession = fastapi.Depends(dependencies.get_db),
):
    user = await auth_crud.user.get_by_username(db, username)
    if not user:
        raise fastapi.HTTPException(
            fastapi.status.HTTP_404_NOT_FOUND, {"message": "Not Found"}
        )
    alg, cost, salt_and_hash = user.password.split("$")[1:]
    salt = salt_and_hash[:22]
    return {
        "alg": alg,
        "cost": cost,
        "salt": salt,
    }
