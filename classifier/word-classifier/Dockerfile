FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        libjpeg-dev libpng-dev libglib2.0-0 libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY classifier/word-classifier/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY classifier/shared/          ./shared/
COPY classifier/word-classifier/ ./word_service/

EXPOSE 8002
CMD ["uvicorn", "word_service.main:app", "--host", "0.0.0.0", "--port", "8002"]
