import pandas as pd
import numpy as np
import os
import sys

# Ensure we can find the data if running from notebooks dir
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_PATH = os.path.join(PROJECT_ROOT, 'data', 'raw', 'creditcard.csv')

def load_data(path):
    """
    Loads the credit card dataset.
    """
    if not os.path.exists(path):
        print(f"[ERROR] File not found at: {path}")
        print("Please download the dataset (e.g., from Kaggle) and place it in data/raw/")
        sys.exit(1)
    
    print(f"Loading data from {path}...")
    return pd.read_csv(path)

def analyze_structure(df):
    """
    Task 1 & 3: Print dimensions, column names, types, and missing values.
    """
    print("\n--- 1. Data Structure ---")
    print(f"Number of Transactions (Rows): {df.shape[0]}")
    print(f"Number of Columns: {df.shape[1]}")
    
    print("\n--- 3. Column Info & Missing Values ---")
    # Using info() for types and non-null counts
    df.info()
    
    print("\nMissing values per column:")
    print(df.isnull().sum()[df.isnull().sum() > 0]) # Only show columns with missing values

def show_samples(df):
    """
    Task 2: Show first 5 rows.
    """
    print("\n--- 2. First 5 Rows ---")
    print(df.head())

def analyze_class_imbalance(df):
    """
    Task 4: Count fraud vs non-fraud and calculate percentage.
    """
    print("\n--- 4. Class Imbalance Analysis ---")
    if 'Class' not in df.columns:
        print("[WARNING] 'Class' column not found!")
        return

    counts = df['Class'].value_counts()
    fraud_count = counts.get(1, 0)
    normal_count = counts.get(0, 0)
    total = fraud_count + normal_count
    fraud_pct = (fraud_count / total) * 100

    print(f"Normal Transactions (0): {normal_count}")
    print(f"Fraud Transactions (1):  {fraud_count}")
    print(f"Fraud Percentage:        {fraud_pct:.4f}%")
    
    if fraud_pct < 0.5:
        print(">> NOTICE: This is an extremely imbalanced dataset.")

def check_duplicates(df):
    """
    Task 5: Check for duplicate rows.
    """
    print("\n--- 5. Duplicate Check ---")
    num_duplicates = df.duplicated().sum()
    print(f"Number of duplicate rows: {num_duplicates}")
    if num_duplicates > 0:
        print(">> TIP: In fraud detection, duplicate rows might be real (same transaction submitted twice) or data errors. Always investigate.")

def main():
    print("Starting Initial Data Exploration...")
    
    # 1. Load
    df = load_data(DATA_PATH)
    
    # 2. Structure & Info
    analyze_structure(df)
    
    # 3. Head
    show_samples(df)
    
    # 4. Class Imbalance
    analyze_class_imbalance(df)
    
    # 5. Duplicates
    check_duplicates(df)

if __name__ == "__main__":
    main()
