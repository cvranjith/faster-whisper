# app/transcriber.py
from faster_whisper import WhisperModel
import os, requests, json

TMP_DIR = "tmp"

def transcribe_audio(audio_path, model_size, audio_id, callback_url):
    model = WhisperModel(model_size, compute_type="int8")
    segments, info = model.transcribe(audio_path, beam_size=5)

    result = ""
    segment_count = 0

    for segment in segments:
        cancel_path = f"{TMP_DIR}/cancel_{audio_id}.json"
        if os.path.exists(cancel_path):
            with open(cancel_path, "r") as f:
                if json.load(f).get("cancel"):
                    with open(f"{TMP_DIR}/progress_{audio_id}.json", "w") as pf:
                        json.dump({"status": "cancelled", "segments": segment_count, "result": result}, pf)
                    os.remove(audio_path)
                    return

        result += f"[{segment.start:.2f}s - {segment.end:.2f}s] {segment.text}\n"
        segment_count += 1
        if segment_count % 5 == 0:
            with open(f"{TMP_DIR}/progress_{audio_id}.json", "w") as f:
                json.dump({"status": "processing", "segments": segment_count, "result": result}, f)

    output_path = f"{TMP_DIR}/output_{audio_id}.txt"
    with open(output_path, "w") as f:
        f.write(result)

    with open(f"{TMP_DIR}/progress_{audio_id}.json", "w") as f:
        json.dump({"status": "done", "segments": segment_count, "result": result}, f)

    if callback_url:
        try:
            requests.post(callback_url, json={"audio_id": audio_id, "transcription": result})
        except Exception as e:
            print(f"Callback failed: {e}")

    os.remove(audio_path)
