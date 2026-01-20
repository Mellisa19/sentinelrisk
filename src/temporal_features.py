from datetime import datetime
import pandas as pd
import numpy as np
from typing import Dict, Any


class TemporalFeatureProcessor:
    """Process temporal features for fraud detection"""
    
    @staticmethod
    def extract_temporal_features(transaction_timestamp: datetime) -> Dict[str, Any]:
        """Extract meaningful temporal features from timestamp"""
        
        # Basic temporal features
        features = {
            'hour_of_day': transaction_timestamp.hour,
            'day_of_week': transaction_timestamp.weekday(),  # 0=Monday, 6=Sunday
            'day_of_month': transaction_timestamp.day,
            'month': transaction_timestamp.month,
            'year': transaction_timestamp.year,
            'is_weekend': transaction_timestamp.weekday() >= 5,  # Saturday, Sunday
            'is_night': transaction_timestamp.hour < 6 or transaction_timestamp.hour > 22,
            'is_business_hours': 9 <= transaction_timestamp.hour <= 17,
        }
        
        # Advanced temporal features
        features.update({
            'time_of_day_category': TemporalFeatureProcessor._get_time_of_day(transaction_timestamp.hour),
            'season': TemporalFeatureProcessor._get_season(transaction_timestamp.month),
            'quarter': (transaction_timestamp.month - 1) // 3 + 1,
            'week_of_year': transaction_timestamp.isocalendar()[1],
        })
        
        return features
    
    @staticmethod
    def _get_time_of_day(hour: int) -> str:
        """Categorize time of day"""
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 22:
            return "evening"
        else:
            return "night"
    
    @staticmethod
    def _get_season(month: int) -> str:
        """Get season from month"""
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "autumn"
    
    @staticmethod
    def create_time_based_features(df: pd.DataFrame, timestamp_col: str = 'transaction_timestamp') -> pd.DataFrame:
        """Create time-based features for a DataFrame"""
        
        df = df.copy()
        
        # Ensure timestamp column is datetime
        df[timestamp_col] = pd.to_datetime(df[timestamp_col])
        
        # Extract temporal features
        df['hour_of_day'] = df[timestamp_col].dt.hour
        df['day_of_week'] = df[timestamp_col].dt.weekday
        df['day_of_month'] = df[timestamp_col].dt.day
        df['month'] = df[timestamp_col].dt.month
        df['year'] = df[timestamp_col].dt.year
        df['is_weekend'] = df[timestamp_col].dt.weekday >= 5
        df['is_night'] = (df[timestamp_col].dt.hour < 6) | (df[timestamp_col].dt.hour > 22)
        df['is_business_hours'] = (df[timestamp_col].dt.hour >= 9) & (df[timestamp_col].dt.hour <= 17)
        
        # Cyclical features for better ML performance
        df['hour_sin'] = np.sin(2 * np.pi * df['hour_of_day'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour_of_day'] / 24)
        df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        
        return df
    
    @staticmethod
    def detect_anomalous_time_patterns(transaction_timestamp: datetime, user_history: list = None) -> list:
        """Detect anomalous time patterns in transactions"""
        
        anomalies = []
        current_features = TemporalFeatureProcessor.extract_temporal_features(transaction_timestamp)
        
        # Check for unusual hours
        if current_features['is_night']:
            anomalies.append("Transaction during unusual night hours")
        
        # Check for weekend transactions (might be unusual for business accounts)
        if current_features['is_weekend']:
            anomalies.append("Weekend transaction")
        
        # If user history is available, check for deviations
        if user_history and len(user_history) > 5:
            user_hours = [ts.hour for ts in user_history]
            user_hour_std = np.std(user_hours)
            
            if user_hour_std < 2 and abs(transaction_timestamp.hour - np.mean(user_hours)) > 4:
                anomalies.append("Transaction time deviates from user's normal pattern")
        
        return anomalies


class ProductionPreprocessor:
    """Production-ready preprocessor that handles temporal features properly"""
    
    def __init__(self, original_preprocessor):
        """Wrap the original preprocessor with temporal feature handling"""
        self.original_preprocessor = original_preprocessor
        self.temporal_processor = TemporalFeatureProcessor()
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform data with proper temporal feature handling"""
        
        # Check if we have the old 'Time' column or new timestamp
        if 'transaction_timestamp' in df.columns:
            # New format: extract temporal features from timestamp
            df = self.temporal_processor.create_time_based_features(df, 'transaction_timestamp')
            
            # For backward compatibility with the model, create a synthetic Time column
            # Use seconds since midnight instead of since first transaction
            df['Time'] = (df['transaction_timestamp'].dt.hour * 3600 + 
                         df['transaction_timestamp'].dt.minute * 60 + 
                         df['transaction_timestamp'].dt.second)
            
        elif 'Time' in df.columns:
            # Legacy format: keep existing Time column but add temporal features
            # Convert Time (seconds since first transaction) to approximate timestamp
            # This is a rough approximation for backward compatibility
            base_timestamp = datetime(2023, 1, 1)  # Arbitrary base date
            df['transaction_timestamp'] = base_timestamp + pd.to_timedelta(df['Time'], unit='s')
            df = self.temporal_processor.create_time_based_features(df, 'transaction_timestamp')
        
        # Apply original preprocessing
        processed_df = self.original_preprocessor.transform(df)
        
        return processed_df


def create_production_preprocessor(original_preprocessor_path: str) -> ProductionPreprocessor:
    """Create a production preprocessor from the original one"""
    
    import joblib
    original_preprocessor = joblib.load(original_preprocessor_path)
    return ProductionPreprocessor(original_preprocessor)
