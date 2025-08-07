# app/main.py
from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from app.transcriber import transcribe_audio
import uuid, shutil, os, json
from threading import Semaphore
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

TMP_DIR = "tmp"
os.makedirs(TMP_DIR, exist_ok=True)

MAX_CONCURRENT = int(os.getenv("MAX_CONCURRENT_TRANSCRIPTIONS", 5))
semaphore = Semaphore(MAX_CONCURRENT)

@app.get("/", response_class=HTMLResponse)
async def upload_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/upload.html", response_class=HTMLResponse)
async def upload_html(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

@app.post("/upload")
async def upload_audio(
    background_tasks: BackgroundTasks,
    request: Request,
    file: UploadFile = File(...),
    model_size: str = Form("base"),
    callback_url: str = Form(None),
    custom_id: str = Form(None)
):
    clean_old_tmp_files()

    audio_id = custom_id if custom_id else str(uuid.uuid4())

    # 🔐 Reject if this ID is already in use
    progress_file = f"{TMP_DIR}/progress_{audio_id}.json"
    result_file = f"{TMP_DIR}/output_{audio_id}.txt"
    if os.path.exists(progress_file) or os.path.exists(result_file):
        return JSONResponse({
            "error": "This ID is already in use. Please supply a new one.",
            "audio_id": audio_id
        }, status_code=409)

    audio_path = f"{TMP_DIR}/{audio_id}_{file.filename}"
    with open(audio_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    if not semaphore.acquire(blocking=False):
        with open(progress_file, "w") as f:
            json.dump({
                "status": "throttled",
                "message": "Transcription is throttled. Please retry later.",
                "result_url": f"/result/{audio_id}"
            }, f)
        return JSONResponse({
            "message": "Throttled due to concurrency limits.",
            "audio_id": audio_id,
            "retry_url": f"/result/{audio_id}"
        }, status_code=429)

    with open(progress_file, "w") as f:
        json.dump({"status": "processing", "segments": 0, "result": ""}, f)

    with open(f"{TMP_DIR}/cancel_{audio_id}.json", "w") as f:
        json.dump({"cancel": False}, f)

    background_tasks.add_task(wrapped_transcribe_audio, audio_path, model_size, audio_id, callback_url)

    return {
        "message": "Transcription started",
        "audio_id": audio_id,
        "result_url": f"/result/{audio_id}"
    }



@app.post("/upload1")
async def upload_audio1(
    background_tasks: BackgroundTasks,
    request: Request,
    file: UploadFile = File(...),
    model_size: str = Form("base"),
    callback_url: str = Form(None)
):
    clean_old_tmp_files()
    audio_id = str(uuid.uuid4())
    audio_path = f"{TMP_DIR}/{audio_id}_{file.filename}"
    with open(audio_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    if not semaphore.acquire(blocking=False):
        with open(f"{TMP_DIR}/progress_{audio_id}.json", "w") as f:
            json.dump({
                "status": "throttled",
                "message": "Transcription is throttled. Please retry later.",
                "result_url": f"/result/{audio_id}"
            }, f)
        return JSONResponse({
            "message": "Throttled due to concurrency limits.",
            "audio_id": audio_id,
            "retry_url": f"/result/{audio_id}"
        }, status_code=429)

    with open(f"{TMP_DIR}/progress_{audio_id}.json", "w") as f:
        json.dump({"status": "processing", "segments": 0, "result": ""}, f)

    with open(f"{TMP_DIR}/cancel_{audio_id}.json", "w") as f:
        json.dump({"cancel": False}, f)

    background_tasks.add_task(wrapped_transcribe_audio, audio_path, model_size, audio_id, callback_url)

    return {
        "message": "Transcription started",
        "audio_id": audio_id,
        "result_url": f"/result/{audio_id}"
    }

@app.get("/result/{audio_id}", response_class=PlainTextResponse)
async def get_result(audio_id: str):
    output_path = f"{TMP_DIR}/output_{audio_id}.txt"
    if os.path.exists(output_path):
        with open(output_path, "r") as f:
            return f.read()
    return PlainTextResponse("Result not ready or audio_id invalid.", status_code=404)

@app.get("/progress1/{audio_id}", response_class=JSONResponse)
async def get_progress1(audio_id: str):
    progress_file = f"{TMP_DIR}/progress_{audio_id}.json"
    if os.path.exists(progress_file):
        with open(progress_file, "r") as f:
            return json.load(f)
    return JSONResponse({"status": "not_found"}, status_code=404)

import logging
logging.basicConfig(level=logging.INFO)

@app.get("/progress/{audio_id}", response_class=JSONResponse)
async def get_progress(audio_id: str):
    #print(f" Received Progress: {audio_id} ")
    #logging.info(f"[{audio_id}] ...")
    progress_file = f"{TMP_DIR}/progress_{audio_id}.json"
    if os.path.exists(progress_file):
        try:
            with open(progress_file, "r") as f:
                data = json.load(f)
                #logging.info(f"[{audio_id}] Returning progress data: {data}")
                return JSONResponse(data)  # Explicit response
        except Exception as e:
            #logging.error(f"[{audio_id}] Failed to load progress file: {e}")
            return JSONResponse({"status": "error", "error": str(e)}, status_code=500)
    #logging.warning(f"[{audio_id}] Progress file not found.")
    return JSONResponse({"status": "not_found"}, status_code=404)

@app.post("/cancel/{audio_id}", response_class=JSONResponse)
async def cancel_transcription(audio_id: str):
    cancel_file = f"{TMP_DIR}/cancel_{audio_id}.json"
    if os.path.exists(cancel_file):
        with open(cancel_file, "w") as f:
            json.dump({"cancel": True}, f)
        return {"status": "cancellation_requested"}
    return JSONResponse({"error": "No active transcription found for this ID."}, status_code=404)

def wrapped_transcribe_audio(audio_path, model_size, audio_id, callback_url):
    try:
        transcribe_audio(audio_path, model_size, audio_id, callback_url)
    finally:
        semaphore.release()

import os
import time

def clean_old_tmp_files(tmp_folder='tmp', max_age_minutes=30):
    now = time.time()
    max_age_seconds = max_age_minutes * 60

    for fname in os.listdir(tmp_folder):
        path = os.path.join(tmp_folder, fname)
        if os.path.isfile(path):
            if now - os.path.getmtime(path) > max_age_seconds:
                try:
                    os.remove(path)
                    print(f"🧹 Deleted old tmp file: {path}")
                except Exception as e:
                    print(f"Failed to delete {path}: {e}")
