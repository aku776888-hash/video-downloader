import re
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import os

app = FastAPI(title="TaufikDownloader - SaveFrom Killer")

# 3 instance cobalt ampuh (kalau 1 down, pindah otomatis kayak Savefrom)
COBALT_INSTANCES = [
    "https://api.cobalt.tools/api/json",
    "https://co.wuk.sh/api/json",
    "https://api.cobalt.tn/api/json",
]

def get_from_cobalt(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"
    for api in COBALT_INSTANCES:
        try:
            r = requests.post(api, json={"url": url, "vQuality": "1080", "aFormat": "mp3"}, 
                              headers={"Accept": "application/json", "Content-Type": "application/json"}, timeout=12)
            j = r.json()
            if j.get("url"):
                return [{"quality": "1080p (HD)", "format": "MP4", "url": j["url"]}]
        except: continue
    return []

def get_from_ytdlp(video_id):
    try:
        import yt_dlp
        # Ini rahasia Savefrom: pakai 4 client sekaligus + impersonate iPhone
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "noplaylist": True,
            "extractor_args": {
                "youtube": {
                    "player_client": ["ios", "android", "tv_embedded", "web"],
                    "player_skip": ["webpage"]
                }
            },
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            best = []
            for f in info.get("formats", []):
                if f.get("ext") == "mp4" and f.get("url") and f.get("vcodec") != "none":
                    h = f.get("height") or 0
                    has_audio = f.get("acodec") != "none"
                    # Prioritaskan yang ada audio
                    if h >= 360:
                        label = f"{h}p"
                        if not has_audio: label += " - no audio"
                        best.append({"quality": label, "format": "MP4", "url": f["url"], "_h": h, "_a": has_audio})
            # sort: ada audio dulu, resolusi tinggi dulu
            best.sort(key=lambda x: (x["_a"], x["_h"]), reverse=True)
            # unique dan bersihkan
            seen = set()
            out = []
            for b in best:
                if b["quality"] not in seen:
                    seen.add(b["quality"])
                    del b["_h"]; del b["_a"]
                    out.append(b)
                if len(out) >= 6: break
            return out
    except Exception as e:
        print(f"yt-dlp error: {e}")
        return []

@app.get("/", include_in_schema=False)
def home():
    return FileResponse("index.html") if os.path.exists("index.html") else {"status":"live"}

@app.get("/health")
def health(): return {"status":"ok","region":"iad","mode":"savefrom-killer"}

@app.get("/streams/{video_id}")
def streams(video_id: str):
    if not re.fullmatch(r"[a-zA-Z0-9_-]{11}", video_id):
        raise HTTPException(400, "ID salah")
    
    # 1. Coba Cobalt dulu (paling cepat kayak Savefrom)
    s = get_from_cobalt(video_id)
    if s: return {"videoStreams": s, "source": "cobalt-savefrom"}
    
    # 2. Fallback yt-dlp AMPUH
    s = get_from_ytdlp(video_id)
    if s: return {"videoStreams": s, "source": "yt-dlp-ios+tv+web"}
    
    raise HTTPException(500, detail="Video ini di-private / batas umur oleh YouTube. Coba video publik lain. (Savefrom pun gagal di video ini)")
