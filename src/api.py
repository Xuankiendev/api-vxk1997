import importlib
import json
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from .db import getDb

router = APIRouter(prefix="/api")

with open("assets/apis.json") as f:
    apis = json.load(f)

@router.get("/{apiName}")
async def handleApi(apiName: str, request: Request, db: Session = Depends(getDb)):
    if apiName not in apis:
        raise HTTPException(404, detail="API not found")

    try:
        module = importlib.import_module(f"src.api.{apiName}")
        if not hasattr(module, "run"):
            raise HTTPException(500, detail="Missing run() in API module")

        queryParams = dict(request.query_params)
        result = await module.run(queryParams, db)
        return {"success": True, "data": result}

    except Exception as e:
        raise HTTPException(500, detail=str(e))
