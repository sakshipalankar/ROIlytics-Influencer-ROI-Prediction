import pandas as pd
import numpy as np
import logging
import os
import argparse

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

FOLLOWER_BUCKETS = {
    'Nano': (0, 10_000),
    'Micro': (10_000, 100_000),
    'Macro': (100_000, 1_000_000),
    'Mega': (1_000_000, float('inf'))
}

CATEGORY_KEYWORDS = {
    'Fitness': ['fitness', 'workout', 'gym', 'health', 'training', 'athlete'],
    'Fashion': ['fashion', 'style', 'beauty', 'model', 'outfit', 'clothing'],
    'Tech': ['tech', 'gadget', 'developer', 'software', 'coding', 'digital'],
    'Food': ['food', 'recipe', 'cook', 'chef', 'restaurant', 'baking'],
    'Travel': ['travel', 'adventure', 'explore', 'wanderlust', 'destination'],
    'Lifestyle': ['lifestyle', 'life', 'daily', 'vlog', 'blog']
}

def assign_follower_bucket(followers: int) -> str:
    """Assign a follower bucket based on the follower count."""
    if pd.isna(followers):
        return 'Nano'
    for bucket, (low, high) in FOLLOWER_BUCKETS.items():
        if low <= followers < high:
            return bucket
    return 'Mega'

def infer_category(biography: str) -> str:
    """Infer category from the biography using keyword matching."""
    if not isinstance(biography, str):
        return 'Lifestyle'
    
    bio_lower = biography.lower()
    best_category = 'Lifestyle'
    max_matches = 0
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        matches = sum(1 for keyword in keywords if keyword in bio_lower)
        if matches > max_matches:
            max_matches = matches
            best_category = category
            
    return best_category

def load_instagram_data(path: str) -> pd.DataFrame:
    """Load and process Instagram data."""
    df = pd.read_csv(path)
    logger.info(f"Loaded Instagram data from {path} with shape {df.shape}")
    
    if 'followers_count' in df.columns:
        df['follower_bucket'] = df['followers_count'].apply(assign_follower_bucket)
    else:
        df['follower_bucket'] = 'Nano'
        
    if 'biography' in df.columns:
        df['category'] = df['biography'].apply(infer_category)
    else:
        df['category'] = 'Lifestyle'
        
    return df

def load_kaggle_data(path: str) -> pd.DataFrame:
    """Load and detect variant of Kaggle data."""
    df = pd.read_csv(path)
    logger.info(f"Loaded Kaggle data from {path} with shape {df.shape}")
    
    columns_lower = {c.lower(): c for c in df.columns}
    out_df = pd.DataFrame()
    
    if 'amount_spent' in columns_lower and 'revenue_generated' in columns_lower:
        # Variant A
        if 'campaign_type' in columns_lower:
            mask1 = df[columns_lower['campaign_type']].astype(str).str.contains('Influencer', case=False, na=False)
            mask2 = df.get(columns_lower.get('platform', ''), pd.Series(dtype=str)).astype(str).str.contains('Instagram', case=False, na=False)
            filtered = df[mask1 | mask2]
            if len(filtered) > 0:
                df = filtered
        
        out_df['spend'] = pd.to_numeric(df[columns_lower['amount_spent']], errors='coerce')
        out_df['revenue'] = pd.to_numeric(df[columns_lower['revenue_generated']], errors='coerce')
        
        if 'roi' in columns_lower:
            out_df['roi'] = pd.to_numeric(df[columns_lower['roi']], errors='coerce')
        else:
            out_df['roi'] = (out_df['revenue'] - out_df['spend']) / out_df['spend']
        
        if 'follower_bucket' in columns_lower:
            out_df['follower_bucket'] = df[columns_lower['follower_bucket']].astype(str)
        elif 'budget_allocated' in columns_lower:
            budget = pd.to_numeric(df[columns_lower['budget_allocated']], errors='coerce')
            out_df['follower_bucket'] = pd.cut(budget, bins=[-np.inf, 1000, 5000, 20000, np.inf], labels=['Nano', 'Micro', 'Macro', 'Mega']).astype(str)
        elif 'estimated_reach' in columns_lower:
            reach = pd.to_numeric(df[columns_lower['estimated_reach']], errors='coerce')
            out_df['follower_bucket'] = pd.cut(reach, bins=[-np.inf, 10000, 100000, 1000000, np.inf], labels=['Nano', 'Micro', 'Macro', 'Mega']).astype(str)
        else:
            out_df['follower_bucket'] = 'Micro'
            
        if 'influencer_category' in columns_lower:
            out_df['category'] = df[columns_lower['influencer_category']]
        elif 'category' in columns_lower:
            out_df['category'] = df[columns_lower['category']]
        elif 'target_audience' in columns_lower:
            out_df['category'] = df[columns_lower['target_audience']]
        elif 'industry' in columns_lower:
            out_df['category'] = df[columns_lower['industry']]
        else:
            out_df['category'] = 'Lifestyle'
        
    elif 'influencer_category' in columns_lower and 'estimated_reach' in columns_lower:
        # Variant B
        if 'platform' in columns_lower:
            mask = df[columns_lower['platform']].astype(str).str.contains('Instagram', case=False, na=False)
            filtered = df[mask]
            if len(filtered) > 0:
                df = filtered
            
        out_df['category'] = df[columns_lower['influencer_category']]
        reach = pd.to_numeric(df[columns_lower['estimated_reach']], errors='coerce').fillna(10000)
        
        if 'product_sales' in columns_lower:
            sales = pd.to_numeric(df[columns_lower['product_sales']], errors='coerce').fillna(0)
            out_df['revenue'] = sales * 25
        else:
            out_df['revenue'] = reach * 0.05
            
        out_df['spend'] = reach * 0.01
        out_df['roi'] = (out_df['revenue'] - out_df['spend']) / out_df['spend']
        out_df['follower_bucket'] = pd.cut(reach, bins=[-np.inf, 10000, 100000, 1000000, np.inf], labels=['Nano', 'Micro', 'Macro', 'Mega']).astype(str)
        
    elif 'acquisition_cost' in columns_lower and 'roi' in columns_lower:
        # Variant C
        if 'campaign_type' in columns_lower:
            mask = df[columns_lower['campaign_type']].astype(str).str.contains('Influencer', case=False, na=False)
            filtered = df[mask]
            if len(filtered) > 0:
                df = filtered
            
        out_df['spend'] = pd.to_numeric(df[columns_lower['acquisition_cost']], errors='coerce')
        out_df['roi'] = pd.to_numeric(df[columns_lower['roi']], errors='coerce')
        out_df['revenue'] = out_df['spend'] * (1 + out_df['roi'])
        
        if 'customer_segment' in columns_lower:
            out_df['category'] = df[columns_lower['customer_segment']]
        else:
            out_df['category'] = 'Lifestyle'
            
        out_df['follower_bucket'] = pd.cut(out_df['spend'], bins=[-np.inf, 100, 500, 2000, np.inf], labels=['Nano', 'Micro', 'Macro', 'Mega']).astype(str)
        
    else:
        logger.error("Could not detect Kaggle dataset variant.")
        return pd.DataFrame(columns=['spend', 'revenue', 'roi', 'follower_bucket', 'category'])
        
    # Standardize category values to title case and map unknown to closest
    valid_categories = list(CATEGORY_KEYWORDS.keys())
    def clean_category(cat):
        if not isinstance(cat, str):
            return 'Lifestyle'
        cat_title = cat.strip().title()
        if cat_title in valid_categories:
            return cat_title
        for vc in valid_categories:
            if vc.lower() in cat.lower():
                return vc
        return 'Lifestyle'
        
    out_df['category'] = out_df['category'].apply(clean_category)
    out_df['follower_bucket'] = out_df['follower_bucket'].fillna('Micro')
    
    # Drop rows with invalid spend or roi
    out_df = out_df.dropna(subset=['spend', 'revenue', 'roi'])
    return out_df

def merge_datasets(ig_df: pd.DataFrame, kaggle_df: pd.DataFrame) -> pd.DataFrame:
    """Merge Instagram and Kaggle data based on follower_bucket and category averages.
    
    Produces:
    1. Benchmark data for each real Instagram profile
    2. Combined training data enriched with realistic engagement features for model training
    """
    # Group Kaggle data by follower_bucket and category -> compute mean of spend, revenue, roi
    k_agg = kaggle_df.groupby(['follower_bucket', 'category'])[['spend', 'revenue', 'roi']].mean().reset_index()
    
    # Left join Instagram data
    merged_ig = pd.merge(ig_df, k_agg, on=['follower_bucket', 'category'], how='left')
    
    # For unmatched rows, fall back to joining on follower_bucket only
    unmatched_mask = merged_ig['spend'].isna()
    unmatched_count = unmatched_mask.sum()
    matched_count = len(merged_ig) - unmatched_count
    
    if unmatched_count > 0:
        k_fallback = kaggle_df.groupby(['follower_bucket'])[['spend', 'revenue', 'roi']].mean().reset_index()
        fallback_merge = pd.merge(merged_ig.loc[unmatched_mask, ['follower_bucket']], k_fallback, on='follower_bucket', how='left')
        
        merged_ig.loc[unmatched_mask, 'spend'] = fallback_merge['spend'].values
        merged_ig.loc[unmatched_mask, 'revenue'] = fallback_merge['revenue'].values
        merged_ig.loc[unmatched_mask, 'roi'] = fallback_merge['roi'].values
        
        final_unmatched = merged_ig['spend'].isna().sum()
        fallback_matched = unmatched_count - final_unmatched
    else:
        fallback_matched = 0
        final_unmatched = 0
        
    logger.info(f"Merge stats: {matched_count} matched directly, {fallback_matched} fallback matches, {final_unmatched} unmatched.")
    
    # Save the real profile benchmark dataset for the Streamlit dashboard
    os.makedirs('data', exist_ok=True)
    merged_ig.to_csv('data/instagram_profiles_benchmark.csv', index=False)
    
    # Now enrich Kaggle campaign records with follower and engagement metrics matching their tier + category
    # to provide a statistically robust training dataset (600+ records)
    ig_tier_stats = ig_df.groupby('follower_bucket').agg({
        'followers_count': 'median',
        'media_count': 'median',
        'avg_likes': 'median',
        'avg_comments': 'median',
        'engagement_rate': 'median',
        'posting_frequency': 'median'
    }).to_dict('index')
    
    # Defaults in case some tier is missing in ig_df
    default_stats = {
        'Nano': {'followers_count': 6000, 'media_count': 180, 'avg_likes': 380, 'avg_comments': 35, 'engagement_rate': 0.065, 'posting_frequency': 3.5},
        'Micro': {'followers_count': 45000, 'media_count': 450, 'avg_likes': 1800, 'avg_comments': 90, 'engagement_rate': 0.038, 'posting_frequency': 4.0},
        'Macro': {'followers_count': 450000, 'media_count': 1400, 'avg_likes': 12000, 'avg_comments': 450, 'engagement_rate': 0.024, 'posting_frequency': 4.5},
        'Mega': {'followers_count': 4200000, 'media_count': 4500, 'avg_likes': 65000, 'avg_comments': 1800, 'engagement_rate': 0.015, 'posting_frequency': 5.0}
    }
    
    np.random.seed(42)
    enriched_rows = []
    for _, row in kaggle_df.iterrows():
        bucket = row['follower_bucket']
        cat = row['category']
        spend = row['spend']
        revenue = row['revenue']
        roi = row['roi']
        
        base = ig_tier_stats.get(bucket, default_stats.get(bucket, default_stats['Micro']))
        # Add slight natural variance
        noise = np.random.uniform(0.85, 1.15)
        followers = max(500, int(base.get('followers_count', 25000) * noise))
        media = max(10, int(base.get('media_count', 300) * np.random.uniform(0.8, 1.2)))
        er = max(0.002, float(base.get('engagement_rate', 0.03) * np.random.uniform(0.85, 1.15)))
        likes = max(10, int(followers * er * 0.92))
        comments = max(1, int(followers * er * 0.08))
        freq = max(0.5, round(float(base.get('posting_frequency', 3.5)) * np.random.uniform(0.8, 1.2), 2))
        
        enriched_rows.append({
            'followers_count': followers,
            'media_count': media,
            'avg_likes': likes,
            'avg_comments': comments,
            'engagement_rate': er,
            'posting_frequency': freq,
            'follower_bucket': bucket,
            'category': cat,
            'spend': spend,
            'revenue': revenue,
            'roi': roi
        })
        
    enriched_df = pd.DataFrame(enriched_rows)
    
    # Combine real profiles (with benchmarked spend/roi) and enriched campaigns
    cols_to_keep = ['followers_count', 'media_count', 'avg_likes', 'avg_comments', 
                    'engagement_rate', 'posting_frequency', 'follower_bucket', 'category', 
                    'spend', 'revenue', 'roi']
    combined_df = pd.concat([merged_ig[cols_to_keep], enriched_df[cols_to_keep]], ignore_index=True)
    logger.info(f"Combined training set prepared with {len(combined_df)} samples.")
    return combined_df


def generate_synthetic_data(n: int = 500) -> pd.DataFrame:
    """Generate realistic synthetic data for demo purposes."""
    np.random.seed(42)
    
    followers_count = np.random.lognormal(mean=10.5, sigma=1.5, size=n).astype(int)
    followers_count = np.clip(followers_count, 1000, 5000000)
    
    media_count = np.random.randint(10, 5000, size=n)
    engagement_rate = np.random.beta(a=2, b=10, size=n) * (5000 / np.sqrt(followers_count))
    engagement_rate = np.clip(engagement_rate, 0.001, 0.2)
    
    avg_likes = (followers_count * engagement_rate).astype(int)
    avg_comments = (avg_likes * np.random.uniform(0.01, 0.1, size=n)).astype(int)
    
    posting_frequency = np.random.uniform(1, 14, size=n)
    
    categories = list(CATEGORY_KEYWORDS.keys())
    category = np.random.choice(categories, size=n)
    
    df = pd.DataFrame({
        'username': [f"user_{i}" for i in range(n)],
        'followers_count': followers_count,
        'media_count': media_count,
        'avg_likes': avg_likes,
        'avg_comments': avg_comments,
        'engagement_rate': engagement_rate,
        'posting_frequency': posting_frequency,
        'category': category
    })
    
    df['follower_bucket'] = df['followers_count'].apply(assign_follower_bucket)
    
    df['spend'] = np.sqrt(df['followers_count']) * np.random.uniform(0.5, 2.0, size=n)
    base_roi = 0.5 + (df['engagement_rate'] * 10) + np.random.normal(0, 0.2, size=n)
    df['roi'] = np.clip(base_roi, -0.5, 5.0)
    df['revenue'] = df['spend'] * (1 + df['roi'])
    
    os.makedirs('data', exist_ok=True)
    df.to_csv('data/demo_synthetic.csv', index=False)
    logger.info("Generated synthetic data and saved to data/demo_synthetic.csv")
    
    return df

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Engineer features for ML."""
    df_feat = df.copy()
    
    bucket_map = {'Nano': 0, 'Micro': 1, 'Macro': 2, 'Mega': 3}
    if 'follower_bucket' in df_feat.columns:
        df_feat['follower_bucket_encoded'] = df_feat['follower_bucket'].map(bucket_map).fillna(0).astype(int)
    
    if 'category' in df_feat.columns:
        df_feat['category_encoded'] = pd.Categorical(df_feat['category']).codes
    
    if 'followers_count' in df_feat.columns:
        df_feat['log_followers'] = np.log1p(df_feat['followers_count'])
        
    if 'avg_likes' in df_feat.columns and 'avg_comments' in df_feat.columns:
        df_feat['likes_to_comments_ratio'] = df_feat['avg_likes'] / (df_feat['avg_comments'] + 1)
        
    # Drop non-numeric and non-feature columns
    drop_cols = ['username', 'name', 'biography', 'collected_at', 'follower_bucket', 'category']
    drop_cols = [c for c in drop_cols if c in df_feat.columns]
    df_feat.drop(columns=drop_cols, inplace=True)
    
    return df_feat

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--instagram', default='data/instagram_profiles_raw.csv')
    parser.add_argument('--kaggle', default='data/kaggle_campaign_data.csv')
    parser.add_argument('--out', default='data/features_merged.csv')
    args = parser.parse_args()
    
    ig_exists = os.path.exists(args.instagram)
    k_exists = os.path.exists(args.kaggle)
    
    if ig_exists and k_exists:
        logger.info("Both datasets found. Merging.")
        ig_df = load_instagram_data(args.instagram)
        k_df = load_kaggle_data(args.kaggle)
        df = merge_datasets(ig_df, k_df)
    elif ig_exists:
        logger.warning("Only Instagram dataset found. Generating synthetic spend/ROI.")
        ig_df = load_instagram_data(args.instagram)
        if 'followers_count' in ig_df.columns:
            ig_df['spend'] = np.sqrt(ig_df['followers_count'].fillna(1000)) * np.random.uniform(0.5, 2.0, size=len(ig_df))
        else:
            ig_df['spend'] = np.random.uniform(100, 10000, size=len(ig_df))
            
        engagement = np.random.uniform(0.01, 0.1, size=len(ig_df))
        base_roi = 0.5 + (engagement * 10) + np.random.normal(0, 0.2, size=len(ig_df))
        ig_df['roi'] = np.clip(base_roi, -0.5, 5.0)
        ig_df['revenue'] = ig_df['spend'] * (1 + ig_df['roi'])
        df = ig_df
    elif k_exists:
        logger.warning("Only Kaggle dataset found. Using directly.")
        k_df = load_kaggle_data(args.kaggle)
        k_df['followers_count'] = np.random.uniform(1000, 1000000, size=len(k_df))
        k_df['avg_likes'] = k_df['followers_count'] * np.random.uniform(0.01, 0.05, size=len(k_df))
        k_df['avg_comments'] = k_df['avg_likes'] * 0.1
        df = k_df
    else:
        logger.info("Neither dataset found. Generating completely synthetic data.")
        df = generate_synthetic_data()
        
    df_final = engineer_features(df)
    
    os.makedirs(os.path.dirname(args.out) or '.', exist_ok=True)
    df_final.to_csv(args.out, index=False)
    logger.info(f"Feature engineering complete. Saved to {args.out} with shape {df_final.shape}")

if __name__ == '__main__':
    main()
