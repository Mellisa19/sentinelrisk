import sys
import os
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
import joblib

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(PROJECT_ROOT, 'src'))

from data.loader import load_and_split_data
from data.preprocessor import Preprocessor
from utils.evaluation import print_evaluation_report

DATA_PATH = os.path.join(PROJECT_ROOT, 'data', 'raw', 'creditcard.csv')
MODEL_DIR = os.path.join(PROJECT_ROOT, 'models')
os.makedirs(MODEL_DIR, exist_ok=True)

def train_baseline():
    print("--- Starting Baseline Training Pipeline ---")
    
    # 1. Load Data (Strict Chronological Split)
    train_df, test_df = load_and_split_data(DATA_PATH, test_size=0.3)
    
    # 2. Preprocess
    # We need to separate X and y. 
    # NOTE: Helper function to split features/target
    def split_features_target(df):
        X = df.drop('Class', axis=1)
        y = df['Class']
        return X, y

    X_train, y_train = split_features_target(train_df)
    X_test, y_test = split_features_target(test_df)
    
    # Save 'Amount' for financial evaluation later
    amounts_test = X_test['Amount']
    
    print("Initializing Preprocessor...")
    preprocessor = Preprocessor()
    
    print("Transforming Data...")
    X_train_processed = preprocessor.fit_transform(X_train)
    X_test_processed = preprocessor.transform(X_test)
    
    # 3. Train Model
    # Using class_weight='balanced' to handle the 0.17% imbalance automatically
    print("Training Logistic Regression (class_weight='balanced')...")
    model = LogisticRegression(class_weight='balanced', random_state=42, max_iter=1000)
    model.fit(X_train_processed, y_train)
    
    # 4. Evaluate
    print("Predicting on Test Set...")
    y_pred = model.predict(X_test_processed)
    y_prob = model.predict_proba(X_test_processed)[:, 1]
    
    print_evaluation_report(y_test, y_pred, y_prob, amounts=amounts_test)
    
    # 5. Save
    model_path = os.path.join(MODEL_DIR, 'baseline_lr.pkl')
    joblib.dump(model, model_path)
    print(f"\nModel saved to {model_path}")

if __name__ == "__main__":
    train_baseline()
