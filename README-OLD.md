## Quick Start

### 1. Backend Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Run the API: `python src/services/api.py` (Or use Docker)

### 2. Frontend Setup
1. Navigate to `app/`: `cd app`
2. Install dependencies: `npm install`
3. Run dev server: `npm run dev`

### 3. Live Demo (The "Real Thing")
To see the system in action with real-time fraud detection:
1. Ensure the API is running (`localhost:8000`).
2. Run the traffic generator:
   ```bash
   python src/services/traffic_generator.py
   ```
3. Open the Dashboard in your browser. You will see transactions streaming into the **Live Transaction Stream** with real-time risk scores and decisions.

---

### Audit & Compliance
The system includes a robust logging layer (`src/services/db.py`) that stores every prediction request for audit purposes.
- **Data Stored**: Request ID, Timestamp, Input Amount, Risk Score, Decision, Explanation.
- **Storage**: Currently uses SQLite (`data/sentinelrisk.db`), upgradeable to PostgreSQL.
- **Latency**: Logging is performed asynchronously via background tasks to ensure zero impact on inference latency.
- **Compliance**: Provides a complete immutable history of decisions for regulatory review.

### Monitoring & Metrics
A built-in analytics endpoint provides real-time visibility into system health and data drift.
- **Endpoint**: `GET /metrics?hours=24`
- **Response**:
    - `total_requests`: Volume of traffic.
    - `avg_risk_score`: Mean fraud score (indicates concept drift if spiking).
    - `decisions`: Count of APPROVE/REVIEW/BLOCK.
    - `alerts`: Automatic warnings for high block rates (>15%) or abnormal scores.
- **Performance**: Aggregations are performed on indexed columns (`timestamp`, `decision`) for speed.

### Security
The API is protected by API Key authentication to prevent unauthorized access.
- **Header**: `X-API-KEY`
- **Endpoints Protected**: `/predict`, `/metrics`
- **Public Endpoints**: `/health`, `/docs`
- **Configuration**: Set the `SENTINEL_API_KEY` environment variable (default: `sentinel-dev-key`).

## Project Structure

The folder structure is organized to support a scalable and maintainable machine learning workflow:

### `data/`
Centralized storage for all data assets.
- **`raw/`**: Stores the original, immutable dataset (`creditcard.csv`).
- **`processed/`**: Contains cleaned, canonical data sets used for modeling.
- **`external/`**: Data from third-party sources or secondary datasets.

### `src/`
Source code for the project.
- **`data/`**: Scripts for data ingestion, cleaning, and preprocessing pipelines.
- **`models/`**: Scripts for training, hyperparameter tuning, and model evaluation.
- **`services/`**:  Production-facing code. Scripts for inference, API endpoints, and real-time scoring logic.
- **`utils/`**: Shared helper functions and utility modules.

### CI/CD
A GitHub Actions workflow (`.github/workflows/ci.yml`) is configured to run tests on every push.

### Deployment (Docker)
The system is ready for containerized deployment.

1.  **Build and Run**:
    ```bash
    docker-compose up --build
    ```
2.  **Access**:
    - API: `http://localhost:8000`
    - Swagger UI: `http://localhost:8000/docs`

### `app/`
Production-ready React + Tailwind CSS frontend for the dashboard and simulator.

### `notebooks/`
Jupyter notebooks for Exploratory Data Analysis (EDA).

### `tests/`
Unit and integration tests to ensure code reliability and correctness.
