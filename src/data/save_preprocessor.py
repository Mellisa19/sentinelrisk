import sys
import os
import joblib

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(PROJECT_ROOT, 'src'))

from data.loader import load_and_split_data
from data.preprocessor import Preprocessor

DATA_PATH = os.path.join(PROJECT_ROOT, 'data', 'raw', 'creditcard.csv')
MODEL_DIR = os.path.join(PROJECT_ROOT, 'models')
os.makedirs(MODEL_DIR, exist_ok=True)

def save_preprocessor():
    print("--- Saving Preprocessor (RobustScaler) ---")
    
    # 1. Load Data (Exact same split logic)
    print("Loading valid training split...")
    train_df, _ = load_and_split_data(DATA_PATH, test_size=0.3)
    
    X_train = train_df.drop('Class', axis=1)
    
    # 2. Fit Preprocessor
    print("Fitting Scaler on Training Data...")
    preprocessor = Preprocessor()
    preprocessor.fit_transform(X_train)
    
    # 3. Save
    path = os.path.join(MODEL_DIR, 'preprocessor.pkl')
    joblib.dump(preprocessor, path)
    print(f"Preprocessor saved to {path}")

if __name__ == "__main__":
    save_preprocessor()
