import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import os
import json
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title='ROIlytics — Influencer ROI Prediction & Analytics',
    page_icon='📈',
    layout='wide',
    initial_sidebar_state='expanded'
)

# Custom CSS for Premium Design Aesthetic
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .hero-container {
        background: linear-gradient(135deg, #111827 0%, #1f2937 50%, #0f172a 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 24px 30px;
        border-radius: 16px;
        margin-bottom: 24px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.35);
    }
    
    .hero-badge {
        display: inline-block;
        background: linear-gradient(90deg, #6366f1, #a855f7);
        color: white;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 10px;
    }
    
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        background: linear-gradient(120deg, #ffffff 0%, #cbd5e1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    
    .hero-subtitle {
        color: #94a3b8;
        font-size: 0.98rem;
        margin-top: 8px;
        margin-bottom: 0;
    }
    
    .metric-card {
        background: rgba(30, 41, 59, 0.65);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        border-color: rgba(99, 102, 241, 0.4);
        transform: translateY(-2px);
    }
    
    .metric-label {
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94a3b8;
        margin-bottom: 4px;
    }
    
    .metric-value {
        font-size: 1.85rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        color: #f8fafc;
    }
    
    .tier-badge {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 9999px;
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.02em;
    }
    
    .highlight-box {
        background: rgba(99, 102, 241, 0.08);
        border-left: 4px solid #6366f1;
        border-radius: 0 8px 8px 0;
        padding: 12px 16px;
        margin: 14px 0;
    }
</style>
""", unsafe_allow_html=True)

# Helper Functions
@st.cache_resource
def load_model(path='models/best_model.pkl'):
    if os.path.exists(path):
        try:
            return joblib.load(path)
        except Exception as e:
            st.error(f"Error loading model: {e}")
            return None
    return None

@st.cache_data
def load_training_data(path='data/features_merged.csv'):
    if os.path.exists(path):
        return pd.read_csv(path)
    elif os.path.exists('data/demo_synthetic.csv'):
        return pd.read_csv('data/demo_synthetic.csv')
    return None

@st.cache_data
def load_benchmark_profiles(path='data/instagram_profiles_benchmark.csv'):
    if os.path.exists(path):
        return pd.read_csv(path)
    elif os.path.exists('data/instagram_profiles_raw.csv'):
        return pd.read_csv('data/instagram_profiles_raw.csv')
    return None

@st.cache_data
def load_model_results(path='models/model_results.json'):
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading model results: {e}")
            return None
    return None

CAT_MAP = {'Fitness': 0, 'Fashion': 1, 'Tech': 2, 'Food': 3, 'Travel': 4, 'Lifestyle': 5}

def assign_bucket_code(followers: int) -> int:
    if followers < 10_000:
        return 0  # Nano
    elif followers < 100_000:
        return 1  # Micro
    elif followers < 1_000_000:
        return 2  # Macro
    else:
        return 3  # Mega

def engineer_features_dict(raw: dict) -> dict:
    """Ensure all 11 model features are computed accurately from raw inputs."""
    followers = float(raw.get('followers_count', 50000))
    media_count = float(raw.get('media_count', 200))
    likes = float(raw.get('avg_likes', 2000))
    comments = float(raw.get('avg_comments', 50))
    spend = float(raw.get('spend', 5000))
    freq = float(raw.get('posting_frequency', 3.0))
    
    # Category
    cat_val = raw.get('category', 'Lifestyle')
    if isinstance(cat_val, str):
        cat_encoded = CAT_MAP.get(cat_val.strip().title(), 5)
    else:
        cat_encoded = int(raw.get('category_encoded', 5))
        
    er = raw.get('engagement_rate')
    if er is None or np.isnan(er) or er <= 0:
        er = (likes + comments) / followers if followers > 0 else 0.02
        
    bucket_code = raw.get('follower_bucket_encoded')
    if bucket_code is None or np.isnan(bucket_code):
        bucket_code = assign_bucket_code(followers)
        
    log_fol = raw.get('log_followers')
    if log_fol is None or np.isnan(log_fol):
        log_fol = np.log1p(followers)
        
    ratio = raw.get('likes_to_comments_ratio')
    if ratio is None or np.isnan(ratio):
        ratio = likes / max(comments, 1.0)
        
    return {
        'followers_count': followers,
        'media_count': media_count,
        'avg_likes': likes,
        'avg_comments': comments,
        'engagement_rate': er,
        'posting_frequency': freq,
        'follower_bucket_encoded': bucket_code,
        'category_encoded': cat_encoded,
        'spend': spend,
        'log_followers': log_fol,
        'likes_to_comments_ratio': ratio
    }

def predict_roi(model_data: dict, features: dict) -> float:
    prepared_features = engineer_features_dict(features)
    df = pd.DataFrame([prepared_features])
    
    feature_cols = model_data.get('feature_columns', list(prepared_features.keys()))
    df = df[feature_cols]
    
    if 'scaler' in model_data and model_data['scaler'] is not None:
        X = model_data['scaler'].transform(df)
    else:
        X = df.values
        
    roi = model_data['model'].predict(X)[0]
    return float(roi)

def categorize_roi(roi: float) -> tuple[str, str, str]:
    if roi >= 4.0:
        return ('🌟 Exceptional', '#10b981', 'rgba(16, 185, 129, 0.15)')
    elif roi >= 2.5:
        return ('🔥 Excellent', '#3b82f6', 'rgba(59, 130, 246, 0.15)')
    elif roi >= 1.5:
        return ('👍 Good', '#f59e0b', 'rgba(245, 158, 11, 0.15)')
    elif roi >= 0.5:
        return ('⚠️ Moderate', '#f97316', 'rgba(249, 115, 22, 0.15)')
    else:
        return ('❌ Underperforming', '#ef4444', 'rgba(239, 68, 68, 0.15)')

# Load artifacts
model_data = load_model()
training_data = load_training_data()
benchmark_profiles = load_benchmark_profiles()
model_results = load_model_results()

# Hero Header
st.markdown("""
<div class="hero-container">
    <div class="hero-badge">ROIlytics AI Engine • 2026 Production Edition</div>
    <h1 class="hero-title">Influencer Campaign ROI Predictor</h1>
    <p class="hero-subtitle">
        Predict return on investment by bridging live Instagram profile engagement with historical multi-brand campaign performance data.
    </p>
</div>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.markdown("### ⚙️ Campaign Setup")
input_mode = st.sidebar.radio(
    "Prediction Mode",
    ["Manual / Preset Influencer", "Batch CSV Upload", "Live Instagram API"]
)

# Initialize feature dictionary
features = {}
spend = 5000.0

if input_mode == "Manual / Preset Influencer":
    st.sidebar.markdown("#### 👤 Influencer Selection")
    
    preset_options = ["Custom Influencer"]
    preset_dict = {}
    if benchmark_profiles is not None and not benchmark_profiles.empty:
        for _, row in benchmark_profiles.iterrows():
            label = f"{row.get('name', row['username'])} (@{row['username']}) — {row.get('category', 'Lifestyle')}"
            preset_options.append(label)
            preset_dict[label] = row.to_dict()
            
    selected_preset = st.sidebar.selectbox("Load Verified Creator Profile", preset_options)
    
    if selected_preset != "Custom Influencer":
        creator_data = preset_dict[selected_preset]
        def_cat = creator_data.get('category', 'Lifestyle')
        def_fol = int(creator_data.get('followers_count', 50000))
        def_media = int(creator_data.get('media_count', 300))
        def_likes = int(creator_data.get('avg_likes', 2000))
        def_comments = int(creator_data.get('avg_comments', 50))
        def_freq = float(creator_data.get('posting_frequency', 3.5))
        def_spend = float(creator_data.get('spend', 5000.0))
        bio_preview = creator_data.get('biography', '')
        if bio_preview:
            st.sidebar.caption(f"Bio: _{bio_preview[:100]}..._")
    else:
        def_cat = 'Tech'
        def_fol = 85000
        def_media = 340
        def_likes = 3200
        def_comments = 95
        def_freq = 3.5
        def_spend = 4500.0

    cat_list = ['Fitness', 'Fashion', 'Tech', 'Food', 'Travel', 'Lifestyle']
    cat_index = cat_list.index(def_cat) if def_cat in cat_list else 0
    category = st.sidebar.selectbox('Niche / Category', cat_list, index=cat_index)
    
    followers = st.sidebar.number_input('Followers Count', min_value=500, max_value=50_000_000, value=def_fol, step=1000)
    media_count = st.sidebar.number_input('Total Media Posts', min_value=5, max_value=50_000, value=def_media, step=10)
    likes = st.sidebar.number_input('Average Likes per Post', min_value=5, max_value=2_000_000, value=def_likes, step=100)
    comments = st.sidebar.number_input('Average Comments per Post', min_value=0, max_value=100_000, value=def_comments, step=10)
    freq = st.sidebar.slider('Posting Frequency (posts / week)', min_value=0.5, max_value=21.0, value=float(def_freq), step=0.5)
    spend = st.sidebar.number_input('Proposed Campaign Spend ($)', min_value=100, max_value=500_000, value=int(def_spend), step=250)

    # Derived
    raw_inputs = {
        'followers_count': followers,
        'media_count': media_count,
        'avg_likes': likes,
        'avg_comments': comments,
        'category': category,
        'posting_frequency': freq,
        'spend': spend
    }
    features = engineer_features_dict(raw_inputs)

# Main Navigation Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    '📈 ROI Prediction',
    '🧮 Budget & Scenario Simulator',
    '🏆 Model Benchmark',
    '🔍 Feature Importance',
    '📊 Data Explorer',
    '📡 Live Instagram API'
])

# ----------------- TAB 1: PREDICTION -----------------
with tab1:
    if not model_data:
        st.warning('⚠️ Model file (`models/best_model.pkl`) not found. Please train models first.')
    else:
        if input_mode == "Manual / Preset Influencer":
            predicted_roi = predict_roi(model_data, features)
            tier_label, tier_color, tier_bg = categorize_roi(predicted_roi)
            predicted_revenue = spend * (1.0 + predicted_roi)
            predicted_profit = spend * predicted_roi
            
            # KPI Cards
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Predicted ROI Multiplier</div>
                    <div class="metric-value" style="color: {tier_color};">{predicted_roi:.2f}x</div>
                    <div style="margin-top: 6px;">
                        <span class="tier-badge" style="background-color: {tier_bg}; color: {tier_color};">{tier_label}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            with c2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Estimated Gross Revenue</div>
                    <div class="metric-value">${predicted_revenue:,.2f}</div>
                    <div style="font-size: 0.78rem; color: #94a3b8; margin-top: 6px;">Total sales generated</div>
                </div>
                """, unsafe_allow_html=True)

            with c3:
                profit_color = "#10b981" if predicted_profit >= 0 else "#ef4444"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Net Campaign Profit</div>
                    <div class="metric-value" style="color: {profit_color};">${predicted_profit:,.2f}</div>
                    <div style="font-size: 0.78rem; color: #94a3b8; margin-top: 6px;">Revenue minus spend</div>
                </div>
                """, unsafe_allow_html=True)

            with c4:
                er_pct = features['engagement_rate'] * 100
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Audience Engagement Rate</div>
                    <div class="metric-value">{er_pct:.2f}%</div>
                    <div style="font-size: 0.78rem; color: #94a3b8; margin-top: 6px;">Likes + Comments / Followers</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
            
            col_chart, col_meta = st.columns([3, 2])
            with col_chart:
                st.subheader("Performance Multiplier Gauge")
                fig, ax = plt.subplots(figsize=(8, 1.8))
                fig.patch.set_facecolor('#0e1117')
                ax.set_facecolor('#0e1117')
                
                max_scale = max(5.0, predicted_roi * 1.3)
                # Background track
                ax.barh(0, max_scale, color='#1e293b', height=0.45, edgecolor='#334155', linewidth=1)
                # Value bar
                ax.barh(0, min(predicted_roi, max_scale), color=tier_color, height=0.45)
                # Threshold marks
                for threshold, label in [(1.0, '1.0x Break-even'), (2.5, '2.5x Good'), (4.0, '4.0x Exceptional')]:
                    if threshold <= max_scale:
                        ax.axvline(threshold, color='#64748b', linestyle='--', alpha=0.7)
                        ax.text(threshold, 0.35, f" {label}", color='#94a3b8', fontsize=8, va='bottom')
                        
                ax.set_xlim(0, max_scale)
                ax.set_ylim(-0.4, 0.7)
                ax.set_yticks([])
                ax.tick_params(colors='#94a3b8')
                ax.set_xlabel("ROI Multiplier (Revenue = Spend × (1 + ROI))", color='#94a3b8', fontsize=9)
                for spine in ax.spines.values():
                    spine.set_color('#334155')
                st.pyplot(fig)
                plt.close(fig)

            with col_meta:
                st.subheader("Key Influencer Signals")
                tier_names = ['Nano (<10K)', 'Micro (10K-100K)', 'Macro (100K-1M)', 'Mega (>1M)']
                tier_idx = int(features['follower_bucket_encoded'])
                ratio_val = features['likes_to_comments_ratio']
                
                st.markdown(f"""
                - **Tier:** `{tier_names[tier_idx]}`
                - **Likes-to-Comments Ratio:** `{ratio_val:.1f}:1`
                - **Posting Frequency:** `{features['posting_frequency']:.1f} posts/week`
                - **Active Model:** `{model_data.get('model_name', 'Trained Regressor')}`
                """)
                
                with st.expander("🛠️ View Scaled & Encoded ML Vector"):
                    st.json(features)

        elif input_mode == "Batch CSV Upload":
            st.markdown("### 📁 Batch Prediction Engine")
            st.write("Upload a CSV with influencer metrics (`followers_count`, `avg_likes`, `avg_comments`, `spend`, `category`, etc.). Missing columns will be intelligently derived.")
            
            uploaded_file = st.file_uploader("Choose CSV File", type=['csv'])
            if uploaded_file is not None:
                try:
                    df_raw = pd.read_csv(uploaded_file)
                    st.write(f"Loaded **{len(df_raw)}** rows. Processing features...")
                    
                    df_processed = df_raw.copy()
                    preds = []
                    revenues = []
                    profits = []
                    tiers = []
                    
                    for _, row in df_processed.iterrows():
                        row_dict = row.to_dict()
                        pred_roi = predict_roi(model_data, row_dict)
                        preds.append(round(pred_roi, 3))
                        
                        row_spend = float(row_dict.get('spend', 5000))
                        rev = row_spend * (1.0 + pred_roi)
                        revenues.append(round(rev, 2))
                        profits.append(round(rev - row_spend, 2))
                        
                        t_lbl, _, _ = categorize_roi(pred_roi)
                        tiers.append(t_lbl)
                        
                    df_processed['Predicted_ROI'] = preds
                    df_processed['Predicted_Revenue ($)'] = revenues
                    df_processed['Predicted_Net_Profit ($)'] = profits
                    df_processed['Performance_Tier'] = tiers
                    
                    # Metrics summary
                    b1, b2, b3 = st.columns(3)
                    with b1:
                        st.metric("Avg Predicted ROI", f"{df_processed['Predicted_ROI'].mean():.2f}x")
                    with b2:
                        st.metric("Total Projected Revenue", f"${df_processed['Predicted_Revenue ($)'].sum():,.2f}")
                    with b3:
                        st.metric("Total Projected Profit", f"${df_processed['Predicted_Net_Profit ($)'].sum():,.2f}")
                        
                    st.dataframe(df_processed, use_container_width=True)
                    
                    csv_export = df_processed.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Predictions CSV",
                        data=csv_export,
                        file_name=f"roilytics_predictions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime='text/csv'
                    )
                except Exception as e:
                    st.error(f"Error processing uploaded CSV: {e}")

        elif input_mode == "Live Instagram API":
            st.info("Switch to the **📡 Live Instagram API** tab to test live calls or configure tokens.")

# ----------------- TAB 2: BUDGET & SCENARIO SIMULATOR -----------------
with tab2:
    st.subheader("🧮 Campaign Budget & Break-Even Simulator")
    st.markdown("Analyze how varying budget allocations impact expected revenue, profit margins, and ROI efficiency.")
    
    sim_col1, sim_col2 = st.columns([1, 2])
    with sim_col1:
        sim_budget_min = st.slider("Minimum Spend ($)", 500, 10000, 1000, step=500)
        sim_budget_max = st.slider("Maximum Spend ($)", 10000, 200000, 50000, step=5000)
        sim_steps = st.slider("Simulation Granularity (points)", 10, 50, 20)
        
    with sim_col2:
        if model_data and features:
            spend_range = np.linspace(sim_budget_min, sim_budget_max, sim_steps)
            sim_rois = []
            sim_revenues = []
            sim_profits = []
            
            for s in spend_range:
                sim_feats = features.copy()
                sim_feats['spend'] = s
                r = predict_roi(model_data, sim_feats)
                sim_rois.append(r)
                rev = s * (1.0 + r)
                sim_revenues.append(rev)
                sim_profits.append(rev - s)
                
            fig, ax1 = plt.subplots(figsize=(10, 4.5))
            fig.patch.set_facecolor('#0e1117')
            ax1.set_facecolor('#0e1117')
            
            # Revenue & Spend curve
            ax1.plot(spend_range, sim_revenues, color='#3b82f6', linewidth=2.5, label='Projected Gross Revenue ($)')
            ax1.plot(spend_range, sim_profits, color='#10b981', linewidth=2.5, linestyle='-', label='Projected Net Profit ($)')
            ax1.plot(spend_range, spend_range, color='#64748b', linewidth=1.5, linestyle='--', label='Campaign Spend ($)')
            
            ax1.set_xlabel("Campaign Spend ($)", color='#94a3b8')
            ax1.set_ylabel("Financial Outcome ($)", color='#94a3b8')
            ax1.tick_params(colors='#94a3b8')
            ax1.legend(facecolor='#1e293b', edgecolor='#334155', labelcolor='#f8fafc', loc='upper left')
            ax1.grid(True, linestyle=':', alpha=0.3, color='#475569')
            for spine in ax1.spines.values():
                spine.set_color('#334155')
                
            st.pyplot(fig)
            plt.close(fig)
            
            opt_idx = np.argmax(sim_profits)
            st.success(f"💡 **Optimal Simulated Spend:** `${spend_range[opt_idx]:,.0f}` yields estimated Net Profit of **`${sim_profits[opt_idx]:,.0f}`** (ROI: **{sim_rois[opt_idx]:.2f}x**)")

# ----------------- TAB 3: MODEL BENCHMARK -----------------
with tab3:
    st.subheader("🏆 Model Benchmark & Performance Comparison")
    st.markdown("All candidate regression models evaluated using 5-fold train/test split on R² Score, Mean Absolute Error (MAE), and Root Mean Squared Error (RMSE).")
    
    if model_results:
        metrics_df = pd.DataFrame(model_results)
        st.dataframe(metrics_df, use_container_width=True, hide_index=True)
        
        best_name = metrics_df.loc[metrics_df['R2'].idxmax(), 'Model']
        st.markdown(f"""
        <div class="highlight-box">
            <strong>Top Performing Architecture:</strong> <code>{best_name}</code> achieves the highest variance explanation with <strong>R² = {metrics_df['R2'].max():.4f}</strong> and lowest MAE = <strong>{metrics_df['MAE'].min():.4f}</strong>.
        </div>
        """, unsafe_allow_html=True)
        
        m1, m2, m3 = st.columns(3)
        with m1:
            fig, ax = plt.subplots(figsize=(4, 3.5))
            fig.patch.set_facecolor('#0e1117')
            ax.set_facecolor('#0e1117')
            sns.barplot(data=metrics_df, x='Model', y='R2', palette='viridis', ax=ax, hue='Model', legend=False)
            ax.set_title("R² Score (Higher is Better)", color='#f8fafc')
            ax.tick_params(colors='#94a3b8', rotation=25)
            for s in ax.spines.values(): s.set_color('#334155')
            st.pyplot(fig)
            plt.close(fig)
            
        with m2:
            fig, ax = plt.subplots(figsize=(4, 3.5))
            fig.patch.set_facecolor('#0e1117')
            ax.set_facecolor('#0e1117')
            sns.barplot(data=metrics_df, x='Model', y='MAE', palette='magma', ax=ax, hue='Model', legend=False)
            ax.set_title("MAE (Lower is Better)", color='#f8fafc')
            ax.tick_params(colors='#94a3b8', rotation=25)
            for s in ax.spines.values(): s.set_color('#334155')
            st.pyplot(fig)
            plt.close(fig)

        with m3:
            fig, ax = plt.subplots(figsize=(4, 3.5))
            fig.patch.set_facecolor('#0e1117')
            ax.set_facecolor('#0e1117')
            sns.barplot(data=metrics_df, x='Model', y='RMSE', palette='rocket', ax=ax, hue='Model', legend=False)
            ax.set_title("RMSE (Lower is Better)", color='#f8fafc')
            ax.tick_params(colors='#94a3b8', rotation=25)
            for s in ax.spines.values(): s.set_color('#334155')
            st.pyplot(fig)
            plt.close(fig)

# ----------------- TAB 4: FEATURE IMPORTANCE -----------------
with tab4:
    st.subheader("🔍 Feature Importance & Driver Analysis")
    st.write("Identifies the dominant signals driving campaign ROI predictions.")
    
    if os.path.exists('models/feature_importance.png'):
        st.image('models/feature_importance.png', caption='Model Feature Importance Rankings')
    elif model_data and hasattr(model_data['model'], 'feature_importances_'):
        importances = model_data['model'].feature_importances_
        feat_cols = model_data.get('feature_columns', [])
        if len(importances) == len(feat_cols):
            imp_df = pd.DataFrame({'Feature': feat_cols, 'Importance': importances}).sort_values('Importance', ascending=False)
            
            fig, ax = plt.subplots(figsize=(9, 4.5))
            fig.patch.set_facecolor('#0e1117')
            ax.set_facecolor('#0e1117')
            sns.barplot(data=imp_df.head(10), x='Importance', y='Feature', palette='crest', ax=ax, hue='Feature', legend=False)
            ax.set_title("Top 10 Feature Importances", color='#f8fafc')
            ax.tick_params(colors='#94a3b8')
            for s in ax.spines.values(): s.set_color('#334155')
            st.pyplot(fig)
            plt.close(fig)

# ----------------- TAB 5: DATA EXPLORER -----------------
with tab5:
    st.subheader("📊 Dataset Explorer & Distributions")
    if training_data is not None:
        st.write(f"Total training observations: **{len(training_data):,}**")
        st.dataframe(training_data.head(50), use_container_width=True)
        
        st.subheader("Bivariate Distributions")
        c1, c2 = st.columns(2)
        with c1:
            if 'engagement_rate' in training_data.columns and 'roi' in training_data.columns:
                fig, ax = plt.subplots(figsize=(6, 4))
                fig.patch.set_facecolor('#0e1117')
                ax.set_facecolor('#0e1117')
                sns.scatterplot(data=training_data, x='engagement_rate', y='roi', color='#6366f1', alpha=0.6, ax=ax)
                ax.set_title("Engagement Rate vs. ROI Multiplier", color='#f8fafc')
                ax.tick_params(colors='#94a3b8')
                for s in ax.spines.values(): s.set_color('#334155')
                st.pyplot(fig)
                plt.close(fig)
                
        with c2:
            if 'spend' in training_data.columns and 'revenue' in training_data.columns:
                fig, ax = plt.subplots(figsize=(6, 4))
                fig.patch.set_facecolor('#0e1117')
                ax.set_facecolor('#0e1117')
                sns.scatterplot(data=training_data, x='spend', y='revenue', color='#10b981', alpha=0.6, ax=ax)
                ax.set_title("Campaign Spend vs. Revenue Generated", color='#f8fafc')
                ax.tick_params(colors='#94a3b8')
                for s in ax.spines.values(): s.set_color('#334155')
                st.pyplot(fig)
                plt.close(fig)
    else:
        st.info("No training data loaded.")

# ----------------- TAB 6: LIVE INSTAGRAM API -----------------
with tab6:
    st.subheader("📡 Live Instagram Graph API (Business Discovery)")
    st.markdown("""
    The **Instagram Business Discovery API** queries real-time public metrics (`followers_count`, `media_count`, per-post `like_count`, `comments_count`) for any Business or Creator account.
    """)
    
    env_token = os.getenv('IG_ACCESS_TOKEN', '')
    env_user_id = os.getenv('IG_USER_ID', '')
    
    api_col1, api_col2 = st.columns([1, 1])
    with api_col1:
        st.markdown("#### API Gateway Credentials Status")
        has_token = bool(env_token and not env_token.startswith('<') and env_token != 'your_access_token_here')
        has_uid = bool(env_user_id and not env_user_id.startswith('<') and env_user_id != 'your_ig_user_id_here')
        
        if has_token and has_uid:
            st.success("✅ Credentials configured in `.env`!")
        else:
            st.warning("⚠️ Using offline mode. Meta credentials are not configured in `.env`.")
            
        with st.expander("Setup Instructions"):
            st.markdown("""
            1. Go to [developers.facebook.com](https://developers.facebook.com) and create an App of type **Business**.
            2. Add **Instagram Graph API**.
            3. Link your Instagram account (converted to Business/Creator) to a Facebook Page.
            4. Generate a User Access Token with `instagram_basic` and `pages_show_list`.
            5. Set credentials in `.env`:
            ```bash
            IG_ACCESS_TOKEN=your_token_here
            IG_USER_ID=your_instagram_business_id
            ```
            """)

    with api_col2:
        st.markdown("#### Test Live Profile Fetch")
        test_username = st.text_input("Instagram Username (Business/Creator)", value="mkbhd")
        if st.button("🚀 Fetch Real-Time Instagram Stats"):
            if not (has_token and has_uid):
                st.info(f"💡 Offline Demo Mode: Pulling pre-collected profile metrics for `@{test_username}` from dataset...")
                if benchmark_profiles is not None:
                    matched = benchmark_profiles[benchmark_profiles['username'].str.lower() == test_username.lower()]
                    if not matched.empty:
                        m_row = matched.iloc[0]
                        st.json({
                            'username': m_row['username'],
                            'name': m_row.get('name', ''),
                            'followers_count': int(m_row['followers_count']),
                            'media_count': int(m_row['media_count']),
                            'avg_likes': int(m_row['avg_likes']),
                            'avg_comments': int(m_row['avg_comments']),
                            'engagement_rate': float(m_row['engagement_rate']),
                            'posting_frequency': float(m_row['posting_frequency'])
                        })
                    else:
                        st.warning(f"Username `{test_username}` is not in pre-collected cache. Add Meta token to `.env` to query any live Instagram account!")
            else:
                from src.instagram_collector import fetch_profile
                with st.spinner(f"Querying Meta Graph API for @{test_username}..."):
                    live_data = fetch_profile(test_username, env_user_id, env_token)
                    if live_data:
                        st.success(f"Successfully retrieved @{test_username} live data!")
                        st.json(live_data)
                    else:
                        st.error("Failed to fetch profile. Verify the account is a public Business/Creator account and your token is valid.")
