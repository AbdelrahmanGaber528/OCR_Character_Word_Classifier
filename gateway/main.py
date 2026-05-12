import os
import logging
from datetime import datetime
from fastapi import FastAPI, Request, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx
import boto3
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("gateway")

CHAR_URL = os.getenv("CHAR_URL", "http://character_service:8001")
WORD_URL = os.getenv("WORD_URL", "http://word_service:8002")
S3_BUCKET = os.getenv("S3_BUCKET_NAME")
DATABASE_URL = os.getenv("DATABASE_URL")
TIMEOUT  = 30.0

# ── DATABASE SETUP ────────────────────────────────────────────────────────
Base = declarative_base()

class PredictionRecord(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    s3_key = Column(String)
    prediction = Column(String)
    confidence = Column(Float)
    model_type = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

engine = None
SessionLocal = None
if DATABASE_URL:
    try:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")



# ── S3 SETUP ─────────────────────────────────────────────────────────────
s3_client = None
if S3_BUCKET:
    try:
        s3_client = boto3.client('s3')
        logger.info(f"S3 client initialized for bucket: {S3_BUCKET}")
    except Exception as e:
        logger.error(f"S3 initialization failed: {e}")

def save_to_cloud_task(filename: str, data: bytes, prediction: str, confidence: float, model_type: str):
    """Background task to persist data to S3 and RDS."""
    try:
        s3_key = None
        if s3_client and S3_BUCKET:
            s3_key = f"uploads/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
            s3_client.put_object(Bucket=S3_BUCKET, Key=s3_key, Body=data)
            logger.info(f"Uploaded {filename} to S3.")

        if SessionLocal:
            db = SessionLocal()
            record = PredictionRecord(
                filename=filename,
                s3_key=s3_key,
                prediction=prediction,
                confidence=confidence,
                model_type=model_type
            )
            db.add(record)
            db.commit()
            db.close()
            logger.info(f"Saved prediction for {filename} to RDS.")
    except Exception as e:
        logger.error(f"Failed to save to cloud: {e}")


app = FastAPI(title="OCR Gateway")
app.mount("/static", StaticFiles(directory="gateway/static"), name="static")
templates = Jinja2Templates(directory="gateway/templates")




# ── UI ────────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})



@app.get("/health")
async def health():
    results = {}
    async with httpx.AsyncClient(timeout=5.0) as client:
        for name, url in [("character_service", CHAR_URL), ("word_service", WORD_URL)]:
            try:
                r = await client.get(f"{url}/health")
                results[name] = r.json()
            except Exception:
                results[name] = {"status": "unreachable"}
    return {"gateway": "ok", "services": results}




@app.post("/predict/character")
async def predict_character(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "Must be an image file.")

    logger.info(f"Proxying character request: {file.filename}")
    data = await file.read()
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            resp = await client.post(
                f"{CHAR_URL}/predict-character",
                files={"file": (file.filename, data, file.content_type)},
            )
            resp.raise_for_status()
            res = resp.json()
            
            # Save to cloud in background
            background_tasks.add_task(
                save_to_cloud_task, 
                file.filename, data, res['predicted_letter'], res['confidence'], 'character'
            )

            logger.info(f"Character prediction success for {file.filename}")
            return res
        except Exception as e:
            logger.error(f"Character service error: {e}")
            raise HTTPException(502, f"Service error: {e}")






@app.post("/predict/word")
async def predict_word(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "Must be an image file.")

    logger.info(f"Proxying word request: {file.filename}")
    data = await file.read()
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            resp = await client.post(
                f"{WORD_URL}/predict-word",
                files={"file": (file.filename, data, file.content_type)},
            )
            resp.raise_for_status()
            res = resp.json()

            # Save to cloud in background
            background_tasks.add_task(
                save_to_cloud_task, 
                file.filename, data, res['predicted_word'], res['avg_confidence'], 'word'
            )

            logger.info(f"Word prediction success for {file.filename}")
            return res
        except Exception as e:
            logger.error(f"Word service error: {e}")
            raise HTTPException(502, f"Service error: {e}")