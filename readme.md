# 🎤 Faster Whisper Transcription App

A modern, fast, and flexible transcription web app powered by [faster-whisper](https://github.com/guillaumekln/faster-whisper). It supports three modes:

- 📁 **File Upload**: Upload audio files for transcription.
- 🎙️ **Mic Recording**: Record speech and send it for transcription via Whisper.
- 💬 **Live Transcribe**: In-browser real-time transcription using the browser’s SpeechRecognition API (English only).

---

## 🚀 Features

- ✅ File upload via drag-and-drop or file picker  
- ✅ Asynchronous transcription with status polling  
- ✅ Optional callback integration via URL  
- ✅ Self-cleaning temp directory  
- ✅ UUID tracking for each audio job  
- ✅ Live in-browser transcription (no server required)  
- ✅ Chrome-optimized UX with fallback guidance  
- ✅ Microphone activity animation during recording  
- ✅ Voice input segment styling (real-time + finalized)

---

## 🛠️ Setup

### 1. Prerequisites

- Python 3.9+
- `ffmpeg` installed
- Docker (optional, for containerization)
- (Optional) Whisper model files (e.g. `.tar` archive preloaded)

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the server

```
uvicorn app.main:app --host 0.0.0.0 --port 443 --ssl-keyfile=certs/key.pem --ssl-certfile=certs/cert.pem
```

🔗 Endpoints
Method	Endpoint	Description
GET	/	Main page
GET	/upload.html	Minimal upload-only page
POST	/upload	Accepts audio file for transcription
GET	/progress/{id}	Returns job status + partial result
GET	/result/{id}	Final result text (plain text)
POST	/cancel/{id}	Request cancellation
🧪 Features Demo Pages

APEX Embedded Page: Integrates polling + dynamic status display

    upload.html?id=...&close=true: For direct upload without UI

Speech Recorder / Live Transcriber: Mic-based input options with buttons and transcript pane

📦 Docker

Build and run the image with:

docker build -t whisper-app .
docker run -p 443:443 whisper-app

    🧼 Remember to .dockerignore large model files (*.tar) and temporary output folders (tmp/)
🧹 Auto Cleanup

The app deletes files in tmp/ older than 30 minutes:

    On every upload

    During server startup

No polling daemon needed.
🧠 Credits

    faster-whisper by Guillaume Klein

    Frontend: Custom vanilla JS + Oracle APEX integration

    UI Inspired by ChatGPT voice experience and Chrome UX

📬 Questions?

Reach out to @cv.ranjith@gmail.com
