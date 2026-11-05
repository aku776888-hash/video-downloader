import re
import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

app = FastAPI(title="TaufikDownloader - AMPUH")

def get_from_cobalt(video_id):
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        r = requests.post(
            "https://api.cobalt.tools/api/json",
            json={"url": url, "vQuality": "1080"},
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=15
        )
        data = r.json()
        if data.get("url"):
            return [{"quality": "1080p", "format": "MP4", "url": data["url"]}]
    except Exception as e:
        print(f"cobalt error {e}")
    return []

def get_from_ytdlp(video_id):
    try:
        import yt_dlp
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
            uniq = {}
            for s in streams: uniq[s["quality"]] = s
            return sorted(uniq.values(), key=lambda x: int(re.search(r"\d+", x["quality"]).group()) if re.search(r"\d+", x["quality"]) else 0, reverse=True)
    except Exception as e:
        print(f"ytdlp error: {e}")
        return []

@app.get("/", include_in_schema=False)
def serve_home():
    html_file = "index-final.html" if os.path.exists("index-final.html") else "index.html"
    if os.path.exists(html_file):
        return FileResponse(html_file)
    return {"message": "LIVE - AMPUH MODE"}

@app.get("/health")
def health(): return {"status": "ok", "mode": "ampuh", "region": "iad"}

@app.get("/streams/{video_id}")
def get_streams(video_id: str):
    if not re.fullmatch(r"[a-zA-Z0-9_-]{11}", video_id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    streams = get_from_cobalt(video_id)
    if streams:
        return {"videoStreams": streams, "source": "cobalt.tools"}
    streams = get_from_ytdlp(video_id)
    if streams:
        return {"videoStreams": streams, "source": "yt-dlp-ios-tv"}
    raise HTTPException(status_code=500, detail="Gagal, coba video lain")
