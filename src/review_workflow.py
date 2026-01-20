from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from pydantic import BaseModel
import uuid
from enum import Enum

from services.db import ReviewQueue, PredictionLog, User
from monitoring import structured_logger


class ReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class ReviewPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReviewRequest(BaseModel):
    """Request for manual review"""
    prediction_log_id: int
    priority: ReviewPriority = ReviewPriority.MEDIUM
    notes: Optional[str] = None
    escalate_to_role: Optional[str] = None  # For escalation to higher role


class ReviewResponse(BaseModel):
    """Response to review request"""
    status: ReviewStatus
    notes: Optional[str] = None
    escalate_to: Optional[int] = None  # User ID to escalate to


class ReviewQueueManager:
    """Manage manual review queue for flagged transactions"""
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = structured_logger.logger
    
    def add_to_review_queue(self, prediction_log_id: int, priority: ReviewPriority = ReviewStatus.MEDIUM, notes: Optional[str] = None) -> ReviewQueue:
        """Add transaction to review queue"""
        
        # Check if already in queue
        existing = self.db.query(ReviewQueue).filter(
            ReviewQueue.prediction_log_id == prediction_log_id,
            ReviewQueue.status == ReviewStatus.PENDING
        ).first()
        
        if existing:
            self.logger.warning(f"Transaction {prediction_log_id} already in review queue")
            return existing
        
        # Create review queue entry
        review_item = ReviewQueue(
            prediction_log_id=prediction_log_id,
            status=ReviewStatus.PENDING,
            priority=priority.value,
            created_at=datetime.utcnow()
        )
        
        self.db.add(review_item)
        self.db.commit()
        self.db.refresh(review_item)
        
        self.logger.info(
            f"Added transaction {prediction_log_id} to review queue with priority {priority.value}",
            extra={"review_id": review_item.id, "priority": priority.value}
        )
        
        return review_item
    
    def get_pending_reviews(self, reviewer_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get pending reviews for a reviewer"""
        
        reviews = self.db.query(ReviewQueue, PredictionLog, User).join(
            PredictionLog, ReviewQueue.prediction_log_id == PredictionLog.id
        ).join(
            User, PredictionLog.user_id == User.id
        ).filter(
            ReviewQueue.status == ReviewStatus.PENDING,
            ReviewQueue.reviewer_id.is_(None)
        ).order_by(
            ReviewQueue.priority.desc(),
            ReviewQueue.created_at.asc()
        ).limit(limit).all()
        
        result = []
        for review, prediction_log, user in reviews:
            result.append({
                "review_id": review.id,
                "prediction_log_id": prediction_log.id,
                "priority": review.priority,
                "created_at": review.created_at,
                "transaction": {
                    "amount": prediction_log.amount,
                    "risk_score": prediction_log.risk_score,
                    "decision": prediction_log.decision,
                    "explanation": prediction_log.explanation,
                    "timestamp": prediction_log.timestamp,
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "role": user.role
                    }
                }
            })
        
        return result
    
    def assign_review(self, review_id: int, reviewer_id: int) -> ReviewQueue:
        """Assign a review to a specific reviewer"""
        
        review = self.db.query(ReviewQueue).filter(ReviewQueue.id == review_id).first()
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found"
            )
        
        if review.status != ReviewStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Review is not pending (current status: {review.status})"
            )
        
        if review.reviewer_id and review.reviewer_id != reviewer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Review is already assigned to another reviewer"
            )
        
        review.reviewer_id = reviewer_id
        review.status = ReviewStatus.PENDING  # Still pending but now assigned
        self.db.commit()
        
        self.logger.info(
            f"Assigned review {review_id} to reviewer {reviewer_id}",
            extra={"review_id": review_id, "reviewer_id": reviewer_id}
        )
        
        return review
    
    def complete_review(self, review_id: int, reviewer_id: int, response: ReviewResponse) -> ReviewQueue:
        """Complete a review with decision"""
        
        review = self.db.query(ReviewQueue).filter(ReviewQueue.id == review_id).first()
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found"
            )
        
        if review.reviewer_id != reviewer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Review not assigned to this reviewer"
            )
        
        if review.status != ReviewStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Review is not pending (current status: {review.status})"
            )
        
        # Update review
        review.status = response.status
        review.review_notes = response.notes
        review.reviewed_at = datetime.utcnow()
        
        # Handle escalation
        if response.status == ReviewStatus.ESCALATED and response.escalate_to:
            review.reviewer_id = response.escalate_to
            review.status = ReviewStatus.PENDING  # Reset to pending for new reviewer
        
        self.db.commit()
        
        self.logger.info(
            f"Completed review {review_id} with status {response.status}",
            extra={
                "review_id": review_id,
                "reviewer_id": reviewer_id,
                "status": response.status,
                "notes": response.notes
            }
        )
        
        return review
    
    def get_review_statistics(self, reviewer_id: Optional[int] = None) -> Dict[str, Any]:
        """Get review queue statistics"""
        
        base_query = self.db.query(ReviewQueue)
        if reviewer_id:
            base_query = base_query.filter(ReviewQueue.reviewer_id == reviewer_id)
        
        # Status counts
        pending_count = base_query.filter(ReviewQueue.status == ReviewStatus.PENDING).count()
        approved_count = base_query.filter(ReviewQueue.status == ReviewStatus.APPROVED).count()
        rejected_count = base_query.filter(ReviewQueue.status == ReviewStatus.REJECTED).count()
        escalated_count = base_query.filter(ReviewQueue.status == ReviewStatus.ESCALATED).count()
        
        # Priority breakdown
        priority_counts = {}
        for priority in ReviewPriority:
            count = base_query.filter(
                ReviewQueue.priority == priority.value,
                ReviewQueue.status == ReviewStatus.PENDING
            ).count()
            priority_counts[priority.value] = count
        
        # Average review time
        completed_reviews = base_query.filter(
            ReviewQueue.reviewed_at.isnot(None),
            ReviewQueue.created_at.isnot(None)
        ).all()
        
        avg_review_time = 0
        if completed_reviews:
            total_time = sum(
                (r.reviewed_at - r.created_at).total_seconds()
                for r in completed_reviews
            )
            avg_review_time = total_time / len(completed_reviews) / 3600  # Convert to hours
        
        return {
            "queue_stats": {
                "pending": pending_count,
                "approved": approved_count,
                "rejected": rejected_count,
                "escalated": escalated_count
            },
            "priority_breakdown": priority_counts,
            "average_review_time_hours": round(avg_review_time, 2),
            "total_completed": approved_count + rejected_count
        }


class AutoReviewRules:
    """Automatic rules for determining which transactions need review"""
    
    @staticmethod
    def should_auto_review(prediction_data: Dict[str, Any]) -> tuple[bool, ReviewPriority, str]:
        """Determine if transaction should be auto-reviewed"""
        
        risk_score = prediction_data.get('risk_score', 0)
        amount = prediction_data.get('amount', 0)
        decision = prediction_data.get('decision', '')
        
        # High risk score
        if risk_score > 0.8:
            return True, ReviewPriority.CRITICAL, f"Very high risk score: {risk_score:.3f}"
        
        # Medium-high risk with high amount
        if risk_score > 0.6 and amount > 5000:
            return True, ReviewPriority.HIGH, f"High risk score ({risk_score:.3f}) with high amount (${amount})"
        
        # Block decisions always get reviewed
        if decision == "BLOCK":
            return True, ReviewPriority.MEDIUM, "Transaction was blocked"
        
        # Review decisions with notable risk
        if decision == "REVIEW" and risk_score > 0.3:
            return True, ReviewPriority.MEDIUM, f"Review decision with moderate risk ({risk_score:.3f})"
        
        # Very high amounts regardless of risk score
        if amount > 50000:
            return True, ReviewPriority.HIGH, f"High value transaction: ${amount}"
        
        return False, ReviewPriority.LOW, ""


class ReviewNotificationService:
    """Service for sending review notifications"""
    
    def __init__(self):
        self.logger = structured_logger.logger
    
    def notify_reviewer(self, reviewer_id: int, review_data: Dict[str, Any]):
        """Send notification to reviewer"""
        
        self.logger.info(
            f"Notification sent to reviewer {reviewer_id}",
            extra={
                "reviewer_id": reviewer_id,
                "review_id": review_data.get("review_id"),
                "priority": review_data.get("priority"),
                "amount": review_data.get("transaction", {}).get("amount")
            }
        )
        
        # In production, this would integrate with:
        # - Email service
        # - Slack/Teams notifications
        # - SMS for critical reviews
        # - Push notifications
    
    def notify_escalation(self, escalate_to_id: int, original_reviewer_id: int, review_data: Dict[str, Any]):
        """Send escalation notification"""
        
        self.logger.warning(
            f"Review escalated from reviewer {original_reviewer_id} to {escalate_to_id}",
            extra={
                "escalate_to": escalate_to_id,
                "original_reviewer": original_reviewer_id,
                "review_id": review_data.get("review_id"),
                "priority": review_data.get("priority")
            }
        )
