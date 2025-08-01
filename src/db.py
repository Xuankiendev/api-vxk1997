from sqlalchemy import create_engine, Column, String, Integer, exc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://neondb_owner:npg_vdMq1IOD6wiR@ep-orange-star-a18qqv9e-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    apiKey = Column(String(255), unique=True, nullable=False)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

def getDb():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
