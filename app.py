import re
import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

app = FastAPI(title="TaufikDownloader")

PIPED_SERVERS = [
    "https://pipedapi.kavin.rocks",
    "https://pipedapi.moomoo.me",
    "https://pipedapi.syncpundit.io",
    "https://api.piped.private.coffee",
    "https://piped-api.lunar.icu",
]
INVIDIOUS_SERVERS = [
    "https://inv.nadeko.net",
    "https://invidious.nerdvpn.de",
]

@app.get("/", include_in_schema=False)
def serve_home():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"message": "LIVE"}

@app.get("/health")
def health(): return {"status": "ok"}

@app.get("/streams/{video_id}")
def get_streams(video_id: str):
    if not re.fullmatch(r"[a-zA-Z0-9_-]{11}", video_id):
        raise HTTPException(400, "Invalid ID")
    for server in PIPED_SERVERS:
        try:
            r = requests.get(f"{server}/streams/{video_id}", timeout=12)
            if r.status_code != 200: continue
            data = r.json()
            streams = []
            for s in data.get("videoStreams", []):
                if "video/mp4" in s.get("mimeType","") and s.get("url"):
                    streams.append({"quality": s.get("quality","HD"), "format": "MP4", "url": s["url"]})
            if streams:
                streams.sort(key=lambda x: int(re.search(r"\d+", x["quality"]).group()) if re.search(r"\d+", x["quality"]) else 0, reverse=True)
                return {"videoStreams": streams, "source": server}
        except: continue
    for server in INVIDIOUS_SERVERS:
        try:
            r = requests.get(f"{server}/api/v1/videos/{video_id}", timeout=12)
            if r.status_code != 200: continue
            data = r.json()
            streams = []
            for f in data.get("formatStreams", []):
                if f.get("container") == "mp4" and f.get("url"):
                    streams.append({"quality": f.get("qualityLabel","HD"), "format": "MP4", "url": f["url"]})
            if streams: return {"videoStreams": streams, "source": server}
        except: continue
    try:
        import yt_dlp
        ydl_opts = {"quiet": True, "skip_download": True, "noplaylist": True, "format": "best[ext=mp4]", "extractor_args": {"youtube": {"player_client": ["ios", "android", "web"]}}}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            streams = []
            for f in info.get("formats", []):
                if f.get("ext") == "mp4" and f.get("vcodec") != "none" and f.get("acodec") != "none" and f.get("url"):
                    h = f.get("height")
                    q = f"{h}p" if h else f.get("format_note","HD")
                    streams.append({"quality": q, "format": "MP4", "url": f["url"]})
            if streams:
                unique = {s["quality"]: s for s in streams}
                streams = sorted(unique.values(), key=lambda x: int(re.search(r"\d+", x["quality"]).group()) if re.search(r"\d+", x["quality"]) else 0, reverse=True)
                return {"videoStreams": streams, "source": "yt-dlp-ios"}
    except: pass
    raise HTTPException(500, "Semua server down, coba lagi 5 detik")
