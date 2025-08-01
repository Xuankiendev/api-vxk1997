from fastapi import APIRouter, Query, HTTPException
from src.db import getConn

router = APIRouter()

@router.get("/echo")
def echo(msg: str = Query(...), apikey: str = Query(...)):
    conn = getConn()
    user = conn.execute("select 1 from users where apiKey = %s", [apikey]).fetchone()
    conn.close()
    if not user:
        raise HTTPException(statusCode=401, detail="unauthorized")
    return {"message": msg}
