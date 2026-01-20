import sys
import os
import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
from sklearn.metrics import classification_report, average_precision_score

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(PROJECT_ROOT, 'src'))

from data.loader import load_and_split_data
from data.preprocessor import Preprocessor
from utils.evaluation import calculate_fraud_savings, print_evaluation_report

DATA_PATH = os.path.join(PROJECT_ROOT, 'data', 'raw', 'creditcard.csv')
MODEL_DIR = os.path.join(PROJECT_ROOT, 'models')
os.makedirs(MODEL_DIR, exist_ok=True)

def train_xgboost():
    print("--- Starting XGBoost Training Pipeline ---")
    
    # 1. Load Data
    train_df, test_df = load_and_split_data(DATA_PATH, test_size=0.3)
    
    def split_features_target(df):
        X = df.drop('Class', axis=1)
        y = df['Class']
        return X, y

    X_train, y_train = split_features_target(train_df)
    X_test, y_test = split_features_target(test_df)
    amounts_test = X_test['Amount']
    
    # 2. Preprocess
    print("Preprocessing...")
    preprocessor = Preprocessor()
    X_train_processed = preprocessor.fit_transform(X_train)
    X_test_processed = preprocessor.transform(X_test)
    
    # 3. Train XGBoost
    # scale_pos_weight calculation: sum(negative) / sum(positive)
    # This guides the model to pay more attention to the minority class
    ratio = float(np.sum(y_train == 0)) / np.sum(y_train == 1)
    
    print(f"Training XGBoost (scale_pos_weight={ratio:.1f})...")
    
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=ratio,
        random_state=42,
        tree_method="hist",  # Faster
        eval_metric="logloss"
    )
    
    model.fit(X_train_processed, y_train)
    
    # 4. Threshold Tuning for PROFIT
    print("\n--- Tuning Threshold for Financial Impact ---")
    y_prob = model.predict_proba(X_test_processed)[:, 1]
    
    best_threshold = 0.5
    best_savings = -float('inf')
    best_report = {}
    
    # Search space: 0.50 up to 0.99 (because we have scale_pos_weight, probs will be skewed high)
    thresholds = np.arange(0.5, 0.99, 0.05)
    
    for thresh in thresholds:
        y_pred_thresh = (y_prob >= thresh).astype(int)
        fin = calculate_fraud_savings(y_test, y_pred_thresh, amounts_test)
        net = fin['net_savings']
        
        print(f"Thresh={thresh:.2f} | Net Savings=${net:,.2f} | FPS={int(fin['cost_of_false_alarms']/5)}")
        
        if net > best_savings:
            best_savings = net
            best_threshold = thresh
            best_report = fin
            
    print(f"\n>> BEST THRESHOLD: {best_threshold:.2f}")
    print(f">> MAX SAVINGS:    ${best_savings:,.2f}")
    
    # 5. Final Evaluation
    y_pred_final = (y_prob >= best_threshold).astype(int)
    print_evaluation_report(y_test, y_pred_final, y_prob, amounts=amounts_test)
    
    # Save model
    model_path = os.path.join(MODEL_DIR, 'xgboost_fraud.pkl')
    joblib.dump(model, model_path)
    print(f"Model saved to {model_path}")

if __name__ == "__main__":
    train_xgboost()
