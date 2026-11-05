import re
import requests
from fastapi import FastAPI, HTTPException

app = FastAPI(title="TaufikDownloader API - Anti Blokir")

@app.get("/")
def root():
    return {"message": "TaufikDownloader API is LIVE!", "status": "online", "method": "Piped - No Cookie Needed"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/streams/{video_id}")
def get_streams(video_id: str):
    if not re.fullmatch(r"[a-zA-Z0-9_-]{11}", video_id):
        raise HTTPException(status_code=400, detail="Invalid YouTube video ID")

    # List server Piped - kalau 1 down, pindah ke yang lain
    servers = [
        "https://pipedapi.kavin.rocks",
        "https://pipedapi.adminforge.de",
        "https://api.piped.private.coffee",
    ]

    last_error = ""
    for server in servers:
        try:
            resp = requests.get(f"{server}/streams/{video_id}", timeout=20)
            if resp.status_code != 200:
                last_error = f"{server} status {resp.status_code}"
                continue
            
            data = resp.json()
            video_streams = []

            # Piped kasih semua format, kita filter MP4 yang ada audio+video
            for s in data.get("videoStreams", []):
                url = s.get("url")
                mime = s.get("mimeType", "")
                if not url: continue
                if "video/mp4" not in mime: continue
                
                # Piped quality contoh: "720p", "1080p"
                quality = s.get("quality", "HD")
                video_streams.append({
                    "quality": quality,
                    "format": "MP4",
                    "url": url
                })

            if not video_streams:
                last_error = f"{server} no mp4 found"
                continue

            # Hapus duplikat & sort 1080p paling atas
            unique = {}
            for st in video_streams:
                unique[st["quality"]] = st
            video_streams = list(unique.values())
            video_streams.sort(key=lambda x: int(re.search(r"\d+", x["quality"]).group()) if re.search(r"\d+", x["quality"]) else 0, reverse=True)

            return {"videoStreams": video_streams}

        except Exception as e:
            last_error = str(e)
            continue

    raise HTTPException(status_code=500, detail=f"Semua Piped down. Last error: {last_error[:500]}")
