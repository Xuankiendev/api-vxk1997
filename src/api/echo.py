from sqlalchemy.orm import Session
from ..auth import validateApiKey
from ..db import getDb

async def run(params: dict, db: Session):
    await validateApiKey(params["apiKey"], db)
    return {"message": params["msg"]}
