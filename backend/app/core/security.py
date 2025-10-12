from fastapi import HTTPException, Header
from typing import Optional

async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Verify API key for admin endpoints"""
    from app.core.config import settings
    
    if not x_api_key or x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key"
        )
    return x_api_key
