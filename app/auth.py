"""
JWT Authentication module for protecting API routes.
Implements Bearer token authentication for sensitive endpoints.
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Configuration from environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
API_KEY = os.getenv("API_KEY", "your-api-key-change-this-in-production")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token scheme
security = HTTPBearer()

class Token(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Token data extracted from JWT"""
    username: Optional[str] = None
    scopes: list[str] = []

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """
    Verify JWT token from Bearer authentication.
    
    Args:
        credentials: HTTP Bearer credentials
        
    Returns:
        TokenData with decoded information
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        scopes: list = payload.get("scopes", [])
        
        if username is None:
            raise credentials_exception
            
        token_data = TokenData(username=username, scopes=scopes)
        return token_data
        
    except JWTError:
        raise credentials_exception

def verify_api_key(api_key: str) -> bool:
    """
    Verify if the provided API key is valid.
    
    Args:
        api_key: API key to verify
        
    Returns:
        True if valid, False otherwise
    """
    return api_key == API_KEY

def get_admin_token() -> str:
    """
    Generate an admin token for protected operations.
    
    Returns:
        JWT token with admin privileges
    """
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": "admin", "scopes": ["admin", "retrain"]},
        expires_delta=access_token_expires
    )
    return access_token

# Dependency for protected routes
async def require_token(token_data: TokenData = Depends(verify_token)) -> TokenData:
    """
    Dependency to require valid JWT token.
    
    Args:
        token_data: Decoded token data
        
    Returns:
        TokenData if valid
        
    Raises:
        HTTPException: If token is invalid
    """
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data

async def require_admin(token_data: TokenData = Depends(verify_token)) -> TokenData:
    """
    Dependency to require admin privileges.
    
    Args:
        token_data: Decoded token data
        
    Returns:
        TokenData if user has admin scope
        
    Raises:
        HTTPException: If user doesn't have admin privileges
    """
    if "admin" not in token_data.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return token_data

async def require_retrain_permission(token_data: TokenData = Depends(verify_token)) -> TokenData:
    """
    Dependency to require retrain permission.
    
    Args:
        token_data: Decoded token data
        
    Returns:
        TokenData if user has retrain scope
        
    Raises:
        HTTPException: If user doesn't have retrain permission
    """
    if "retrain" not in token_data.scopes and "admin" not in token_data.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to retrain model"
        )
    return token_data

# Simple API key authentication for basic protection
def get_api_key_header(api_key: str) -> str:
    """
    Extract API key from header.
    
    Args:
        api_key: API key from X-API-Key header
        
    Returns:
        API key if valid
        
    Raises:
        HTTPException: If API key is invalid
    """
    if not verify_api_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key"
        )
    return api_key