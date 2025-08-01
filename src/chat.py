from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import pytz
import json
from typing import List, Dict
from . import db
from .db import User

router = APIRouter()
templates = Jinja2Templates(directory="templates")

Base = declarative_base()

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    username = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "message": self.message,
            "timestamp": self.timestamp.isoformat()
        }

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_email: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.user_connections[user_email] = websocket

    def disconnect(self, websocket: WebSocket, user_email: str = None):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if user_email and user_email in self.user_connections:
            del self.user_connections[user_email]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

    def get_online_users(self):
        return list(self.user_connections.keys())

manager = ConnectionManager()

def get_vietnam_time():
    vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    return datetime.now(vietnam_tz)

async def get_user_by_api_key(api_key: str, db: Session):
    return db.query(User).filter(User.apiKey == api_key).first()

@router.get("/chat")
async def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@router.get("/api/chat/messages")
async def get_chat_messages(apikey: str, limit: int = 50, db: Session = Depends(db.getDb)):
    user = await get_user_by_api_key(apikey, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        messages = db.query(ChatMessage).order_by(ChatMessage.timestamp.desc()).limit(limit).all()
        messages.reverse()  # Show oldest first
        
        return JSONResponse(content={
            "success": True,
            "messages": [msg.to_dict() for msg in messages]
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@router.post("/api/chat/send")
async def send_message(request: Request, db: Session = Depends(db.getDb)):
    try:
        data = await request.json()
        api_key = data.get("apikey")
        message_text = data.get("message", "").strip()
        
        if not message_text:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Message cannot be empty"}
            )
        
        user = await get_user_by_api_key(api_key, db)
        if not user:
            return JSONResponse(
                status_code=401,
                content={"success": False, "error": "Invalid API key"}
            )
        
        # Create new message
        vietnam_time = get_vietnam_time()
        new_message = ChatMessage(
            user_id=user.id,
            username=user.email.split('@')[0],  # Use email prefix as username
            message=message_text,
            timestamp=vietnam_time
        )
        
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        
        # Broadcast to all connected users
        message_data = {
            "type": "new_message",
            "data": new_message.to_dict()
        }
        await manager.broadcast(json.dumps(message_data))
        
        return JSONResponse(content={
            "success": True,
            "message": new_message.to_dict()
        })
        
    except Exception as e:
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@router.get("/api/chat/online-users")
async def get_online_users(apikey: str, db: Session = Depends(db.getDb)):
    user = await get_user_by_api_key(apikey, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    online_users = manager.get_online_users()
    return JSONResponse(content={
        "success": True,
        "online_users": online_users,
        "count": len(online_users)
    })

@router.websocket("/ws/chat/{api_key}")
async def websocket_endpoint(websocket: WebSocket, api_key: str, db: Session = Depends(db.getDb)):
    user = await get_user_by_api_key(api_key, db)
    if not user:
        await websocket.close(code=4001, reason="Invalid API key")
        return
    
    user_email = user.email
    username = user_email.split('@')[0]
    
    await manager.connect(websocket, user_email)
    
    # Notify others that user joined
    join_message = {
        "type": "user_joined",
        "data": {
            "username": username,
            "message": f"{username} joined the chat",
            "timestamp": get_vietnam_time().isoformat()
        }
    }
    await manager.broadcast(json.dumps(join_message))
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                if message_data.get("type") == "ping":
                    await manager.send_personal_message(json.dumps({"type": "pong"}), websocket)
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_email)
        
        # Notify others that user left
        leave_message = {
            "type": "user_left",
            "data": {
                "username": username,
                "message": f"{username} left the chat",
                "timestamp": get_vietnam_time().isoformat()
            }
        }
        await manager.broadcast(json.dumps(leave_message))
