import logging
import os
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime

# Configure logging to both console and file
LOG_FILE = "app.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("central-logger")

app = FastAPI(title="Logger Service")


class LogEntry(BaseModel):
    service: str
    level: str = "INFO"
    message: str
    timestamp: str = ""


@app.post("/log")
async def receive_log(entry: LogEntry):
    ts = entry.timestamp or datetime.utcnow().isoformat()
    log.info(f"[{ts}] [{entry.service}] [{entry.level}] {entry.message}")
    return {"status": "logged"}


@app.get("/health")
def health():
    return {"status": "ok"}