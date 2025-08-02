from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from . import db
from .db import User, Base
from .auth import validateApiKey

router = APIRouter()
templates = Jinja2Templates(directory="templates")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", foreign_keys=[userId])

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
        user = await validateApiKey(apikey, db)
        
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
        await validateApiKey(apikey, db)
        
        messages = db.query(ChatMessage).order_by(ChatMessage.createdAt.desc()).limit(100).all()
        
        messageList = []
        for msg in messages:
            messageList.append({
                "id": msg.id,
                "userEmail": msg.user.email,
                "message": msg.message,
                "createdAt": msg.createdAt.isoformat()
            })
        
        messageList.reverse()
        
        return JSONResponse(content={
            "success": True,
            "messages": messageList
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

@router.get("/api/online-users")
async def getOnlineUsers(apikey: str, db: Session = Depends(db.getDb)):
    try:
        await validateApiKey(apikey, db)
        
        recentMessages = db.query(ChatMessage.userId).filter(
            ChatMessage.createdAt >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        ).distinct()
        
        activeUserIds = [msg.userId for msg in recentMessages]
        
        activeUsers = []
        for userId in activeUserIds:
            user = db.query(User).filter(User.id == userId).first()
            if user:
                activeUsers.append({
                    "email": user.email,
                    "id": user.id
                })
        
        totalUsers = db.query(User).count()
        
        return JSONResponse(content={
            "success": True,
            "activeUsers": activeUsers,
            "totalUsers": totalUsers,
            "activeCount": len(activeUsers)
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
