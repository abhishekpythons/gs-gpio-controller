"""
Raspberry Pi GPIO Controller Backend
FastAPI server with authentication, WebSocket support, and database logging
"""

from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import jwt
import bcrypt
import sqlite3
import asyncio
import json
from contextlib import asynccontextmanager

# Try to import actual GPIO, fallback to mock for testing
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("RPi.GPIO not available - using mock GPIO for testing")

# Configuration
SECRET_KEY = "your-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Database setup
DB_PATH = "gpio_controller.db"

# Mock GPIO class for testing
class MockGPIO:
    BCM = "BCM"
    OUT = "OUT"
    IN = "IN"
    HIGH = 1
    LOW = 0
    
    _pins_state = {}
    _pins_mode = {}
    
    @classmethod
    def setmode(cls, mode):
        pass
    
    @classmethod
    def setup(cls, pin, mode):
        cls._pins_mode[pin] = mode
        if mode == cls.OUT:
            cls._pins_state[pin] = cls.LOW
    
    @classmethod
    def output(cls, pin, state):
        cls._pins_state[pin] = state
    
    @classmethod
    def input(cls, pin):
        return cls._pins_state.get(pin, cls.LOW)
    
    @classmethod
    def cleanup(cls):
        cls._pins_state = {}
        cls._pins_mode = {}

# Use actual GPIO or mock
if GPIO_AVAILABLE:
    gpio = GPIO
else:
    gpio = MockGPIO()

# Initialize GPIO
gpio.setmode(gpio.BCM)

# Default GPIO pins configuration
GPIO_PINS = [17, 18, 27, 22, 23, 24, 25, 4]  # Configurable GPIO pins

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# Database functions
def init_db():
    """Initialize database with users and access_logs tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # Access logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            action TEXT,
            pin INTEGER,
            state TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # GPIO state table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gpio_state (
            pin INTEGER PRIMARY KEY,
            state INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Initialize GPIO pins
    for pin in GPIO_PINS:
        cursor.execute('INSERT OR IGNORE INTO gpio_state (pin, state) VALUES (?, ?)', (pin, 0))
        gpio.setup(pin, gpio.OUT)
        gpio.output(pin, gpio.LOW)
    
    # Create default admin user (username: admin, password: admin123)
    # CHANGE THIS IN PRODUCTION!
    admin_hash = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt())
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, password_hash, email) 
        VALUES (?, ?, ?)
    ''', ("admin", admin_hash.decode('utf-8'), "admin@example.com"))
    
    conn.commit()
    conn.close()

def log_access(user_id: int, username: str, action: str, pin: Optional[int] = None, state: Optional[str] = None):
    """Log user access to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO access_logs (user_id, username, action, pin, state) 
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, username, action, pin, state))
    conn.commit()
    conn.close()

# Pydantic models
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    email: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class GPIOControl(BaseModel):
    pin: int
    state: int  # 0 or 1

class User(BaseModel):
    id: int
    username: str
    email: Optional[str]

# Security functions
security = HTTPBearer()

def create_access_token(data: dict):
    """Create JWT token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        if username is None or user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return {"username": username, "user_id": user_id}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown
    gpio.cleanup()

# FastAPI app
app = FastAPI(title="Raspberry Pi GPIO Controller", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication endpoints
@app.post("/api/register", response_model=Token)
async def register(user: UserCreate):
    """Register a new user"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT id FROM users WHERE username = ?", (user.username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Hash password
    password_hash = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    
    # Insert user
    cursor.execute('''
        INSERT INTO users (username, password_hash, email) 
        VALUES (?, ?, ?)
    ''', (user.username, password_hash.decode('utf-8'), user.email))
    
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # Log registration
    log_access(user_id, user.username, "REGISTER")
    
    # Create token
    access_token = create_access_token({"sub": user.username, "user_id": user_id})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/login", response_model=Token)
async def login(user: UserLogin):
    """Login user"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, username, password_hash, is_active 
        FROM users WHERE username = ?
    ''', (user.username,))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user_id, username, password_hash, is_active = result
    
    if not is_active:
        raise HTTPException(status_code=401, detail="Account is disabled")
    
    # Verify password
    if not bcrypt.checkpw(user.password.encode('utf-8'), password_hash.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Log login
    log_access(user_id, username, "LOGIN")
    
    # Create token
    access_token = create_access_token({"sub": username, "user_id": user_id})
    return {"access_token": access_token, "token_type": "bearer"}

# GPIO endpoints
@app.get("/api/gpio/pins")
async def get_pins(current_user: dict = Depends(verify_token)):
    """Get all GPIO pins and their states"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT pin, state FROM gpio_state ORDER BY pin")
    pins = [{"pin": row[0], "state": row[1]} for row in cursor.fetchall()]
    conn.close()
    
    return {"pins": pins}

@app.post("/api/gpio/control")
async def control_gpio(control: GPIOControl, current_user: dict = Depends(verify_token)):
    """Control a GPIO pin"""
    if control.pin not in GPIO_PINS:
        raise HTTPException(status_code=400, detail="Invalid pin number")
    
    if control.state not in [0, 1]:
        raise HTTPException(status_code=400, detail="State must be 0 or 1")
    
    # Set GPIO state
    gpio.output(control.pin, gpio.HIGH if control.state == 1 else gpio.LOW)
    
    # Update database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE gpio_state SET state = ?, last_updated = CURRENT_TIMESTAMP 
        WHERE pin = ?
    ''', (control.state, control.pin))
    conn.commit()
    conn.close()
    
    # Log action
    log_access(
        current_user["user_id"], 
        current_user["username"], 
        "GPIO_CONTROL", 
        control.pin, 
        "HIGH" if control.state == 1 else "LOW"
    )
    
    # Broadcast to all WebSocket clients
    await manager.broadcast({
        "type": "gpio_update",
        "pin": control.pin,
        "state": control.state,
        "user": current_user["username"]
    })
    
    return {"success": True, "pin": control.pin, "state": control.state}

@app.get("/api/logs")
async def get_logs(limit: int = 50, current_user: dict = Depends(verify_token)):
    """Get access logs"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT username, action, pin, state, timestamp 
        FROM access_logs 
        ORDER BY timestamp DESC 
        LIMIT ?
    ''', (limit,))
    
    logs = [{
        "username": row[0],
        "action": row[1],
        "pin": row[2],
        "state": row[3],
        "timestamp": row[4]
    } for row in cursor.fetchall()]
    
    conn.close()
    return {"logs": logs}

@app.get("/api/user/me")
async def get_current_user(current_user: dict = Depends(verify_token)):
    """Get current user info"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, username, email, created_at 
        FROM users WHERE id = ?
    ''', (current_user["user_id"],))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": result[0],
        "username": result[1],
        "email": result[2],
        "created_at": result[3]
    }

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time GPIO updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and receive messages
            data = await websocket.receive_text()
            # Echo back (can be used for heartbeat)
            await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Raspberry Pi GPIO Controller API", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
