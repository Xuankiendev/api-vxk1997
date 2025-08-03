from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
from . import db, utils
from .db import User, Verification

router = APIRouter()

@router.post("/requestVerification")
async def requestVerification(email: str = Form(...), db: Session = Depends(db.getDb)):
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return JSONResponse(status_code=400, content={"success": False, "error": "Email already exists"})

    code = utils.generateVerificationCode()
    expiresAt = utils.oneMinuteLater()

    db.query(Verification).filter(Verification.email == email).delete()
    db.add(Verification(email=email, code=code, expiresAt=expiresAt))
    db.commit()

    try:
        utils.sendVerificationEmail(email, code)
        return JSONResponse(content={"success": True, "message": "Verification code sent"})
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

@router.post("/signup")
async def signup(
    email: str = Form(...),
    password: str = Form(...),
    confirmPassword: str = Form(...),
    code: str = Form(...),
    db: Session = Depends(db.getDb)
):
    if password != confirmPassword:
        return JSONResponse(status_code=400, content={"success": False, "error": "Passwords do not match"})

    verification = db.query(Verification).filter(Verification.email == email).first()
    if not verification or verification.code != code or verification.expiresAt < datetime.utcnow():
        return JSONResponse(status_code=400, content={"success": False, "error": "Invalid or expired verification code"})

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return JSONResponse(status_code=400, content={"success": False, "error": "Email already exists"})

    hashedPassword = utils.hashPassword(password)
    apiKey = utils.generateApiKey()

    user = User(email=email, password=hashedPassword, apiKey=apiKey)
    db.add(user)
    db.query(Verification).filter(Verification.email == email).delete()
    db.commit()
    db.refresh(user)

    return JSONResponse(content={
        "success": True,
        "apiKey": apiKey,
        "user": {
            "email": email,
            "id": user.id,
            "createdAt": user.createdAt.isoformat()
        }
    })

@router.post("/login")
async def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(db.getDb)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not utils.verifyPassword(password, user.password):
        return JSONResponse(status_code=401, content={"success": False, "error": "Invalid email or password"})

    return JSONResponse(content={
        "success": True,
        "apiKey": user.apiKey,
        "user": {
            "email": user.email,
            "id": user.id,
            "createdAt": user.createdAt.isoformat()
        }
    })

async def validateApiKey(apiKey: str, db: Session = Depends(db.getDb)):
    user = db.query(User).filter(User.apiKey == apiKey).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return user
