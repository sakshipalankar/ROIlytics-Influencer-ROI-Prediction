from fastapi import APIRouter
from ..services import live_db, accounts_db
from ..settings import get_settings
from ..services.public_lookup import get_public_lookup_status

router = APIRouter(prefix="/api/demo", tags=["demo"])

@router.get("/summary")
async def demo_summary():
    profiles = live_db.list_profiles()
    accounts = accounts_db.list_accounts()
    
    # "for each category, the counts of reliable and unreliable profiles per source"
    categories = {}
    oldest_fetched_at = None
    
    unreliable_flags = {"low_followers", "few_posts", "no_posts", "incomplete_data"}
    
    for p in profiles:
        cat = p.get("category", "Unknown")
        src = p.get("source", "official")
        if cat not in categories:
            categories[cat] = {}
        if src not in categories[cat]:
            categories[cat][src] = {"reliable": 0, "unreliable": 0}
            
        warnings = p.get("warnings", [])
        reliable = not bool(unreliable_flags.intersection(warnings))
        if reliable:
            categories[cat][src]["reliable"] += 1
        else:
            categories[cat][src]["unreliable"] += 1
            
        fetched = p.get("fetched_at")
        if fetched:
            if not oldest_fetched_at or fetched < oldest_fetched_at:
                oldest_fetched_at = fetched

    status = get_public_lookup_status()
    
    token_states = []
    for acc in accounts:
        token_states.append({
            "label": acc["label"],
            "username": acc["username"],
            "updated_at": acc["token_updated_at"],
            "expires_at": acc.get("token_expires_at"),
            "has_error": bool(acc.get("last_error"))
        })

    return {
        "categories": categories,
        "oldest_fetched_at": oldest_fetched_at,
        "lookup_enabled": status["enabled"],
        "reader_implemented": status["reader_implemented"],
        "token_states": token_states
    }
