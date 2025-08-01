from fastapi import APIRouter, Depends, Form
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import exc
from fastapi.responses import JSONResponse
from . import db, utils

router = APIRouter()
templates = Jinja2Templates(directory="templates")

async def validateApiKey(apiKey: str, db: Session = Depends(db.getDb)):
    user = db.query(db.User).filter(db.User.apiKey == apiKey).first()
    if not user:
        return JSONResponse(status_code=401, content={"error": "Invalid API key"})
    return user

@router.post("/signup")
async def signup(email: str = Form(...), password: str = Form(...), db: Session = Depends(db.getDb)):
    try:
        existing_user = db.query(db.User).filter(db.User.email == email).first()
        if existing_user:
            return JSONResponse(status_code=400, content={"success": False, "error": "Email already exists"})

        hashedPassword = utils.hashPassword(password)
        apiKey = utils.generateApiKey()
        
        new_user = db.User(email=email, password=hashedPassword, apiKey=apiKey)
        db.add(new_user)
        db.commit()
        
        return JSONResponse(content={"success": True, "apiKey": apiKey})
        
    except exc.IntegrityError:
        db.rollback()
        return JSONResponse(status_code=400, content={"success": False, "error": "Email already exists"})
    except Exception:
        db.rollback()
        return JSONResponse(status_code=500, content={"success": False, "error": "Server error"})

@router.post("/login")
async def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(db.getDb)):
    try:
        user = db.query(db.User).filter(db.User.email == email).first()
        if not user or not utils.verifyPassword(password, user.password):
            return JSONResponse(status_code=401, content={"success": False, "error": "Invalid email or password"})
        
        return JSONResponse(content={"success": True, "apiKey": user.apiKey})
        
    except Exception:
        return JSONResponse(status_code=500, content={"success": False, "error": "Server error"})
