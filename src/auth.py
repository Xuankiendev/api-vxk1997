from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from datetime import datetime
from . import db, utils
from .db import User

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.post("/signup")
async def signup(email: str = Form(...), password: str = Form(...), db: Session = Depends(db.getDb)):
    try:
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Email already exists"}
            )

        hashedPassword = utils.hashPassword(password)
        apiKey = utils.generateApiKey()
        
        new_user = User(
            email=email,
            password=hashedPassword,
            apiKey=apiKey
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return JSONResponse(content={
            "success": True, 
            "apiKey": apiKey,
            "user": {
                "email": email,
                "id": new_user.id,
                "createdAt": new_user.created_at.isoformat() if hasattr(new_user, 'created_at') else datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@router.post("/login")
async def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(db.getDb)):
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or not utils.verifyPassword(password, user.password):
            return JSONResponse(
                status_code=401,
                content={"success": False, "error": "Invalid email or password"}
            )
        
        return JSONResponse(content={
            "success": True, 
            "apiKey": user.apiKey,
            "user": {
                "email": user.email,
                "id": user.id,
                "createdAt": user.created_at.isoformat() if hasattr(user, 'created_at') else datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

async def validateApiKey(apiKey: str, db: Session = Depends(db.getDb)):
    user = db.query(User).filter(User.apiKey == apiKey).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return user
