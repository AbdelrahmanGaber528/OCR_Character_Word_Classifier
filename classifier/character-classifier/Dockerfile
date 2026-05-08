FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        libjpeg-dev libpng-dev libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY classifier/character-classifier/requirements.txt .
RUN pip install --no-cache-dir torch==2.11.0+cpu torchvision==0.26.0+cpu --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

# Copy model files into the image
COPY model/ /app/model/

COPY classifier/shared/                ./shared/
COPY classifier/character-classifier/  ./character_service/

EXPOSE 8001
CMD ["uvicorn", "character_service.main:app", "--host", "0.0.0.0", "--port", "8001"]
