import time
import requests
import pandas as pd
import os
import random
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_PATH = os.path.join(PROJECT_ROOT, 'data', 'raw', 'creditcard.csv')
API_URL = "http://localhost:8000/predict"
API_KEY = "sentinel-dev-key"

def stream_transactions():
    if not os.path.exists(DATA_PATH):
        logger.error(f"Dataset not found at {DATA_PATH}")
        return

    logger.info("Loading dataset for streaming...")
    df = pd.read_csv(DATA_PATH)
    
    # Mix fraud and safe transactions for a good demo
    fraud = df[df['Class'] == 1].sample(50)
    safe = df[df['Class'] == 0].sample(200)
    demo_pool = pd.concat([fraud, safe]).sample(frac=1).reset_index(drop=True)

    logger.info(f"Starting Live Stream of {len(demo_pool)} transactions...")
    
    headers = {
        "X-API-KEY": API_KEY,
        "Content-Type": "application/json"
    }

    for _, row in demo_pool.iterrows():
        # Prepare payload
        payload = row.to_dict()
        # Remove Class (target) as API doesn't expect it
        payload.pop('Class', None)
        # Mark as simulated
        payload['is_simulated'] = 1
        
        try:
            start_time = time.time()
            response = requests.post(API_URL, json=payload, headers=headers)
            latency = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                res_data = response.json()
                logger.info(f"Sent: ${payload['Amount']:.2f} | Result: {res_data['decision']} | Score: {res_data['risk_score']:.4f} | Latency: {latency:.2f}ms")
            else:
                logger.warning(f"Failed to send transaction: {response.text}")
        except Exception as e:
            logger.error(f"Stream Error: {e}")
        
        # Slower intervals to let the UI breathe
        time.sleep(random.uniform(2.0, 5.0))

if __name__ == "__main__":
    stream_transactions()
