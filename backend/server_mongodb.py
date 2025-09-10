from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
import bcrypt
import jwt
from datetime import datetime, timedelta
import os
from pathlib import Path
import secrets
import time
from dotenv import load_dotenv
import pymongo
from pymongo import MongoClient
from bson import ObjectId
from bson.errors import InvalidId
import json

# Load environment variables
load_dotenv()

# MongoDB connection
MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb://localhost:27017/')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'tax_sale_compass')

# Initialize MongoDB client
client = MongoClient(MONGODB_URL)
db = client[DATABASE_NAME]

# Collections
users_collection = db.users
properties_collection = db.properties
user_favorites_collection = db.user_favorites
scraper_config_collection = db.scraper_config

# JWT Configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-here')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

# Initialize FastAPI app
app = FastAPI(title= Tax Sale Compass API - MongoDB, version=2.0.0)

# Security
security = HTTPBearer()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[*],
    allow_credentials=True,
    allow_methods=[*],
    allow_headers=[*],
)

# Pydantic models
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    subscription_tier: str
    is_admin: bool
    created_at: datetime
    updated_at: datetime

# Helper functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({exp: expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get(sub)
        if user_id is None:
            raise HTTPException(status_code=401, detail=Invalid authentication credentials)
        
        # Convert string ID to ObjectId for MongoDB query
        try:
            user_object_id = ObjectId(user_id)
        except InvalidId:
            raise HTTPException(status_code=401, detail=Invalid user ID format)
        
        user = users_collection.find_one({_id: user_object_id})
        if user is None:
            raise HTTPException(status_code=401, detail=User not found)
        
        # Convert ObjectId to string for response
        user[id] = str(user[_id])
        del user[_id]
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail=Token expired)
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail=Invalid token)

# API Routes
@app.get(/)
async def root():
    return {message: Tax Sale Compass API - MongoDB Version, status: running}

@app.post(/auth/register)
async def register(user: UserCreate):
    # Check if user already exists
    existing_user = users_collection.find_one({email: user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail=Email already registered)
    
    # Create new user
    hashed_password = hash_password(user.password)
    user_doc = {
        email: user.email,
        password: hashed_password,
        subscription_tier: free,
        subscription_status: free,
        is_admin: False,
        created_at: datetime.utcnow(),
        updated_at: datetime.utcnow()
    }
    
    result = users_collection.insert_one(user_doc)
    user_id = str(result.inserted_id)
    
    # Create access token
    access_token = create_access_token(data={sub: user_id})
    
    return {
        access_token: access_token,
        token_type: bearer,
        user: {
            id: user_id,
            email: user.email,
            subscription_tier: free,
            is_admin: False
        }
    }

@app.post(/auth/login)
async def login(user: UserLogin):
    # Find user by email
    db_user = users_collection.find_one({email: user.email})
    if not db_user or not verify_password(user.password, db_user[password]):
        raise HTTPException(status_code=401, detail=Invalid email or password)
    
    # Create access token
    user_id = str(db_user[_id])
    access_token = create_access_token(data={sub: user_id})
    
    return {
        access_token: access_token,
        token_type: bearer,
        user: {
            id: user_id,
            email: db_user[email],
            subscription_tier: db_user.get(subscription_tier, free),
            is_admin: db_user.get(is_admin, False)
        }
    }

@app.get(/auth/me)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return {
        id: current_user[id],
        email: current_user[email],
        subscription_tier: current_user.get(subscription_tier, free),
        is_admin: current_user.get(is_admin, False),
        created_at: current_user.get(created_at),
        updated_at: current_user.get(updated_at)
    }

@app.get(/properties)
async def get_properties(
    skip: int = 0,
    limit: int = 100,
    municipality: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if municipality:
        query[municipality] = {: municipality, : i}
    
    properties = list(properties_collection.find(query).skip(skip).limit(limit))
    
    # Convert ObjectId to string for JSON serialization
    for prop in properties:
        prop[id] = str(prop[_id])
        del prop[_id]
    
    total_count = properties_collection.count_documents(query)
    
    return {
        properties: properties,
        total: total_count,
        skip: skip,
        limit: limit
    }

@app.get(/health)
async def health_check():
    try:
        # Test MongoDB connection
        client.admin.command('ping')
        return {
            status: healthy,
            database: connected,
            timestamp: datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            status: unhealthy,
            database: disconnected,
            error: str(e),
            timestamp: datetime.utcnow().isoformat()
        }

if __name__ == __main__:
    import uvicorn
    uvicorn.run(app, host=0.0.0.0, port=8001)
