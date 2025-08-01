from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from typing import List, Dict
import json
import pytz
from . import db
from .db import User

router = APIRouter()
templates = Jinja2Templates(directory="templates")
Base = declarative_base()

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, ForeignKey("users.id"), nullable=False)
    username = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False)

    def toDict(self):
        return {
            "id": self.id,
            "userId": self.userId,
            "username": self.username,
            "message": self.message,
            "timestamp": self.timestamp.isoformat()
        }

class ConnectionManager:
    def __init__(self):
        self.connections: List[WebSocket] = []
        self.users: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, email: str):
        await websocket.accept()
        self.connections.append(websocket)
        self.users[email] = websocket

    def disconnect(self, websocket: WebSocket, email: str = None):
        if websocket in self.connections:
            self.connections.remove(websocket)
        if email and email in self.users:
            del self.users[email]

    async def send(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for conn in self.connections:
            try:
                await conn.send_text(message)
            except:
                pass

    def getOnlineUsers(self):
        return list(self.users.keys())

manager = ConnectionManager()

def nowVietnam():
    return datetime.now(pytz.timezone("Asia/Ho_Chi_Minh"))

def getUserByKey(key: str, db: Session):
    return db.query(User).filter(User.apiKey == key).first()

@router.get("/chat")
async def chatPage(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@router.get("/api/chat/messages")
async def getMessages(apiKey: str, limit: int = 50, db: Session = Depends(db.getDb)):
    user = getUserByKey(apiKey, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    messages = db.query(ChatMessage).order_by(ChatMessage.timestamp.desc()).limit(limit).all()
    messages.reverse()
    return JSONResponse(content={
        "success": True,
        "messages": [m.toDict() for m in messages]
    })

@router.get("/api/chat/online")
async def onlineUsers(apiKey: str, db: Session = Depends(db.getDb)):
    user = getUserByKey(apiKey, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return JSONResponse(content={
        "success": True,
        "onlineUsers": manager.getOnlineUsers()
    })

@router.websocket("/ws/chat/{apiKey}")
async def chatSocket(ws: WebSocket, apiKey: str, db: Session = Depends(db.getDb)):
    user = getUserByKey(apiKey, db)
    if not user:
        await ws.close(code=4001)
        return

    email = user.email
    username = email.split("@")[0]
    await manager.connect(ws, email)

    join = {
        "type": "join",
        "data": {
            "username": username,
            "message": f"{username} joined",
            "timestamp": nowVietnam().isoformat()
        }
    }
    await manager.broadcast(json.dumps(join))

    try:
        while True:
            data = await ws.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "message":
                    text = msg.get("message", "").strip()
                    if not text:
                        continue
                    newMsg = ChatMessage(
                        userId=user.id,
                        username=username,
                        message=text,
                        timestamp=nowVietnam()
                    )
                    db.add(newMsg)
                    db.commit()
                    db.refresh(newMsg)
                    await manager.broadcast(json.dumps({
                        "type": "message",
                        "data": newMsg.toDict()
                    }))
                elif msg.get("type") == "ping":
                    await manager.send(json.dumps({"type": "pong"}), ws)
            except:
                pass
    except WebSocketDisconnect:
        manager.disconnect(ws, email)
        leave = {
            "type": "leave",
            "data": {
                "username": username,
                "message": f"{username} left",
                "timestamp": nowVietnam().isoformat()
            }
        }
        await manager.broadcast(json.dumps(leave))
