import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, classification_report, average_precision_score, recall_score, precision_score

def calculate_fraud_savings(y_true, y_pred, amounts):
    """
    Calculates the financial impact of the model.
    
    Assumptions:
    - Cost of False Negative (Missed Fraud): You lose the entire 'Amount' of the transaction.
    - Cost of False Positive (False Alarm): Admin cost to call customer (e.g., $5).
    """
    evaluation_df = pd.DataFrame({
        'y_true': y_true,
        'y_pred': y_pred,
        'Amount': amounts
    })
    
    # False Negatives: Fraud (1) but predicted Normal (0)
    # Loss = Sum of amounts of these transactions
    missed_frauds = evaluation_df[(evaluation_df['y_true'] == 1) & (evaluation_df['y_pred'] == 0)]
    cost_fn = missed_frauds['Amount'].sum()
    
    # False Positives: Normal (0) but predicted Fraud (1)
    # Loss = Fixed cost (e.g., $5) * Count
    false_alarms = evaluation_df[(evaluation_df['y_true'] == 0) & (evaluation_df['y_pred'] == 1)]
    cost_fp = len(false_alarms) * 5.0
    
    # Detected Fraud (True Positives) = Savings
    # We "save" the amount that we blocked.
    caught_frauds = evaluation_df[(evaluation_df['y_true'] == 1) & (evaluation_df['y_pred'] == 1)]
    savings = caught_frauds['Amount'].sum()
    
    return {
        'total_fraud_loss_prevented': savings,
        'cost_of_missed_fraud': cost_fn,
        'cost_of_false_alarms': cost_fp,
        'net_savings': savings - cost_fp 
    }

def print_evaluation_report(y_true, y_pred, y_prob, amounts=None):
    print("\n--- Model Evaluation ---")
    
    # 1. Standard Metrics
    print(classification_report(y_true, y_pred))
    
    # 2. AUC-PR (Better for imbalance than ROC)
    auc_pr = average_precision_score(y_true, y_prob)
    print(f"AUPRC (Area Under Precision-Recall Curve): {auc_pr:.4f}")
    
    # 3. Confusion Matrix
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()
    print(f"\nConfusion Matrix:\nTN={tn} | FP={fp}\nFN={fn}  | TP={tp}")
    
    # 4. Financial Impact
    if amounts is not None:
        financials = calculate_fraud_savings(y_true, y_pred, amounts)
        print("\n--- Financial Impact (Estimated) ---")
        print(f"Money Saved (Blocked Fraud):   ${financials['total_fraud_loss_prevented']:,.2f}")
        print(f"Money Lost (Missed Fraud):     ${financials['cost_of_missed_fraud']:,.2f}")
        print(f"Admin Cost (False Alarms):     ${financials['cost_of_false_alarms']:,.2f}")
        print(f"-------------------------------------------")
        print(f"NET VALUE CREATED:             ${financials['net_savings']:,.2f}")
