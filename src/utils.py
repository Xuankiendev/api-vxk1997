import secrets, bcrypt

def hashPassword(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def checkPassword(pw: str, hashed: str) -> bool:
    return bcrypt.checkpw(pw.encode(), hashed.encode())

def generateKey() -> str:
    return secrets.tokenUrlsafe(32)
