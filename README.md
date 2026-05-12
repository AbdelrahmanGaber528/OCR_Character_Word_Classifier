# Distributed OCR System

A microservices-based Optical Character Recognition (OCR) system that provides both single-character classification and full-word recognition. The system is designed with a Gateway pattern.

## Architecture

The project is split into three main services:

1.  **Gateway (Port 8000):** The entry point. Routes requests to the appropriate classification service and serves a simple web UI.
2.  **Character Service (Port 8001):** Uses a custom MobileNetV2 (or OCR_CNN) model trained on handwritten/printed characters to predict single letters.
3.  **Word Service (Port 8002):** Uses EasyOCR to perform text detection and recognition on full images/words.

All services use standard Python logging, and logs are consolidated during execution.

## Tech Stack

*   **Language:** Python 3.11+
*   **Framework:** FastAPI, Uvicorn
*   **Deep Learning:** PyTorch, Torchvision, EasyOCR
*   **Containerization:** Docker, Docker Compose
*   **Imaging:** Pillow, OpenCV

## Getting Started

### Prerequisites

*   Python 3.11 or higher
*   Docker and Docker Compose (optional, for containerized run)
*   A virtual environment is recommended: `python3 -m venv .venv && source .venv/bin/activate`

### Installation

1.  Clone the repository.
2.  Install dependencies for all services:
    ```bash
    pip install -r gateway/requirements.txt
    pip install -r classifier/character-classifier/requirements.txt
    pip install -r classifier/word-classifier/requirements.txt
    ```

## Running the Project

### Option 1: Local Execution (Fastest for Development)

I have provided an automation script that sets up the environment and starts all services in the background.

```bash
chmod +x run_local.sh
./run_local.sh
```
*   Logs from all services will be consolidated into a single `app.log` file in the root directory.
*   Press `CTRL+C` to stop all services.

### Option 2: Docker Compose

To run the entire stack in isolated containers:

```bash
docker-compose up --build
```
The Gateway will be available at `http://localhost:8000`.

## API Documentation

Each service provides interactive Swagger UI (OpenAPI) documentation for exploring and testing endpoints:

*   **Gateway:** [http://localhost:8000/docs](http://localhost:8000/docs)
*   **Character Service:** [http://localhost:8001/docs](http://localhost:8001/docs)
*   **Word Service:** [http://localhost:8002/docs](http://localhost:8002/docs)

## API Usage

### Gateway Endpoints
*   `GET /`: Web interface for uploading images.
*   `POST /predict/character`: Upload an image to predict a single character.
*   `POST /predict/word`: Upload an image to recognize a full word.

### Direct Service Access
*   `GET http://localhost:8001/health`: Character Service health check.
*   `GET http://localhost:8002/health`: Word Service health check.

## Testing

A comprehensive test suite is included to verify the system's integrity.

1.  **System Verification:** Test all running services and OCR accuracy.
    ```bash
    python3 test_system.py
    ```
2.  **End-to-End Suite:** Automatically tests the project in both Local and Docker modes.
    ```bash
    ./test_all.sh
    ```

## AWS Cloud Integration (Images & Predictions)

The system is deployed on AWS and integrated with cloud storage for persistence.

### Architecture
- **Amazon S3**: Stores the actual image files uploaded by users.
- **Amazon RDS (PostgreSQL)**: Stores prediction metadata (text, confidence, timestamp, and S3 reference).

### Infrastructure Setup
1. **S3 Bucket Creation**:
   ```bash
   aws s3 mb s3://ocr-storage-anas-470895881101 --region eu-north-1
   ```

2. **RDS Database Creation**:
   ```bash
   aws rds create-db-instance \
       --db-instance-identifier ocr-db \
       --db-instance-class db.t3.micro \
       --engine postgres \
       --master-username ocr_admin \
       --master-user-password "Ocr_Void_#123" \
       --allocated-storage 20 \
       --region eu-north-1
   ```

3. **Database Schema**:
   The `predictions` table is automatically created by the Gateway service on startup:
   - `id`: Primary Key
   - `filename`: Original name of the file
   - `s3_key`: Path to the image in S3
   - `prediction`: The OCR result
   - `confidence`: Model confidence score
   - `model_type`: 'character' or 'word'
   - `timestamp`: UTC processing time

### Deployment Steps
1. **Docker Build & Push**:
   ```bash
   aws ecr get-login-password --region eu-north-1 | doas docker login --username AWS --password-stdin 470895881101.dkr.ecr.eu-north-1.amazonaws.com
   docker build --platform linux/amd64 -t ocr-gateway -f gateway/Dockerfile .
   docker tag ocr-gateway:latest 470895881101.dkr.ecr.eu-north-1.amazonaws.com/ocr-gateway:latest
   doas docker push 470895881101.dkr.ecr.eu-north-1.amazonaws.com/ocr-gateway:latest
   ```

2. **ECS Configuration**:
   The Gateway requires the following Environment Variables in the Task Definition:
   - `S3_BUCKET_NAME`: `ocr-storage-anas-470895881101`
   - `DATABASE_URL`: `postgresql://ocr_admin:Ocr_Void_#123@<RDS_ENDPOINT>:5432/postgres`

3. **Service Refresh**:
   ```bash
   aws ecs update-service --cluster ocr-cluster --service gateway-service --force-new-deployment
   ```

### Data Verification
From your local terminal, you can verify the stored data:

**Check Images (S3):**
```bash
aws s3 ls s3://ocr-storage-anas-470895881101/uploads/
```

**Check Records (RDS):**
```bash
psql "host=ocr-db.chi4cw8osd0x.eu-north-1.rds.amazonaws.com port=5432 dbname=postgres user=ocr_admin"
# Run: SELECT * FROM predictions;
```

### Monitoring (CloudWatch)
The system is monitored using **Amazon CloudWatch**:
- **Centralized Logs**: View logs for Gateway, Character, and Word services in CloudWatch Log Groups.
- **Container Insights**: Real-time CPU and Memory tracking for the ECS Cluster.
- **Alarms**: Health check monitoring for service availability.

## Project Structure

```text
.
├── classifier/
│   ├── character-classifier/  # Custom model service
│   ├── word-classifier/       # EasyOCR service
│   └── shared/                # Shared logic (preprocessing, model loading)
├── gateway/                   # API Gateway & Web UI
├── model/                     # Trained .pth model files
├── tested_photos/             # Sample images for testing
├── docker-compose.yml         # Container orchestration
└── run_local.sh               # Local automation script
```

## License

This project is for educational purposes as part of an Advanced Machine Learning curriculum.




---
i want to fill the following : , can you help me PROJECT DISCUSSION – DETAILED SHEET
Course	Semester	Team ID	Discussion Time	TA	Final Grade
Cloud Computing / Integrated Projects	Spring 2026				
1. Project and Team Snapshot
Project Identity
Project No.	
Project Title		Team Type	☐ CS ☐ AI ☐ Mixed
Idea Source	☐ Bank ☐ Custom ☐ Hybrid	Related Courses	
Project Bank Ref.		One-line Summary	



Contacts / Links
Team Leader Email	
GitHub Link	
Demo / Deployment Link	
	
	Project Snapshot
Problem being solved	
Target users	
Minimum viable scope	
	Bonus / Enrichment








	2. Team Details
#	Student Name	Student ID	Main Role / Contribution	Attendance
1				☐ P ☐ A
2				☐ P ☐ A
3				☐ P ☐ A
4				☐ P ☐ A
5				☐ P ☐ A
6				☐ P ☐ A
7				☐ P ☐ A
8				☐ P ☐ A

Interpretation note: For CS teams, cloud depth is expected mainly in deployment, containers, storage, security, monitoring, and scalability. For AI teams, it is expected mainly in hosting inference/experiments, data/result storage, deployment, monitoring, and cost feasibility. For mixed teams, the product and AI layers should be integrated and operated meaningfully in the cloud.

3. Evaluation, Cloud Review, and Decision
A. General Project Evaluation
Criterion / focus	What to check	Score (0–4)	Notes
Problem clarity	Is the problem clear and meaningful?		
Scope realism	Can the team finish it realistically?		
Course alignment	Does it fit the claimed courses naturally?		
Technical depth	Is there enough substance for this team type?		
Evaluation / testing readiness	Are metrics, experiments, or tests defined?		
Discussion performance	Did the team explain and defend the idea well?		
Total General Score / 24			
Scoring scale for both sections: 0 = Not demonstrated, 1 = Weak, 2 = Basic, 3 = Good, 4 = Strong
B. Cloud Computing Evaluation
Cloud criterion	What to check	Student Response	Score (0–4)	Notes
Architecture relevance	Is the cloud design meaningful for the project?			
Service selection	Are chosen cloud services appropriate and justified?		
	
Deployment / containers	Is there a clear deployment and packaging approach?		
	
Networking / security	Is exposure and protection in the cloud understood?		
	
Storage / data handling	Are storage and data choices sensible?		
	
Scalability / reliability	Has the team considered scale and availability?		
	
Monitoring / observability	Is there a credible logging / monitoring plan?			
Cost awareness	Is there awareness of cost and free-tier feasibility?			
Total Cloud Score / 32				