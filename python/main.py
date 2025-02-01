from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import JWTError, jwt
from sqlalchemy import create_engine, Column, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import threading
import time

# Database setup
DATABASE_URL = "mssql+pyodbc://<username>:<password>@<server>.database.windows.net/<database>?driver=ODBC+Driver+17+for+SQL+Server"
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=400,  # Set pool_size to 400
    max_overflow=50,  # Allow 50 more connections above the pool_size
    pool_timeout=30,  # Timeout for getting a connection from the pool
    pool_recycle=3600,  # Recycle connections every hour
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Token(Base):
    __tablename__ = "Tokens"
    token_id = Column(String(255), primary_key=True)
    client_id = Column(String(255), nullable=False)
    scopes = Column(Text, nullable=False)
    issued_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)


Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI()

# JWT settings
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120


class TokenRequest(BaseModel):
    client_id: str
    scopes: str


class TokenResponse(BaseModel):
    token: str
    expires_at: datetime


class CheckResponse(BaseModel):
    valid: bool
    scopes: Optional[str] = None
    message: Optional[str] = None


# Token generation
def create_token(client_id: str, scopes: str) -> str:
    expires_at = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"client_id": client_id, "scopes": scopes, "exp": expires_at}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, expires_at


# Token validation
def validate_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def purge_expired_tokens():
    while True:
        db = SessionLocal()
        try:
            now = datetime.utcnow()
            db.query(Token).filter(Token.expires_at < now).delete()
            db.commit()
        finally:
            db.close()
        time.sleep(3600)  # Run every hour


purger_thread = threading.Thread(target=purge_expired_tokens, daemon=True)
purger_thread.start()


@app.post("/token", response_model=TokenResponse)
def issue_token(request: TokenRequest):
    db = SessionLocal()
    try:
        existing_token = (
            db.query(Token).filter(Token.client_id == request.client_id).first()
        )
        if existing_token and (
            existing_token.expires_at - datetime.utcnow()
        ) > timedelta(minutes=30):
            raise HTTPException(status_code=400, detail="Valid token already exists")

        token, expires_at = create_token(request.client_id, request.scopes)
        db_token = Token(
            token_id=token,
            client_id=request.client_id,
            scopes=request.scopes,
            issued_at=datetime.utcnow(),
            expires_at=expires_at,
        )
        db.add(db_token)
        db.commit()
        return {"token": token, "expires_at": expires_at}
    finally:
        db.close()


@app.post("/check", response_model=CheckResponse)
def check_token(token: str):
    db = SessionLocal()
    try:
        payload = validate_token(token)
        db_token = db.query(Token).filter(Token.token_id == token).first()
        if not db_token:
            return {"valid": False, "message": "Token not found"}
        return {"valid": True, "scopes": db_token.scopes}
    except HTTPException as e:
        return {"valid": False, "message": str(e.detail)}
    finally:
        db.close()
