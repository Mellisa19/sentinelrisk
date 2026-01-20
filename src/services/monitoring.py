from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from services.db import PredictionLog, SessionLocal

def get_monitoring_stats(hours: int = 24):
    """
    Aggregates statistics from the last `hours`.
    Returns:
        dict: {
            "window_hours": int,
            "total_requests": int,
            "avg_risk_score": float,
            "decisions": { "APPROVE": int, "REVIEW": int, "BLOCK": int },
            "alerts": list[str]
        }
    """
    db: Session = SessionLocal()
    try:
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # Base Query
        query = db.query(PredictionLog).filter(PredictionLog.timestamp >= since)
        
        # 1. Total Requests
        total = query.count()
        if total == 0:
            return {
                "window_hours": hours,
                "total_requests": 0,
                "avg_risk_score": 0.0,
                "decisions": {"APPROVE": 0, "REVIEW": 0, "BLOCK": 0},
                "alerts": []
            }

        # 2. Avg Score
        avg_score_result = query.with_entities(func.avg(PredictionLog.risk_score)).first()
        avg_score = float(avg_score_result[0]) if avg_score_result and avg_score_result[0] else 0.0

        # 3. Decision Counts
        # Returns list of tuples: [('APPROVE', 10), ('BLOCK', 2)]
        decision_counts = query.with_entities(
            PredictionLog.decision, func.count(PredictionLog.decision)
        ).group_by(PredictionLog.decision).all()
        
        decisions = {"APPROVE": 0, "REVIEW": 0, "BLOCK": 0}
        for dec, count in decision_counts:
            if dec in decisions:
                decisions[dec] = count
                
        # 4. Drift / Alert Logic
        alerts = []
        
        # Heuristic A: High Average Risk Score (Global Shift)
        # If avg score > 0.20 (20%), something might be wrong (normally fraud is rare < 1%)
        if avg_score > 0.20:
            alerts.append(f"High Average Risk Score detected: {avg_score:.4f} (Threshold: 0.20)")

        # Heuristic B: High Block Rate
        block_rate = decisions["BLOCK"] / total
        if block_rate > 0.15: # 15% Block rate is very high for credit cards
            alerts.append(f"High Block Rate detected: {block_rate:.2%} (Threshold: 15%)")

        return {
            "window_hours": hours,
            "total_requests": total,
            "avg_risk_score": round(avg_score, 4),
            "decisions": decisions,
            "alerts": alerts
        }

    finally:
        db.close()
