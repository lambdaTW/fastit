import fastapi
from sqlalchemy import func as sqlalchemy_func
from sqlalchemy import future as sqlalchemy_future
from sqlalchemy.ext import asyncio as sqlalchemy_asyncio

from app.api import dependencies
from app.models import auth as auth_models
from app.schemas import users as user_schemas

router = fastapi.APIRouter()


@router.get("", response_model=user_schemas.HashInfo)
async def get_hash_parameters(
    username: str,
    db: sqlalchemy_asyncio.AsyncSession = fastapi.Depends(dependencies.get_db),
):
    user = (
        (
            await db.execute(
                sqlalchemy_future.select(auth_models.User).filter(
                    sqlalchemy_func.lower(auth_models.User.username)
                    == sqlalchemy_func.lower(username)
                )
            )
        )
        .scalars()
        .first()
    )
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
