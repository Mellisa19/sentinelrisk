import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base
from config import settings

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DB_PATH = os.path.join(PROJECT_ROOT, 'data', 'sentinelrisk.db')

# Connection String
# Support both SQLite (development) and PostgreSQL (production)
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Configure engine based on database type
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, 
        connect_args={"check_same_thread": False},
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW
    )
else:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW
    )
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class User(Base):
    """User authentication and authorization"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(String, default="analyst")  # analyst, admin, reviewer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)


class PredictionLog(Base):
    """
    Audit Trail for every fraud prediction.
    Stores WHO (Request ID), WHEN (Timestamp), WHAT (Input), and RESULT (Score/Decision).
    """
    __tablename__ = "prediction_logs"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, index=True, unique=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user_id = Column(Integer, index=True)  # Link to user who made the request
    
    # Input Features (Key ones for audit)
    amount = Column(Float)
    
    # Model Output
    risk_score = Column(Float)
    decision = Column(String, index=True)  # APPROVE / REVIEW / BLOCK
    explanation = Column(String)
    is_simulated = Column(Integer, default=0) # 1 for demo traffic, 0 for user traffic


class ReviewQueue(Base):
    """Manual review queue for flagged transactions"""
    __tablename__ = "review_queue"

    id = Column(Integer, primary_key=True, index=True)
    prediction_log_id = Column(Integer, index=True)
    reviewer_id = Column(Integer, index=True)
    status = Column(String, default="pending")  # pending, approved, rejected
    review_notes = Column(String)
    reviewed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    """Initialize database with all tables"""
    print(f"Initializing Database at {SQLALCHEMY_DATABASE_URL}")
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables created/verified successfully")
    except Exception as e:
        print(f"Database initialization warning: {e}")
        # Continue even if tables already exist
