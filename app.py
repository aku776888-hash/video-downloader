from fastapi import FastAPI, HTTPException
import yt_dlp

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Video Downloader API from Semarang is LIVE!"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/streams/{video_id}")
def get_streams(video_id: str):
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    # Konfigurasi yt-dlp yang diperbarui agar menghindari error format
    ydl_opts = {
        'format': 'best',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}}
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            video_streams = []
            
            for f in formats:
                if f.get('url') and f.get('ext') == 'mp4':
                    video_streams.append({
                        "quality": f.get('format_note', 'HD'),
                        "format": f.get('ext', 'mp4').upper(),
                        "url": f.get('url')
                    })
            
            if not video_streams and info.get('url'):
                video_streams.append({
                    "quality": "HD",
                    "format": "MP4",
                    "url": info.get('url')
                })
            
            if not video_streams:
                raise HTTPException(status_code=404, detail="No downloadable streams found.")
                
            return {"videoStreams": video_streams}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
