import sys
import os
import joblib
import pandas as pd
import time
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session

# Import our production modules
from config import settings
from auth import (
    authenticate_user, create_access_token, get_current_active_user, 
    require_role, Token, UserCreate, UserResponse, get_password_hash
)
from validation import TransactionRequest, BatchTransactionRequest, UserCreate as UserCreateValidation
from security import add_security_headers, InputValidator, limiter
from monitoring import structured_logger, model_monitor
from review_workflow import ReviewQueueManager, AutoReviewRules, ReviewPriority, ReviewStatus
from services.db import get_db, init_db, PredictionLog, User

# Configure application
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(PROJECT_ROOT, 'src'))

# Import Preprocessor class and temporal features
from data.preprocessor import Preprocessor
from temporal_features import create_production_preprocessor

# Initialize FastAPI with production settings
app = FastAPI(
    title="SentinelRisk Fraud Detection API",
    version="2.0.0",
    description="Production-ready fraud detection system with authentication and monitoring"
)

# Add security middleware
app = add_security_headers(app)

# Add rate limiting exception handler
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Enable CORS with production settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Paths
MODEL_PATH = os.path.join(PROJECT_ROOT, settings.MODEL_PATH)
PREPROCESSOR_PATH = os.path.join(PROJECT_ROOT, settings.PREPROCESSOR_PATH)

# Global variables
model = None
preprocessor = None


@app.on_event("startup")
async def load_artifacts():
    """Load model artifacts and initialize database"""
    global model, preprocessor
    
    try:
        structured_logger.logger.info("Initializing production database...")
        init_db()
        
        structured_logger.logger.info("Loading ML model and production preprocessor...")
        if not os.path.exists(MODEL_PATH) or not os.path.exists(PREPROCESSOR_PATH):
            raise FileNotFoundError("Model or preprocessor files missing!")
        
        model = joblib.load(MODEL_PATH)
        
        # Use production preprocessor that handles temporal features properly
        preprocessor = create_production_preprocessor(PREPROCESSOR_PATH)
        
        structured_logger.logger.info("Production system initialized successfully")
        structured_logger.logger.info("Temporal feature processing enabled - deprecated 'Time' field replaced")
        
    except Exception as e:
        structured_logger.log_error(e, {"context": "startup"})
        raise e


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing"""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    structured_logger.log_request(request, response, process_time)
    
    return response


def get_decision(risk_score: float) -> tuple[str, str]:
    """Enhanced decision logic with more granular thresholds"""
    if risk_score > 0.85:
        return "BLOCK", "Very high fraud risk detected"
    elif risk_score > 0.65:
        return "REVIEW", "High fraud risk - manual review required"
    elif risk_score > 0.35:
        return "REVIEW", "Moderate fraud risk - review recommended"
    else:
        return "APPROVE", "Low fraud risk"


# Authentication endpoints
@app.post("/auth/login", response_model=Token)
@limiter.limit("5/minute")
async def login(request: Request, username: str, password: str, db: Session = Depends(get_db)):
    """User authentication endpoint"""
    
    user = authenticate_user(db, username, password)
    if not user:
        structured_logger.log_security_event("failed_login", {
            "username": username,
            "ip": request.client.host if request.client else None
        })
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )
    
    access_token_expires = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    structured_logger.logger.info(
        f"User {username} logged in successfully",
        extra={"user_id": user.id, "ip": request.client.host if request.client else None}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/auth/register", response_model=UserResponse)
@limiter.limit("3/minute")
async def register(
    request: Request, 
    user_data: UserCreateValidation, 
    db: Session = Depends(get_db)
):
    """User registration endpoint"""
    
    # Check if user exists
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username or email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role=user_data.role
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    structured_logger.logger.info(
        f"New user registered: {user_data.username}",
        extra={"user_id": db_user.id, "role": user_data.role}
    )
    
    return db_user


# Prediction endpoints
@app.post("/predict")
@limiter.limit("100/minute")
async def predict_fraud(
    request: Request,
    transaction: TransactionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Enhanced fraud prediction with user tracking and auto-review"""
    
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    if not model or not preprocessor:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Validate input
        InputValidator.validate_transaction_amount(transaction.Amount)
        
        # Convert to DataFrame
        data = transaction.dict()
        df = pd.DataFrame([data])
        
        # Preprocess
        X_processed = preprocessor.transform(df)
        
        # Reorder columns to match training
        feature_order = [f"V{i}" for i in range(1, 29)] + ["Amount", "Hour"]
        X_processed = X_processed[feature_order]
        
        # Predict
        risk_score = float(model.predict_proba(X_processed)[0][1])
        
        # Decision logic
        decision, explanation = get_decision(risk_score)
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000
        
        # Create prediction log
        prediction_log = PredictionLog(
            request_id=request_id,
            user_id=current_user.id,
            amount=transaction.Amount,
            risk_score=risk_score,
            decision=decision,
            explanation=explanation,
            is_simulated=transaction.is_simulated
        )
        
        db.add(prediction_log)
        db.commit()
        db.refresh(prediction_log)
        
        # Check for auto-review
        prediction_data = {
            "risk_score": risk_score,
            "amount": transaction.Amount,
            "decision": decision,
            "explanation": explanation
        }
        
        should_review, priority, reason = AutoReviewRules.should_auto_review(prediction_data)
        
        if should_review:
            review_manager = ReviewQueueManager(db)
            review_manager.add_to_review_queue(
                prediction_log.id, 
                priority, 
                f"Auto-review: {reason}"
            )
        
        # Log prediction
        structured_logger.log_prediction({
            "decision": decision,
            "risk_score": risk_score,
            "amount": transaction.Amount,
            "request_id": request_id,
            "user_id": current_user.id,
            "processing_time_ms": processing_time,
            "auto_review": should_review
        })
        
        # Update model monitor
        model_monitor.record_prediction(risk_score, decision)
        
        return {
            "risk_score": risk_score,
            "decision": decision,
            "explanation": explanation,
            "request_id": request_id,
            "processing_time_ms": processing_time,
            "auto_review_queued": should_review
        }
        
    except Exception as e:
        structured_logger.log_error(e, {
            "request_id": request_id,
            "user_id": current_user.id,
            "transaction_amount": transaction.Amount
        })
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/batch")
@limiter.limit("10/minute")
async def predict_batch(
    request: Request,
    batch: BatchTransactionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Batch prediction for multiple transactions"""
    
    results = []
    batch_id = str(uuid.uuid4())
    
    for i, transaction in enumerate(batch.transactions):
        try:
            # Use single prediction logic
            result = await predict_fraud(
                request, transaction, background_tasks, current_user, db
            )
            results.append({
                "index": i,
                "success": True,
                "result": result
            })
        except Exception as e:
            results.append({
                "index": i,
                "success": False,
                "error": str(e)
            })
    
    structured_logger.logger.info(
        f"Batch prediction completed: {len(results)} transactions",
        extra={
            "batch_id": batch_id,
            "user_id": current_user.id,
            "total_transactions": len(batch.transactions),
            "successful_predictions": sum(1 for r in results if r["success"])
        }
    )
    
    return {
        "batch_id": batch_id,
        "total_transactions": len(batch.transactions),
        "results": results
    }


# Review workflow endpoints
@app.get("/reviews/pending")
async def get_pending_reviews(
    request: Request,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get pending reviews for current user"""
    
    # Check user permissions
    if current_user.role not in ["reviewer", "admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    review_manager = ReviewQueueManager(db)
    pending_reviews = review_manager.get_pending_reviews(current_user.id, limit)
    
    return {
        "pending_reviews": pending_reviews,
        "total_pending": len(pending_reviews)
    }


@app.post("/reviews/{review_id}/assign")
async def assign_review(
    request: Request,
    review_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Assign a review to yourself"""
    
    if current_user.role not in ["reviewer", "admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    review_manager = ReviewQueueManager(db)
    review = review_manager.assign_review(review_id, current_user.id)
    
    return {"message": "Review assigned successfully", "review_id": review.id}


@app.post("/reviews/{review_id}/complete")
async def complete_review(
    request: Request,
    review_id: int,
    response_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Complete a review with decision"""
    
    if current_user.role not in ["reviewer", "admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    from review_workflow import ReviewResponse
    review_response = ReviewResponse(
        status=response_data.get("status", ReviewStatus.APPROVED),
        notes=response_data.get("notes"),
        escalate_to=response_data.get("escalate_to")
    )
    
    review_manager = ReviewQueueManager(db)
    review = review_manager.complete_review(review_id, current_user.id, review_response)
    
    return {"message": "Review completed successfully", "review_id": review.id}


# Monitoring endpoints
@app.get("/metrics")
@limiter.limit("60/minute")
async def get_metrics(
    request: Request,
    hours: int = 24,
    current_user: User = Depends(get_current_active_user)
):
    """Get system metrics"""
    
    if current_user.role not in ["admin", "reviewer"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Get model monitoring stats
    model_stats = model_monitor.get_stats()
    
    return {
        "window_hours": hours,
        "model_performance": model_stats,
        "system_health": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "model_loaded": model is not None,
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "SentinelRisk Fraud Detection API v2.0.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/health"
    }
