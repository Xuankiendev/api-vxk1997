from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..auth import validateApiKey
from ..db import getDb

router = APIRouter(prefix="/api")

@router.get("/echo")
async def echo(msg: str, apiKey: str, db: Session = Depends(getDb)):
    await validateApiKey(apiKey, db)
    return {"message": msg}
