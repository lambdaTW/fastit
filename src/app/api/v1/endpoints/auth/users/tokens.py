import fastapi

router = fastapi.APIRouter()


@router.post("")
def create_jtw_token():
    return {"access_token": "access_token", "refresh_token": "refresh_token"}