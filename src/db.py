from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = "postgresql://neondb_owner:npg_vdMq1IOD6wiR@ep-orange-star-a18qqv9e-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

engine = create_engine(DATABASE_URL, pool_size=1, max_overflow=0)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "api_platform_users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    apiKey = Column(String(255), unique=True, nullable=False)
    isVerified = Column(Boolean, default=False, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow, nullable=False)
    lastLoginAt = Column(DateTime, nullable=True)
    isActive = Column(Boolean, default=True, nullable=False)

class VerificationCode(Base):
    __tablename__ = "api_platform_verification_codes"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), index=True, nullable=False)
    code = Column(String(6), nullable=False)
    codeType = Column(String(50), default="registration", nullable=False)
    expiryTime = Column(DateTime, nullable=False)
    isUsed = Column(Boolean, default=False, nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow, nullable=False)
    ipAddress = Column(String(45), nullable=True)
    userAgent = Column(Text, nullable=True)

class UserSession(Base):
    __tablename__ = "api_platform_user_sessions"
    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, nullable=False)
    sessionToken = Column(String(255), unique=True, nullable=False)
    ipAddress = Column(String(45), nullable=True)
    userAgent = Column(Text, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow, nullable=False)
    expiresAt = Column(DateTime, nullable=False)
    isActive = Column(Boolean, default=True, nullable=False)

class ApiKeyUsage(Base):
    __tablename__ = "api_platform_api_key_usage"
    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, nullable=False)
    apiKey = Column(String(255), nullable=False)
    endpoint = Column(String(255), nullable=True)
    requestCount = Column(Integer, default=1, nullable=False)
    lastUsedAt = Column(DateTime, default=datetime.utcnow, nullable=False)
    ipAddress = Column(String(45), nullable=True)
    userAgent = Column(Text, nullable=True)
    responseStatus = Column(Integer, nullable=True)

Base.metadata.create_all(bind=engine)

def getDb():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
