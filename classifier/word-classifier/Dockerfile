FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ENV EASYOCR_MODULE_PATH=/app/.EasyOCR

RUN apt-get update && apt-get install -y --no-install-recommends \
        libjpeg-dev libpng-dev libglib2.0-0 libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY classifier/word-classifier/requirements.txt .
RUN pip install --no-cache-dir torch==2.11.0+cpu torchvision==0.26.0+cpu --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

# Pre-download EasyOCR models (English) during build
RUN python -c "import easyocr; easyocr.Reader(['en'])"

COPY classifier/shared/          ./shared/
COPY classifier/word-classifier/ ./word_service/

EXPOSE 8002
CMD ["uvicorn", "word_service.main:app", "--host", "0.0.0.0", "--port", "8002"]
