from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, create_engine
from sqlalchemy.orm import relationship
from . import db
from .db import User, Base, engine

router = APIRouter()
templates = Jinja2Templates(directory="templates")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")

Base.metadata.create_all(bind=engine)

@router.get("/chat")
async def chatPage(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@router.post("/api/send-message")
async def sendMessage(
    message: str = Form(...),
    apikey: str = Form(...),
    db: Session = Depends(db.getDb)
):
    try:
        user = db.query(User).filter(User.apiKey == apikey).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        if not message.strip():
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Message cannot be empty"}
            )
        
        newMessage = ChatMessage(
            userId=user.id,
            message=message.strip()
        )
        
        db.add(newMessage)
        db.commit()
        db.refresh(newMessage)
        
        return JSONResponse(content={
            "success": True,
            "message": {
                "id": newMessage.id,
                "userEmail": user.email,
                "message": newMessage.message,
                "createdAt": newMessage.createdAt.isoformat()
            }
        })
        
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"success": False, "error": e.detail}
        )
    except Exception as e:
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@router.get("/api/messages")
async def getMessages(apikey: str, db: Session = Depends(db.getDb)):
    try:
        user = db.query(User).filter(User.apiKey == apikey).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        messages = db.query(ChatMessage).order_by(ChatMessage.createdAt.asc()).limit(50).all()
        
        messageList = []
        for msg in messages:
            msgUser = db.query(User).filter(User.id == msg.userId).first()
            messageList.append({
                "id": msg.id,
                "userEmail": msgUser.email if msgUser else "Unknown",
                "message": msg.message,
                "createdAt": msg.createdAt.isoformat()
            })
        
        return JSONResponse(content={
            "success": True,
            "messages": messageList,
            "count": len(messageList)
        })
        
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"success": False, "error": e.detail}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )
