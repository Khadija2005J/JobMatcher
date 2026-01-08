from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import os
from database import get_user_by_id
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer

# Configs (set SECRET_KEY as env var in production)
SECRET_KEY = os.environ.get("SECRET_KEY", "change_this_secret_in_production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token including `sub` and `exp` claims."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "sub": str(data.get("sub"))})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token", auto_error=False)


async def get_token_from_request(request: Request, token: Optional[str] = Depends(oauth2_scheme)):
    """
    Extract Bearer token from Authorization header if present, otherwise
    fall back to the 'access_token' cookie (useful for browser cookie auth).
    """
    # Header-based token (Authorization: Bearer <token>) — preferred
    # Correction : On ignore les tokens "null" ou "undefined" envoyés par erreur par le frontend
    if token and token.lower() not in ["null", "undefined", ""]:
        return token
    # Fallback to cookie
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return cookie_token
        
    # Fallback to query parameter (utile pour les téléchargements directs)
    query_token = request.query_params.get("token")
    if query_token:
        return query_token
        
    print(f"⚠️ AUTH FAIL | URL: {request.url}")
    print(f"   Header: '{token}'")
    print(f"   Cookie 'access_token': '{cookie_token}'")
    print(f"   All Cookies: {list(request.cookies.keys())}")
    raise HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )


async def get_current_user(token: str = Depends(get_token_from_request)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user_by_id(int(user_id))
    if user is None:
        raise credentials_exception
    return user