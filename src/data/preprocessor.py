from sklearn.preprocessing import RobustScaler
import pandas as pd
import numpy as np

class Preprocessor:
    def __init__(self):
        self.scaler = RobustScaler()
        self.fitted = False

    def fit_transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Fits the scaler on the training data and transforms it.
        We only scale 'Amount' and 'Time' (if present), or just 'Amount'.
        """
        X = X.copy()
        
        # Scale Amount - Critical because range is 0-25000 vs V-features 0-1
        # RobustScaler is better for outliers
        if 'Amount' in X.columns:
            X['Amount'] = self.scaler.fit_transform(X[['Amount']])
            
        # Time needs to be handled.
        # Check if Time is present
        if 'Time' in X.columns:
            # Simple feature engineering: Hour of day
            # Assuming Time is in seconds. 3600s = 1h.
            # We will replace 'Time' with 'Hour' which is cyclic or just 0-23
            X['Hour'] = (X['Time'] / 3600) % 24
            # Drop original Time as it is unbound and risky for LR
            X = X.drop('Time', axis=1)
            
        self.fitted = True
        return X

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms test data using fitted scaler.
        """
        if not self.fitted:
            raise ValueError("Preprocessor must be fitted before calling transform!")
            
        X = X.copy()
        
        if 'Amount' in X.columns:
            X['Amount'] = self.scaler.transform(X[['Amount']])
            
        if 'Time' in X.columns:
             X['Hour'] = (X['Time'] / 3600) % 24
             X = X.drop('Time', axis=1)
             
        return X
