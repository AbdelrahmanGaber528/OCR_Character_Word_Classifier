from fastapi import FastAPI, Request, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx

app = FastAPI()


app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="gateway/templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/predict/character")
async def char_proxy(file: UploadFile = File(...)):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://character_service:8001/predict-character", 
            files={"file": (file.filename, file.file)}
        )
    return response.json()


@app.post("/predict/word")
async def word_proxy(file: UploadFile = File(...)):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://word_service:8002/predict-word", 
            files={"file": (file.filename, file.file)}
        )
    return response.json()