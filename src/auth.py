from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from . import db, utils

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.post("/signup")
async def signup(email: str = Form(...), password: str = Form(...), db: Session = Depends(db.getDb)):
    try:
        with db.getDbContext() as session:
            existing_user = session.query(db.User).filter(db.User.email == email).first()
            if existing_user:
                return JSONResponse(status_code=400, content={"success": False, "error": "Email already exists"})

            hashedPassword = utils.hashPassword(password)
            apiKey = utils.generateApiKey()
            
            new_user = db.User(email=email, password=hashedPassword, apiKey=apiKey)
            session.add(new_user)
            session.commit()
            
            return JSONResponse(content={"success": True, "apiKey": apiKey})
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

@router.post("/login")
async def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(db.getDb)):
    try:
        with db.getDbContext() as session:
            user = session.query(db.User).filter(db.User.email == email).first()
            if not user or not utils.verifyPassword(password, user.password):
                return JSONResponse(status_code=401, content={"success": False, "error": "Invalid email or password"})
            
            return JSONResponse(content={"success": True, "apiKey": user.apiKey})
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

async def validateApiKey(apiKey: str, db: Session = Depends(db.getDb)):
    try:
        with db.getDbContext() as session:
            user = session.query(db.User).filter(db.User.apiKey == apiKey).first()
            if not user:
                raise HTTPException(status_code=401, detail="Invalid API key")
            return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
