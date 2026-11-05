import re, requests, os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

app = FastAPI(title="TaufikDownloader - Auto Switch Server")

# AUTO SWITCH - ini rahasia Savefrom: dia punya 5+ server cadangan
SERVERS = [
    {"name": "co.wuk.sh (Hong Kong)", "url": "https://co.wuk.sh/api/json"},
    {"name": "api.cobalt.tools (US)", "url": "https://api.cobalt.tools/api/json"},
    {"name": "api.cobalt.tn (EU)", "url": "https://api.cobalt.tn/api/json"},
    {"name": "cobalt.canine.tools (EU)", "url": "https://cobalt.canine.tools/api/json"},
]

def try_cobalt_auto(video_id):
    yt_url = f"https://www.youtube.com/watch?v={video_id}"
    last_error = None
    for srv in SERVERS:
        try:
            print(f"Trying {srv['name']}...")
            r = requests.post(srv["url"], 
                json={"url": yt_url, "vQuality": "1080", "aFormat": "mp3", "isAudioOnly": False},
                headers={"Accept": "application/json", "Content-Type": "application/json"},
                timeout=10)
            data = r.json()
            if data.get("url"):
                return [{"quality": "1080p HD", "format": "MP4", "url": data["url"], "server": srv["name"]}]
            if data.get("status") == "error":
                last_error = data.get("text")
        except Exception as e:
            last_error = str(e)
            continue
    return []

def try_ytdlp_auto(video_id):
    try:
        import yt_dlp
        # Auto ganti client kayak Savefrom: ios -> android -> tv -> web
        clients = [
            ["ios", "android"],
            ["tv_embedded", "web"],
            ["web", "android_vr"],
        ]
        for client_set in clients:
            try:
                ydl_opts = {
                    "quiet": True, "no_warnings": True,
                    "skip_download": True, "noplaylist": True,
                    "extractor_args": {"youtube": {"player_client": client_set}}
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                    out = []
                    for f in info.get("formats", []):
                        if f.get("ext")=="mp4" and f.get("url") and f.get("vcodec")!="none" and f.get("height"):
                            h = f["height"]
                            has_audio = f.get("acodec")!="none"
                            if h>=360:
                                out.append({"quality": f"{h}p{' (no audio)' if not has_audio else ''}", "format":"MP4", "url":f["url"], "_h":h, "_a":has_audio})
                    if out:
                        out.sort(key=lambda x: (x["_a"], x["_h"]), reverse=True)
                        uniq={}
                        final=[]
                        for o in out:
                            if o["quality"] not in uniq:
                                uniq[o["quality"]]=1
                                del o["_h"]; del o["_a"]
                                final.append(o)
                        return final[:6]
            except: continue
    except Exception as e:
        print(e)
    return []

@app.get("/", include_in_schema=False)
def home():
    return FileResponse("index.html") if os.path.exists("index.html") else {"ok": True}

@app.get("/health")
def health(): return {"status":"ok","mode":"AUTO-SWITCH","servers": len(SERVERS)}

@app.get("/streams/{video_id}")
def get_streams(video_id: str):
    if not re.fullmatch(r"[a-zA-Z0-9_-]{11}", video_id):
        raise HTTPException(400, "ID salah")
    
    # 1. Auto switch antar server cobalt (paling ampuh kayak Savefrom)
    s = try_cobalt_auto(video_id)
    if s: return {"videoStreams": s, "source": f"AUTO-SWITCH: {s[0].get('server')}"}
    
    # 2. Auto switch antar client yt-dlp
    s = try_ytdlp_auto(video_id)
    if s: return {"videoStreams": s, "source": "AUTO-SWITCH: yt-dlp multi-client"}
    
    raise HTTPException(500, detail="Semua server cadangan gagal. Video ini private / copyright block di semua region. Coba video lain (dQw4w9WgXcQ pasti bisa)")
