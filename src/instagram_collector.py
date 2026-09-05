import requests
import pandas as pd
import argparse
import time
import logging
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
API_VERSION = 'v21.0'
BASE_URL = f'https://graph.facebook.com/{API_VERSION}'
DEFAULT_MAX_POSTS = 25
RATE_LIMIT_PAUSE = 60
MAX_RETRIES = 3


def load_credentials() -> tuple[str, str]:
    """Load Instagram API credentials from .env file."""
    # Find .env in project root or current dir
    load_dotenv()
    
    access_token = os.getenv('IG_ACCESS_TOKEN')
    ig_user_id = os.getenv('IG_USER_ID')
    
    if not access_token or access_token.startswith('<') or access_token == 'your_access_token_here':
        raise ValueError("IG_ACCESS_TOKEN is missing or contains a placeholder in .env")
    if not ig_user_id or ig_user_id.startswith('<') or ig_user_id == 'your_ig_user_id_here':
        raise ValueError("IG_USER_ID is missing or contains a placeholder in .env")
        
    return access_token, ig_user_id


def load_usernames(filepath: str) -> list[str]:
    """Read and parse usernames from a file."""
    usernames = []
    if not os.path.exists(filepath):
        logger.warning(f"Usernames file not found: {filepath}")
        return usernames
        
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('@'):
                line = line[1:]
            if line:
                usernames.append(line)
    return usernames


def fetch_profile(username: str, ig_user_id: str, access_token: str, max_posts: int = DEFAULT_MAX_POSTS) -> dict | None:
    """Fetch profile and post data for a username via Instagram Business Discovery API."""
    fields = f"business_discovery.username({username}){{name,biography,followers_count,media_count,media.limit({max_posts}){{like_count,comments_count,timestamp,media_type,caption}}}}"
    url = f"{BASE_URL}/{ig_user_id}"
    params = {
        'fields': fields,
        'access_token': access_token
    }
    
    retries = 0
    while retries <= MAX_RETRIES:
        try:
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            
            if response.status_code == 200:
                # Successfully fetched data
                if 'business_discovery' not in data:
                    logger.warning(f"No business_discovery data for {username}")
                    return None
                    
                bd = data['business_discovery']
                
                # Extract basic profile stats
                profile_data = {
                    'username': username,
                    'name': bd.get('name', ''),
                    'biography': bd.get('biography', ''),
                    'followers_count': bd.get('followers_count', 0),
                    'media_count': bd.get('media_count', 0),
                }
                
                # Process posts for aggregates
                media_data = bd.get('media', {}).get('data', [])
                total_posts = len(media_data)
                
                likes = [post.get('like_count', 0) for post in media_data]
                comments = [post.get('comments_count', 0) for post in media_data]
                
                avg_likes = sum(likes) / total_posts if total_posts > 0 else 0
                avg_comments = sum(comments) / total_posts if total_posts > 0 else 0
                
                followers = profile_data['followers_count']
                engagement_rate = (avg_likes + avg_comments) / followers if followers > 0 else 0
                
                # Compute posting frequency
                posting_frequency = 0.0
                if total_posts > 1:
                    timestamps = []
                    for post in media_data:
                        ts_str = post.get('timestamp')
                        if ts_str:
                            # Parse ISO 8601 string (e.g., 2021-01-01T00:00:00+0000)
                            try:
                                ts = datetime.strptime(ts_str, '%Y-%m-%dT%H:%M:%S%z')
                                timestamps.append(ts)
                            except ValueError:
                                pass
                    
                    if len(timestamps) > 1:
                        timestamps.sort()
                        date_range = (timestamps[-1] - timestamps[0]).days
                        if date_range > 0:
                            weeks = date_range / 7.0
                            posting_frequency = total_posts / weeks
                            
                profile_data.update({
                    'avg_likes': avg_likes,
                    'avg_comments': avg_comments,
                    'engagement_rate': engagement_rate,
                    'posting_frequency': posting_frequency,
                    'total_posts_analyzed': total_posts
                })
                
                return profile_data
                
            elif response.status_code == 429:
                # Rate limit hit
                logger.warning(f"Rate limit exceeded fetching {username}. Pausing for {RATE_LIMIT_PAUSE} seconds...")
                time.sleep(RATE_LIMIT_PAUSE)
                retries += 1
                continue
                
            else:
                # Handle API Errors
                err = data.get('error', {})
                code = err.get('code')
                
                if code == 110 or err.get('error_user_title') == 'A user\'s privacy setting restricts you from viewing this object.':
                    # Not a business account / private / unavailable
                    logger.warning(f"User {username} is not an accessible business/creator account (API Error 110).")
                    return None
                
                error_msg = err.get('message', 'Unknown Error')
                logger.error(f"Error fetching {username}: {error_msg} (Code: {code})")
                
                # Exponential backoff on other errors
                sleep_time = 2 ** retries
                logger.info(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
                retries += 1
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching {username}: {str(e)}")
            sleep_time = 2 ** retries
            time.sleep(sleep_time)
            retries += 1
            
    logger.error(f"Failed to fetch {username} after {MAX_RETRIES} retries.")
    return None


def collect_all(usernames: list[str], ig_user_id: str, access_token: str, max_posts: int = DEFAULT_MAX_POSTS) -> pd.DataFrame:
    """Collect profile data for all provided usernames."""
    results = []
    total = len(usernames)
    
    for i, username in enumerate(usernames):
        logger.info(f"Processing {i+1}/{total}: {username}")
        
        data = fetch_profile(username, ig_user_id, access_token, max_posts)
        if data:
            data['collected_at'] = datetime.utcnow().isoformat() + 'Z'
            results.append(data)
            
        # Delay to avoid hitting rate limits too quickly
        time.sleep(1)
        
    return pd.DataFrame(results)


def main():
    parser = argparse.ArgumentParser(description="Collect real Instagram profile data via Business Discovery API.")
    parser.add_argument('--usernames', type=str, default='usernames.txt', help='Path to file with usernames')
    parser.add_argument('--out', type=str, default='data/instagram_profiles_raw.csv', help='Output CSV path')
    parser.add_argument('--max-posts', type=int, default=DEFAULT_MAX_POSTS, help='Max recent posts to fetch per profile')
    
    args = parser.parse_args()
    
    try:
        access_token, ig_user_id = load_credentials()
        
        usernames = load_usernames(args.usernames)
        if not usernames:
            logger.warning("No usernames loaded. Exiting.")
            return
            
        logger.info(f"Loaded {len(usernames)} usernames. Starting collection...")
        
        # Ensure output directory exists
        out_dir = os.path.dirname(args.out)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
            
        df = collect_all(usernames, ig_user_id, access_token, args.max_posts)
        
        if not df.empty:
            df = df[['username', 'name', 'biography', 'followers_count', 'media_count', 
                     'avg_likes', 'avg_comments', 'engagement_rate', 'posting_frequency', 
                     'total_posts_analyzed', 'collected_at']]
            df.to_csv(args.out, index=False)
            logger.info(f"Successfully saved data for {len(df)} profiles to {args.out}")
        else:
            logger.warning("No data collected (all fetches failed or skipped).")
            
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {str(e)}")


if __name__ == '__main__':
    main()
