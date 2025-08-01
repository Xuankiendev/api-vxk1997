from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from . import db, utils

router = APIRouter()
templates = Jinja2Templates(directory="templates")

async def validateApiKey(apiKey: str, db: Session = Depends(db.getDb)):
    user = db.query(db.User).filter(db.User.apiKey == apiKey).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return user

@router.post("/signup")
async def signup(request: Request, email: str, password: str, db: Session = Depends(db.getDb)):
    hashedPassword = utils.hashPassword(password)
    apiKey = utils.generateApiKey()
    
    user = db.User(
        email=email,
        password=hashedPassword,
        apiKey=apiKey
    )
    
    db.add(user)
    db.commit()
    
    return {"apiKey": apiKey}

@router.post("/login")
async def login(request: Request, email: str, password: str, db: Session = Depends(db.getDb)):
    user = db.query(db.User).filter(db.User.email == email).first()
    if not user or not utils.verifyPassword(password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {"apiKey": user.apiKey}
