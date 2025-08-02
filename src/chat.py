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
    senderId = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiverId = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    
    sender = relationship("User", foreign_keys=[senderId])
    receiver = relationship("User", foreign_keys=[receiverId])

@router.get("/chat")
async def chatPage(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@router.post("/api/send-message")
async def sendMessage(
    receiverEmail: str = Form(...),
    message: str = Form(...),
    apikey: str = Form(...),
    db: Session = Depends(db.getDb)
):
    try:
        sender = await validateApiKey(apikey, db)
        
        receiver = db.query(User).filter(User.email == receiverEmail).first()
        if not receiver:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "Receiver not found"}
            )
        
        if sender.id == receiver.id:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Cannot send message to yourself"}
            )
        
        newMessage = ChatMessage(
            senderId=sender.id,
            receiverId=receiver.id,
            message=message
        )
        
        db.add(newMessage)
        db.commit()
        db.refresh(newMessage)
        
        return JSONResponse(content={
            "success": True,
            "message": {
                "id": newMessage.id,
                "senderEmail": sender.email,
                "receiverEmail": receiver.email,
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
async def getMessages(apikey: str, chatWith: str = None, db: Session = Depends(db.getDb)):
    try:
        user = await validateApiKey(apikey, db)
        
        query = db.query(ChatMessage).filter(
            (ChatMessage.senderId == user.id) | (ChatMessage.receiverId == user.id)
        )
        
        if chatWith:
            chatUser = db.query(User).filter(User.email == chatWith).first()
            if chatUser:
                query = query.filter(
                    ((ChatMessage.senderId == user.id) & (ChatMessage.receiverId == chatUser.id)) |
                    ((ChatMessage.senderId == chatUser.id) & (ChatMessage.receiverId == user.id))
                )
        
        messages = query.order_by(ChatMessage.createdAt.desc()).limit(50).all()
        
        messageList = []
        for msg in messages:
            messageList.append({
                "id": msg.id,
                "senderEmail": msg.sender.email,
                "receiverEmail": msg.receiver.email,
                "message": msg.message,
                "createdAt": msg.createdAt.isoformat(),
                "isSent": msg.senderId == user.id
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

@router.get("/api/chat-users")
async def getChatUsers(apikey: str, db: Session = Depends(db.getDb)):
    try:
        user = await validateApiKey(apikey, db)
        
        sentMessages = db.query(ChatMessage.receiverId).filter(ChatMessage.senderId == user.id).distinct()
        receivedMessages = db.query(ChatMessage.senderId).filter(ChatMessage.receiverId == user.id).distinct()
        
        userIds = set()
        for msg in sentMessages:
            userIds.add(msg.receiverId)
        for msg in receivedMessages:
            userIds.add(msg.senderId)
        
        chatUsers = []
        for userId in userIds:
            chatUser = db.query(User).filter(User.id == userId).first()
            if chatUser:
                lastMessage = db.query(ChatMessage).filter(
                    ((ChatMessage.senderId == user.id) & (ChatMessage.receiverId == userId)) |
                    ((ChatMessage.senderId == userId) & (ChatMessage.receiverId == user.id))
                ).order_by(ChatMessage.createdAt.desc()).first()
                
                chatUsers.append({
                    "email": chatUser.email,
                    "lastMessage": lastMessage.message if lastMessage else "",
                    "lastMessageTime": lastMessage.createdAt.isoformat() if lastMessage else ""
                })
        
        chatUsers.sort(key=lambda x: x["lastMessageTime"], reverse=True)
        
        return JSONResponse(content={
            "success": True,
            "users": chatUsers
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
