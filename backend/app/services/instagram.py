"""Instagram Business Discovery API proxy service."""
from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

IG_API_BASE = "https://graph.facebook.com/v19.0"


async def fetch_instagram_profile(username: str, access_token: str) -> dict[str, Any]:
    """
    Fetch a public Business/Creator Instagram profile via Business Discovery API.
    Requires a valid User Access Token with pages_read_engagement permission.
    """
    params = {
        "fields": "business_discovery.fields(id,username,followers_count,media_count,biography,profile_picture_url,website,media{like_count,comments_count})",
        "access_token": access_token,
    }
    # We need the page ID that manages the token — use /me to get it
    async with httpx.AsyncClient(timeout=30) as client:
        me_resp = await client.get(f"{IG_API_BASE}/me", params={"access_token": access_token, "fields": "id"})
        me_data = me_resp.json()
        if "error" in me_data:
            raise ValueError(f"Instagram API error: {me_data['error'].get('message', 'Unknown error')}")
        page_id = me_data["id"]

        resp = await client.get(
            f"{IG_API_BASE}/{page_id}",
            params={
                "fields": f"business_discovery.fields(id,username,followers_count,media_count,biography,profile_picture_url,website,media{{like_count,comments_count}})",
                "access_token": access_token,
            },
        )
        data = resp.json()

    if "error" in data:
        raise ValueError(f"Instagram API error: {data['error'].get('message', 'Unknown error')}")

    bd = data.get("business_discovery", {})
    media = bd.get("media", {}).get("data", [])

    likes = [m.get("like_count", 0) for m in media if m.get("like_count") is not None]
    comments = [m.get("comments_count", 0) for m in media if m.get("comments_count") is not None]

    return {
        "username": bd.get("username", username),
        "followers_count": bd.get("followers_count", 0),
        "media_count": bd.get("media_count", 0),
        "biography": bd.get("biography"),
        "avg_likes": round(sum(likes) / len(likes), 2) if likes else 0.0,
        "avg_comments": round(sum(comments) / len(comments), 2) if comments else 0.0,
        "profile_picture_url": bd.get("profile_picture_url"),
        "website": bd.get("website"),
    }
