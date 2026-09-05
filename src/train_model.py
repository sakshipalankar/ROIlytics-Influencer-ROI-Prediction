import pandas as pd
import numpy as np
import logging
import os
import argparse
import json
import time
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor
import joblib
import matplotlib.pyplot as plt
import seaborn as sns

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

FEATURE_COLUMNS = [
    'followers_count', 'media_count', 'avg_likes', 'avg_comments', 
    'engagement_rate', 'posting_frequency', 'follower_bucket_encoded', 
    'category_encoded', 'spend', 'log_followers', 'likes_to_comments_ratio'
]
TARGET_COLUMN = 'roi'
TEST_SIZE = 0.2
RANDOM_STATE = 42

def load_data(path: str) -> pd.DataFrame:
    """Load and clean data for modeling."""
    logger.info(f"Loading data from {path}")
    df = pd.read_csv(path)
    logger.info(f"Loaded DataFrame with shape: {df.shape}")
    
    missing_features = [col for col in FEATURE_COLUMNS if col not in df.columns]
    if missing_features:
        raise ValueError(f"Missing feature columns in data: {missing_features}")
    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Missing target column in data: {TARGET_COLUMN}")
        
    initial_len = len(df)
    df = df.dropna(subset=FEATURE_COLUMNS + [TARGET_COLUMN])
    dropped = initial_len - len(df)
    if dropped > 0:
        logger.info(f"Dropped {dropped} rows with NaN values in features or target")
        
    # Remove outliers: clip ROI to [-1, 20] range
    df[TARGET_COLUMN] = df[TARGET_COLUMN].clip(-1, 20)
    
    return df

def prepare_data(df: pd.DataFrame) -> tuple:
    """Split data into train/test sets and scale features."""
    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]
    
    if len(df) < 50:
        logger.warning("Fewer than 50 samples in the dataset!")
        
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    return X_train_scaled, X_test_scaled, y_train, y_test, scaler

def train_models(X_train, y_train) -> dict:
    """Train multiple regression models."""
    models = {
        'Linear Regression': LinearRegression(),
        'Random Forest': RandomForestRegressor(
            n_estimators=200, max_depth=10, min_samples_split=5,
            random_state=RANDOM_STATE, n_jobs=1
        ),
        'XGBoost': XGBRegressor(
            n_estimators=300, learning_rate=0.05, max_depth=6,
            subsample=0.8, colsample_bytree=0.8,
            random_state=RANDOM_STATE, verbosity=0, n_jobs=1
        )
    }
    
    fitted_models = {}
    for name, model in models.items():
        start_time = time.time()
        logger.info(f"Training {name}...")
        model.fit(X_train, y_train)
        elapsed = time.time() - start_time
        logger.info(f"Trained {name} in {elapsed:.2f} seconds")
        fitted_models[name] = model
        
    return fitted_models

def evaluate_models(models: dict, X_test, y_test) -> pd.DataFrame:
    """Evaluate models and return a comparison dataframe."""
    results = []
    for name, model in models.items():
        y_pred = model.predict(X_test)
        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        results.append({
            'Model': name,
            'R2': r2,
            'MAE': mae,
            'RMSE': rmse
        })
        
    df_results = pd.DataFrame(results)
    logger.info(f"Model comparison:\n{df_results.to_string(index=False)}")
    return df_results

def get_feature_importance(model, feature_names: list) -> pd.DataFrame | None:
    """Extract feature importances from a model if available."""
    if hasattr(model, 'feature_importances_'):
        importance = model.feature_importances_
        df = pd.DataFrame({'Feature': feature_names, 'Importance': importance})
        return df.sort_values(by='Importance', ascending=False)
    elif hasattr(model, 'coef_'):
        coef = model.coef_
        df = pd.DataFrame({'Feature': feature_names, 'Importance': np.abs(coef)})
        return df.sort_values(by='Importance', ascending=False)
    return None

def save_results(best_model, best_name: str, scaler, results_df: pd.DataFrame, feature_importance: pd.DataFrame | None, models_dir: str = 'models'):
    """Save the best model, scaler, and evaluation results."""
    os.makedirs(models_dir, exist_ok=True)
    
    # Save best model + scaler
    model_data = {
        'model': best_model,
        'scaler': scaler,
        'model_name': best_name,
        'feature_columns': FEATURE_COLUMNS
    }
    joblib.dump(model_data, os.path.join(models_dir, 'best_model.pkl'))
    logger.info(f"Saved best model to {models_dir}/best_model.pkl")
    
    # Save results_df to CSV and JSON
    csv_path = os.path.join(models_dir, 'model_comparison.csv')
    results_df.to_csv(csv_path, index=False)
    
    json_path = os.path.join(models_dir, 'model_results.json')
    results_df.to_json(json_path, orient='records', indent=4)

def plot_model_comparison(results_df: pd.DataFrame, output_dir: str = 'models'):
    """Create a bar chart comparing model metrics."""
    os.makedirs(output_dir, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle('Model Performance Comparison')
    
    sns.barplot(data=results_df, x='Model', y='R2', ax=axes[0], palette='viridis', hue='Model', legend=False)
    axes[0].set_title('R2 Score')
    axes[0].tick_params(axis='x', rotation=45)
    
    sns.barplot(data=results_df, x='Model', y='MAE', ax=axes[1], palette='viridis', hue='Model', legend=False)
    axes[1].set_title('Mean Absolute Error')
    axes[1].tick_params(axis='x', rotation=45)
    
    sns.barplot(data=results_df, x='Model', y='RMSE', ax=axes[2], palette='viridis', hue='Model', legend=False)
    axes[2].set_title('Root Mean Squared Error')
    axes[2].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'model_comparison.png'), dpi=150)
    plt.close()

def plot_feature_importance(importance_df: pd.DataFrame, model_name: str, output_dir: str = 'models'):
    """Plot the top 10 feature importances."""
    os.makedirs(output_dir, exist_ok=True)
    plt.figure(figsize=(10, 6))
    
    top_10 = importance_df.head(10)
    sns.barplot(data=top_10, x='Importance', y='Feature', palette='viridis', hue='Feature', legend=False)
    plt.title(f'Feature Importance ({model_name})')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'feature_importance.png'), dpi=150)
    plt.close()

def main():
    parser = argparse.ArgumentParser(description="Train and evaluate models for ROI prediction.")
    parser.add_argument('--data', type=str, default='data/features_merged.csv', help="Path to input data")
    parser.add_argument('--output-dir', type=str, default='models', help="Directory to save models and results")
    args = parser.parse_args()
    
    data_path = args.data
    if not os.path.exists(data_path):
        fallback_path = 'data/demo_synthetic.csv'
        logger.warning(f"Data file {data_path} not found. Falling back to {fallback_path}")
        data_path = fallback_path
        
    try:
        df = load_data(data_path)
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return
        
    X_train, X_test, y_train, y_test, scaler = prepare_data(df)
    models = train_models(X_train, y_train)
    results_df = evaluate_models(models, X_test, y_test)
    
    best_row = results_df.loc[results_df['R2'].idxmax()]
    best_name = best_row['Model']
    best_model = models[best_name]
    logger.info(f"Best model identified as {best_name} with R2 = {best_row['R2']:.4f}")
    
    feature_importance = get_feature_importance(best_model, FEATURE_COLUMNS)
    
    save_results(best_model, best_name, scaler, results_df, feature_importance, args.output_dir)
    plot_model_comparison(results_df, args.output_dir)
    
    if feature_importance is not None:
        plot_feature_importance(feature_importance, best_name, args.output_dir)
        
    print(f"Model training and evaluation complete. Best model: {best_name}. Results saved to {args.output_dir}")

if __name__ == '__main__':
    main()
