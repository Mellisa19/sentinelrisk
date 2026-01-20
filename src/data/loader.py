import pandas as pd
import numpy as np
import os
from typing import Tuple

def load_and_split_data(filepath: str, test_size: float = 0.3) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Loads credit card data and splits it strictly chronologically.
    
    Args:
        filepath (str): Path to the CSV file.
        test_size (float): Proportion of dataset to include in the test split (last N%).
        
    Returns:
        train_df (pd.DataFrame): The earlier 70% of data.
        test_df (pd.DataFrame): The later 30% of data.
        
    Raises:
        ValueError: If data integrity checks fail.
    """
    df = load_data()
    if df is None:
        raise FileNotFoundError("Dataset not found")

    # --- MENTOR NOTE: The Critical Step ---
    # Most tutorials skip this, but in production, 'Time' is everything.
    # We explicitly sort by Time to ensure we simulate "Past vs Future".
    if 'Time' not in df.columns:
        raise ValueError("Dataset is missing the 'Time' column required for chronological splitting.")
        
    df = df.sort_values(by="Time").reset_index(drop=True)
    
    # Calculate split index
    split_index = int(len(df) * (1 - test_size))
    
    # Strict Slice
    train_df = df.iloc[:split_index].copy()
    test_df = df.iloc[split_index:].copy()
    
    # --- Integrity Checks ---
    # 1. Check for Overlap
    max_train_time = train_df['Time'].max()
    min_test_time = test_df['Time'].min()
    
    print(f"Split Summary:")
    print(f"Training Samples: {len(train_df)} (Ends at Time={max_train_time})")
    print(f"Test Samples:     {len(test_df)} (Starts at Time={min_test_time})")
    
    if max_train_time > min_test_time:
        # This should theoretically be impossible if sorted, but we verify anyway.
        raise ValueError("CRITICAL: Data Leakage detected! Future data found in training set.")
        
    if not (len(train_df) + len(test_df) == len(df)):
         raise ValueError("Split size mismatch! Data was lost during splitting.")

    return train_df, test_df

if __name__ == "__main__":
    # Quick test if run directly
    # Usage: python src/data/loader.py
    import sys
    # Hack to allow import relative to script location if needed, 
    # but here we just assume running from root
    path = "SentinelRisk/data/raw/creditcard.csv"
    try:
        train, test = load_and_split_data(path)
        print("SUCCESS: Data pipeline verification passed.")
    except Exception as e:
        print(f"FAILURE: {e}")
