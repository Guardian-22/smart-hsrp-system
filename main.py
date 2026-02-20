"""
SMART HSRP MONITORING API — Entry Point
=========================================
Run with:
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""

from jose import jwt
import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from pathlib import Path

from config.settings import settings
from backend.api.routes import router as detection_router
from backend.db.database import get_db
from backend.utils.access_func import create_access_token, hash_password, verify_password

app = FastAPI(
    title="Smart HSRP Monitoring API",
    description="Helmet detection, HSRP classification, violation prediction, and OCR pipeline",
    version="2.0.0",
)

static_dir = Path("static")
static_dir.mkdir(exist_ok=True)
(static_dir / "outputs").mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(detection_router, prefix="/api")

@app.get("/health")
async def health_check():
    return {"status": "OK", "version": "2.0.0"}

@app.get("/")
async def root():
    return {"message": "Smart HSRP Monitoring API v2"}

class UserSignup(BaseModel):
    email: EmailStr
    password: str
    role: str = "user"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    email: str
    role: str

@app.post("/signup", response_model=Token)
def signup(user: UserSignup, conn=Depends(get_db)):
    if user.role not in ("admin", "user"):
        raise HTTPException(status_code=400, detail="Invalid role")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = %s", (user.email,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_pw = hash_password(user.password)
    cursor.execute(
        "INSERT INTO users (email, password_hash, role) VALUES (%s, %s, %s) RETURNING id",
        (user.email, hashed_pw, user.role),
    )
    user_id = cursor.fetchone()["id"]
    conn.commit()
    access_token = create_access_token({"sub": user.email, "role": user.role, "user_id": user_id})
    return Token(access_token=access_token, token_type="bearer", user_id=user_id, email=user.email, role=user.role)

@app.post("/login", response_model=Token)
def login(user: UserLogin, conn=Depends(get_db)):
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, password_hash, role FROM users WHERE email = %s", (user.email,))
    db_user = cursor.fetchone()
    if not db_user or not verify_password(user.password, db_user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    access_token = create_access_token({"sub": db_user["email"], "role": db_user["role"], "user_id": db_user["id"]})
    return Token(access_token=access_token, token_type="bearer", user_id=db_user["id"], email=db_user["email"], role=db_user["role"])

@app.get("/verify-token")
def verify_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"valid": True, "email": email, "role": payload.get("role"), "user_id": payload.get("user_id")}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/users")
def get_all_users(token: str, conn=Depends(get_db)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, role, created_at FROM users ORDER BY created_at DESC")
    return {"users": cursor.fetchall()}

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG, workers=1, log_level="info")
