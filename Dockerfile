FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && \
    apt-get install -y ffmpeg git && \
    pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache && mkdir -p /app/tmp

# Optional: pre-download model
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('base', compute_type='int8')"

COPY app/ app/
COPY ssl/ ssl/

#CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--ssl-keyfile", "ssl/key.pem", "--ssl-certfile", "ssl/cert.pem"]
