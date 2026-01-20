from pydantic import BaseModel, Field, validator
from typing import Optional, List
import re
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import pandas as pd


class TransactionRequest(BaseModel):
    """Enhanced transaction request with comprehensive validation"""
    
    # Required fields with proper temporal features
    transaction_timestamp: datetime = Field(..., description="Actual transaction timestamp")
    Amount: float = Field(..., gt=0, le=1000000, description="Transaction amount (max $1M)")
    
    # Temporal features (derived from timestamp in preprocessing)
    hour_of_day: Optional[int] = Field(None, ge=0, le=23, description="Hour of day (0-23)")
    day_of_week: Optional[int] = Field(None, ge=0, le=6, description="Day of week (0-6)")
    is_weekend: Optional[bool] = Field(None, description="Whether transaction occurred on weekend")
    
    # PCA features V1-V28
    V1: float = Field(..., ge=-100, le=100)
    V2: float = Field(..., ge=-100, le=100)
    V3: float = Field(..., ge=-100, le=100)
    V4: float = Field(..., ge=-100, le=100)
    V5: float = Field(..., ge=-100, le=100)
    V6: float = Field(..., ge=-100, le=100)
    V7: float = Field(..., ge=-100, le=100)
    V8: float = Field(..., ge=-100, le=100)
    V9: float = Field(..., ge=-100, le=100)
    V10: float = Field(..., ge=-100, le=100)
    V11: float = Field(..., ge=-100, le=100)
    V12: float = Field(..., ge=-100, le=100)
    V13: float = Field(..., ge=-100, le=100)
    V14: float = Field(..., ge=-100, le=100)
    V15: float = Field(..., ge=-100, le=100)
    V16: float = Field(..., ge=-100, le=100)
    V17: float = Field(..., ge=-100, le=100)
    V18: float = Field(..., ge=-100, le=100)
    V19: float = Field(..., ge=-100, le=100)
    V20: float = Field(..., ge=-100, le=100)
    V21: float = Field(..., ge=-100, le=100)
    V22: float = Field(..., ge=-100, le=100)
    V23: float = Field(..., ge=-100, le=100)
    V24: float = Field(..., ge=-100, le=100)
    V25: float = Field(..., ge=-100, le=100)
    V26: float = Field(..., ge=-100, le=100)
    V27: float = Field(..., ge=-100, le=100)
    V28: float = Field(..., ge=-100, le=100)
    
    # Optional metadata
    merchant_id: Optional[str] = Field(None, max_length=50)
    customer_id: Optional[str] = Field(None, max_length=50)
    device_id: Optional[str] = Field(None, max_length=100)
    ip_address: Optional[str] = Field(None, max_length=45)
    merchant_category: Optional[str] = Field(None, max_length=50)
    transaction_type: Optional[str] = Field(None, max_length=20)  # online, in_store, atm
    
    # Simulation flag
    is_simulated: int = Field(0, ge=0, le=1, description="1 if simulated, 0 if real")
    
    @validator('transaction_timestamp')
    def validate_timestamp(cls, v):
        """Validate transaction timestamp is reasonable"""
        now = datetime.utcnow()
        
        # Transaction shouldn't be too far in future (more than 5 minutes)
        if v > now + timedelta(minutes=5):
            raise ValueError("Transaction timestamp is too far in the future")
        
        # Transaction shouldn't be too old (more than 30 days)
        if v < now - timedelta(days=30):
            raise ValueError("Transaction timestamp is too old")
        
        return v
    
    @validator('transaction_type')
    def validate_transaction_type(cls, v):
        """Validate transaction type"""
        if v is not None:
            valid_types = ['online', 'in_store', 'atm', 'mobile', 'recurring']
            if v not in valid_types:
                raise ValueError(f"Transaction type must be one of: {valid_types}")
        return v
    
    @validator('merchant_id', 'customer_id', 'device_id')
    def sanitize_string_fields(cls, v):
        if v is not None:
            # Remove any potentially harmful characters
            v = re.sub(r'[<>"\';]', '', v)
            # Check for SQL injection patterns
            if re.search(r'(union|select|insert|update|delete|drop|create|alter)', v, re.IGNORECASE):
                raise ValueError("Invalid characters detected")
        return v
    
    @validator('ip_address')
    def validate_ip_address(cls, v):
        if v is not None:
            # Basic IP validation
            ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
            if not re.match(ip_pattern, v):
                # Check for IPv6 pattern (simplified)
                ipv6_pattern = r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
                if not re.match(ipv6_pattern, v):
                    raise ValueError("Invalid IP address format")
        return v
    
    @validator('Time')
    def validate_time_range(cls, v):
        # Time should be reasonable (not too far in future/past)
        current_time = datetime.now().timestamp()
        if v > current_time + 3600:  # More than 1 hour in future
            raise ValueError("Time value is too far in the future")
        if v < current_time - 86400 * 365:  # More than 1 year in past
            raise ValueError("Time value is too far in the past")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "transaction_timestamp": "2024-01-19T14:30:00Z",
                "Amount": 100.0,
                "hour_of_day": 14,
                "day_of_week": 4,
                "is_weekend": False,
                "V1": 0.1,
                "V2": 0.2,
                "V3": 0.3,
                "V4": 0.4,
                "V5": 0.5,
                "V6": 0.6,
                "V7": 0.7,
                "V8": 0.8,
                "V9": 0.9,
                "V10": 0.1,
                "V11": 0.2,
                "V12": 0.3,
                "V13": 0.4,
                "V14": 0.5,
                "V15": 0.6,
                "V16": 0.7,
                "V17": 0.8,
                "V18": 0.9,
                "V19": 0.1,
                "V20": 0.2,
                "V21": 0.3,
                "V22": 0.4,
                "V23": 0.5,
                "V24": 0.6,
                "V25": 0.7,
                "V26": 0.8,
                "V27": 0.9,
                "V28": 0.1,
                "merchant_id": "merchant_123",
                "customer_id": "customer_456",
                "merchant_category": "electronics",
                "transaction_type": "online",
                "is_simulated": 0
            }
        }


class BatchTransactionRequest(BaseModel):
    """Batch transaction processing with validation"""
    
    transactions: List[TransactionRequest] = Field(..., min_items=1, max_items=100)
    
    @validator('transactions')
    def validate_batch_size(cls, v):
        if len(v) > 100:
            raise ValueError("Batch size cannot exceed 100 transactions")
        return v


class UserCreate(BaseModel):
    """User creation with validation"""
    
    username: str = Field(..., min_length=3, max_length=50, regex=r'^[a-zA-Z0-9_]+$')
    email: str = Field(..., regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=100)
    role: str = Field("analyst", regex=r'^(analyst|admin|reviewer)$')
    
    @validator('password')
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # Check for password strength
        if not re.search(r'[A-Z]', v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', v):
            raise ValueError("Password must contain at least one digit")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")
        
        return v


class DataSanitizer:
    """Utility class for data sanitization"""
    
    @staticmethod
    def sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Sanitize pandas DataFrame"""
        # Remove any NaN values
        df = df.dropna()
        
        # Check for infinite values
        df = df.replace([float('inf'), -float('inf')], float('nan'))
        df = df.dropna()
        
        # Validate numeric ranges
        for col in df.select_dtypes(include=['float64', 'int64']).columns:
            if col.startswith('V'):
                # PCA features should be within reasonable bounds
                df[col] = df[col].clip(-100, 100)
            elif col == 'Amount':
                df[col] = df[col].clip(0.01, 1000000)
        
        return df
    
    @staticmethod
    def detect_anomalies(transaction_data: dict) -> List[str]:
        """Detect potential anomalies in transaction data"""
        anomalies = []
        
        # Check for unusual amounts
        amount = transaction_data.get('Amount', 0)
        if amount > 10000:
            anomalies.append("High value transaction")
        
        # Check for unusual time patterns
        time_val = transaction_data.get('Time', 0)
        if time_val % 3600 < 300:  # Within 5 minutes of hour mark
            anomalies.append("Round time pattern")
        
        # Check for feature values at extremes
        for i in range(1, 29):
            v_val = transaction_data.get(f'V{i}', 0)
            if abs(v_val) > 50:
                anomalies.append(f"Extreme V{i} value")
        
        return anomalies


class SecurityValidator:
    """Security-focused validation"""
    
    @staticmethod
    def check_rate_limit(user_id: int, request_count: int, time_window: int) -> bool:
        """Check if user exceeds rate limit"""
        # This would integrate with Redis for distributed rate limiting
        max_requests = 1000 if user_id else 100  # Authenticated users get higher limits
        return request_count <= max_requests
    
    @staticmethod
    def detect_suspicious_patterns(transaction_data: dict, user_history: List[dict]) -> List[str]:
        """Detect suspicious patterns based on user history"""
        patterns = []
        
        if not user_history:
            return patterns
        
        # Check for unusual amounts compared to user's average
        amounts = [t.get('Amount', 0) for t in user_history]
        if amounts:
            avg_amount = sum(amounts) / len(amounts)
            current_amount = transaction_data.get('Amount', 0)
            
            if current_amount > avg_amount * 10:
                patterns.append("Amount significantly higher than usual")
        
        # Check for rapid transactions
        if len(user_history) > 5:
            recent_times = [t.get('Time', 0) for t in user_history[-5:]]
            if max(recent_times) - min(recent_times) < 60:  # 5 transactions in < 60 seconds
                patterns.append("Rapid transaction pattern")
        
        return patterns
