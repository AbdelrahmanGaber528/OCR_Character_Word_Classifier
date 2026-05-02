import os
import logging
from fastapi import FastAPI, Request, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("gateway")

CHAR_URL = os.getenv("CHAR_URL", "http://character_service:8001")
WORD_URL = os.getenv("WORD_URL", "http://word_service:8002")
TIMEOUT  = 30.0

app = FastAPI(title="OCR Gateway")
app.mount("/static", StaticFiles(directory="gateway/static"), name="static")
templates = Jinja2Templates(directory="gateway/templates")


# ── UI ────────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})



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
async def predict_character(file: UploadFile = File(...)):
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
            logger.info(f"Character prediction success for {file.filename}")
            return res
        except httpx.TimeoutException:
            logger.error(f"Character service timed out for {file.filename}")
            raise HTTPException(504, "Character service timed out.")
        except httpx.HTTPStatusError as e:
            logger.error(f"Character service error {e.response.status_code} for {file.filename}")
            raise HTTPException(e.response.status_code, e.response.text)
        except Exception as e:
            logger.error(f"Character service unreachable: {e}")
            raise HTTPException(502, f"Character service unreachable: {e}")






@app.post("/predict/word")
async def predict_word(file: UploadFile = File(...)):
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
            logger.info(f"Word prediction success for {file.filename}")
            return res
        except httpx.TimeoutException:
            logger.error(f"Word service timed out for {file.filename}")
            raise HTTPException(504, "Word service timed out.")
        except httpx.HTTPStatusError as e:
            logger.error(f"Word service error {e.response.status_code} for {file.filename}")
            raise HTTPException(e.response.status_code, e.response.text)
        except Exception as e:
            logger.error(f"Word service unreachable: {e}")
            raise HTTPException(502, f"Word service unreachable: {e}")