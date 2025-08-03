import hashlib
import uuid
import re

def hashPassword(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def generateApiKey() -> str:
    return str(uuid.uuid4())

def verifyPassword(plainPassword: str, hashedPassword: str) -> bool:
    return hashPassword(plainPassword) == hashedPassword

def isValidEmail(email: str) -> bool:
    emailPattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(emailPattern, email) is not None

def isStrongPassword(password: str) -> bool:
    if len(password) < 8:
        return False
    
    hasUpper = any(c.isupper() for c in password)
    hasLower = any(c.islower() for c in password)
    hasDigit = any(c.isdigit() for c in password)
    hasSpecial = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    return hasUpper and hasLower and hasDigit and hasSpecial

def generateSessionToken() -> str:
    return str(uuid.uuid4())

def sanitizeInput(inputStr: str) -> str:
    if not inputStr:
        return ""
    return inputStr.strip()

def isValidPassword(password: str) -> bool:
    return len(password) >= 8

def formatDateTime(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def generateVerificationCode() -> str:
    import random
    return str(random.randint(100000, 999999))
