from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import smtplib
import random
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from . import db, utils
from .db import User, VerificationCode

router = APIRouter()
templates = Jinja2Templates(directory="templates")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_USER = "apivxk1997utilities@gmail.com"
EMAIL_PASSWORD = "Kien@123"

class EmailService:
    @staticmethod
    async def sendVerificationCode(userEmail: str, verificationCode: str):
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = "Email Verification Code - API Platform"
            message["From"] = EMAIL_USER
            message["To"] = userEmail
            
            htmlContent = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #4f46e5;">🚀 API Platform</h1>
                </div>
                <div style="background: #f8fafc; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h2 style="color: #334155; margin-bottom: 15px;">Email Verification</h2>
                    <p style="color: #64748b; margin-bottom: 20px;">Your verification code is:</p>
                    <div style="background: white; padding: 15px; border-radius: 6px; text-align: center; border: 2px solid #4f46e5;">
                        <span style="font-size: 24px; font-weight: bold; color: #4f46e5; letter-spacing: 2px;">{verificationCode}</span>
                    </div>
                    <p style="color: #ef4444; margin-top: 15px; font-size: 14px;">⚠️ This code expires in 1 minute</p>
                </div>
                <div style="text-align: center; color: #64748b; font-size: 12px;">
                    <p>If you didn't request this code, please ignore this email.</p>
                </div>
            </body>
            </html>
            """
            
            message.attach(MIMEText(htmlContent, "html"))
            
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(EMAIL_USER, EMAIL_PASSWORD)
                server.send_message(message)
            
            return True
        except Exception as e:
            print(f"Email sending failed: {str(e)}")
            return False

@router.post("/sendVerificationCode")
async def sendVerificationCode(email: str = Form(...), db: Session = Depends(db.getDb)):
    try:
        if not utils.isValidEmail(email):
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Invalid email format"}
            )
        
        existingUser = db.query(User).filter(User.email == email).first()
        if existingUser:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Email already registered"}
            )
        
        verificationCode = str(random.randint(100000, 999999))
        expiryTime = datetime.utcnow() + timedelta(minutes=1)
        
        existingCode = db.query(VerificationCode).filter(VerificationCode.email == email).first()
        if existingCode:
            existingCode.code = verificationCode
            existingCode.expiryTime = expiryTime
            existingCode.isUsed = False
        else:
            newCode = VerificationCode(
                email=email,
                code=verificationCode,
                expiryTime=expiryTime,
                isUsed=False
            )
            db.add(newCode)
        
        db.commit()
        
        emailSent = await EmailService.sendVerificationCode(email, verificationCode)
        if not emailSent:
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": "Failed to send verification email"}
            )
        
        return JSONResponse(content={
            "success": True,
            "message": "Verification code sent to your email"
        })
        
    except Exception as e:
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@router.post("/signup")
async def signup(
    email: str = Form(...),
    password: str = Form(...),
    confirmPassword: str = Form(...),
    verificationCode: str = Form(...),
    db: Session = Depends(db.getDb)
):
    try:
        if not utils.isValidEmail(email):
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Invalid email format"}
            )
        
        if len(password) < 8:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Password must be at least 8 characters"}
            )
        
        if password != confirmPassword:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Passwords do not match"}
            )
        
        if not utils.isStrongPassword(password):
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Password must contain uppercase, lowercase, number and special character"}
            )
        
        existingUser = db.query(User).filter(User.email == email).first()
        if existingUser:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Email already registered"}
            )
        
        storedCode = db.query(VerificationCode).filter(
            VerificationCode.email == email,
            VerificationCode.code == verificationCode,
            VerificationCode.isUsed == False
        ).first()
        
        if not storedCode:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Invalid verification code"}
            )
        
        if datetime.utcnow() > storedCode.expiryTime:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Verification code has expired"}
            )
        
        hashedPassword = utils.hashPassword(password)
        apiKey = utils.generateApiKey()
        
        newUser = User(
            email=email,
            password=hashedPassword,
            apiKey=apiKey,
            isVerified=True,
            createdAt=datetime.utcnow()
        )
        
        storedCode.isUsed = True
        
        db.add(newUser)
        db.commit()
        db.refresh(newUser)
        
        return JSONResponse(content={
            "success": True,
            "apiKey": apiKey,
            "user": {
                "email": email,
                "id": newUser.id,
                "createdAt": newUser.createdAt.isoformat()
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
        
        if not user.isVerified:
            return JSONResponse(
                status_code=401,
                content={"success": False, "error": "Please verify your email first"}
            )
        
        return JSONResponse(content={
            "success": True,
            "apiKey": user.apiKey,
            "user": {
                "email": user.email,
                "id": user.id,
                "createdAt": user.createdAt.isoformat()
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
