import hashlib
import uuid
import random
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage

def hashPassword(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verifyPassword(plainPassword: str, hashedPassword: str) -> bool:
    return hashPassword(plainPassword) == hashedPassword

def generateApiKey() -> str:
    return str(uuid.uuid4())

def generateVerificationCode() -> str:
    return str(random.randint(100000, 999999))

def oneMinuteLater() -> datetime:
    return datetime.utcnow() + timedelta(minutes=1)

def sendVerificationEmail(toEmail: str, code: str):
    senderEmail = "apivxk1997utilities@gmail.com"
    senderPassword = "jgwcdaniughaooog"

    msg = EmailMessage()
    msg["Subject"] = "Your Verification Code"
    msg["From"] = senderEmail
    msg["To"] = toEmail
    msg.set_content(f"Your verification code is: {code}. It expires in 1 minute.")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(senderEmail, senderPassword)
        smtp.send_message(msg)
