"""Instagram Business Discovery proxy router."""
from fastapi import APIRouter, HTTPException
from ..schemas.schemas import InstagramFetchRequest, InstagramProfile
from ..services.instagram import fetch_instagram_profile
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/instagram", tags=["instagram"])


@router.post("/fetch", response_model=InstagramProfile)
async def fetch_profile(body: InstagramFetchRequest) -> InstagramProfile:
    """
    Fetch a real Instagram Business/Creator profile via Business Discovery API.
    Requires a valid User Access Token.
    """
    try:
        data = await fetch_instagram_profile(body.username, body.access_token)
        return InstagramProfile(**data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Instagram fetch failed")
        raise HTTPException(status_code=500, detail=str(exc))
