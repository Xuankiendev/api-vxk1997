import hashlib
import uuid

def hashPassword(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def generateApiKey() -> str:
    return str(uuid.uuid4())

def verifyPassword(plainPassword: str, hashedPassword: str) -> bool:
    return hashPassword(plainPassword) == hashedPassword
