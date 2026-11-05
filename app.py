import re
import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

app = FastAPI(title="TaufikDownloader - AMPUH")

# Cobalt itu paling stabil sedunia, nggak pernah down
def get_from_cobalt(video_id):
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        r = requests.post(
            "https://api.cobalt.tools/api/json",
            json={"url": url, "vQuality": "1080", "aFormat": "mp3", "isAudioOnly": False},
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=15
        )
        data = r.json()
        if data.get("status") == "stream" and data.get("url"):
            return [{"quality": "1080p (Cobalt)", "format": "MP4", "url": data["url"]}]
        if data.get("status") == "redirect":
            return [{"quality": "1080p", "format": "MP4", "url": data["url"]}]
    except:
        pass
    return []

def get_from_ytdlp(video_id):
    try:
        import yt_dlp
        # Ini trik paling ampuh: pakai 3 client sekaligus, iOS paling ampuh bypass bot
        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "noplaylist": True,
            "format": "bv*+ba/b",
            "extractor_args": {"youtube": {"player_client": ["ios", "android_vr", "tv_embedded"]}}
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            streams = []
            for f in info.get("formats", [])[::-1]:
                if f.get("ext") == "mp4" and f.get("vcodec") != "none" and f.get("acodec") != "none" and f.get("url"):
                    h = f.get("height")
                    q = f"{h}p" if h else f.get("format_note","HD")
                    streams.append({"quality": q, "format": "MP4", "url": f["url"]})
            # ambil 1 kualitas per resolusi biar rapi
            uniq = {}
            for s in streams: uniq[s["quality"]] = s
            return sorted(uniq.values(), key=lambda x: int(re.search(r"\d+", x["quality"]).group()) if re.search(r"\d+", x["quality"]) else 0, reverse=True)
    except Exception as e:
        print(f"ytdlp error: {e}")
        return []

@app.get("/", include_in_schema=False)
def serve_home():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"message": "LIVE - AMPUH MODE"}

@app.get("/health")
def health(): return {"status": "ok", "mode": "ampuh"}

@app.get("/streams/{video_id}")
def get_streams(video_id: str):
    if not re.fullmatch(r"[a-zA-Z0-9_-]{11}", video_id):
        raise HTTPException(400, "Invalid ID")

    # 1. COBA COBALT DULU (99% work)
    streams = get_from_cobalt(video_id)
    if streams:
        return {"videoStreams": streams, "source": "cobalt.tools"}

    # 2. FALLBACK YT-DLP IOS (paling ampuh kalau cobalt lagi maintenance)
    streams = get_from_ytdlp(video_id)
    if streams:
        return {"videoStreams": streams, "source": "yt-dlp-ios-tv"}

    raise HTTPException(500, "Gagal, coba video lain")
