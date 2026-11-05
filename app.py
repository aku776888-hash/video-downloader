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
    ydl_opts = {'format': 'best', 'noplaylist': True}
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            video_streams = []
            
            # Ambil format mp4 yang tersedia
            for f in formats:
                if f.get('url') and f.get('ext') == 'mp4':
                    video_streams.append({
                        "quality": f.get('format_note', 'HD'),
                        "format": f.get('ext', 'mp4').upper(),
                        "url": f.get('url')
                    })
            
            # Jika daftar format kosong, gunakan direct url utama
            if not video_streams and info.get('url'):
                video_streams.append({
                    "quality": "HD",
                    "format": "MP4",
                    "url": info.get('url')
                })
                
            return {"videoStreams": video_streams}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
