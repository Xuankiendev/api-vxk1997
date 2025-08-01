from fastapi import APIRouter, Form, HTTPException
from src.db import getConn
from src.utils import hashPassword, checkPassword, generateKey

router = APIRouter()

@router.post("/signup")
def signup(email: str = Form(...), password: str = Form(...)):
    conn = getConn()
    if conn.execute("select 1 from users where email = %s", [email]).fetchone():
        raise HTTPException(statusCode=400, detail="exists")
    key = generateKey()
    conn.execute("insert into users (email, password, apiKey) values (%s,%s,%s)",
                 [email, hashPassword(password), key])
    conn.commit()
    conn.close()
    return {"apiKey": key}

@router.post("/login")
def login(email: str = Form(...), password: str = Form(...)):
    conn = getConn()
    user = conn.execute("select password, apiKey from users where email = %s", [email]).fetchone()
    conn.close()
    if not user or not checkPassword(password, user["password"]):
        raise HTTPException(statusCode=401, detail="invalid")
    return {"apiKey": user["apiKey"]}
