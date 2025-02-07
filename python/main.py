from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import JWTError, jwt
from sqlalchemy import create_engine, Column, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import threading
import time
import urllib
from cachetools import TTLCache

# Define your connection parameters
username = "uldanone"
password = "125563_oauth"
server = "oauth.database.windows.net"
database = "oauth_db"
driver = "ODBC Driver 18 for SQL Server"

# Create the connection string
connection_string = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};UID={username};PWD={password}"

# Create the engine with connection pooling parameters
engine = create_engine(
    f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(connection_string)}",
    poolclass=QueuePool,
    pool_size=100,  # Maximum number of connections in the pool
    max_overflow=50,  # Additional connections allowed above pool_size
    pool_timeout=30,  # Time to wait for a connection if the pool is full
    pool_recycle=3600,  # Recycle connections after this many seconds
    echo=False,  # Set to True to enable SQL query logging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

token_cache = TTLCache(maxsize=1000, ttl=7200)


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

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


class CheckRequest(BaseModel):
    token: str


class CheckResponse(BaseModel):
    valid: bool
    scopes: str


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
        raise JWTError


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
    if request.client_id in token_cache:
        cached_token = token_cache[request.client_id]
        if cached_token["expires_at"] > datetime.utcnow():
            return cached_token

    print("test")  # Debugging print
    db = SessionLocal()
    try:
        existing_token = (
            db.query(Token).filter(Token.client_id == request.client_id).first()
        )
        if existing_token and (
            existing_token.expires_at - datetime.utcnow()
        ) > timedelta(minutes=30):
            token_cache[request.client_id] = {
                "token": existing_token.token_id,
                "expires_at": existing_token.expires_at,
                "scopes": existing_token.scopes,
            }
            return {
                "token": existing_token.token_id,
                "expires_at": existing_token.expires_at,
            }

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

        # Store in cache
        token_cache[request.client_id] = {
            "token": token,
            "expires_at": expires_at,
            "scopes": request.scopes,
        }

        return {"token": token, "expires_at": expires_at}
    finally:
        db.close()


@app.post("/check", response_model=CheckResponse)
def check_token(request: CheckRequest):
    try:
        token = request.token
        payload = validate_token(token)
        exp_time = datetime.utcfromtimestamp(payload["exp"])

        # If expired, return immediately
        if exp_time < datetime.utcnow():
            return {"valid": False, "scopes": "Token expired"}

        # Check cache first
        for client_id, cached_token in token_cache.items():
            if cached_token["token"] == token:
                return {"valid": True, "scopes": cached_token["scopes"]}

        # If not in cache, check the database
        db = SessionLocal()
        try:
            db_token = db.query(Token).filter(Token.token_id == token).first()
            if not db_token:
                return {"valid": False, "scopes": "Token not found"}
            return {"valid": True, "scopes": db_token.scopes}
        finally:
            db.close()

    except JWTError:
        return {"valid": False, "scopes": "Invalid or expired token"}
