
import os
import re
import base64
import tempfile

from fastapi import FastAPI, HTTPException
import yt_dlp

app = FastAPI(title="TaufikDownloader API")

@app.get("/")
def root():
    return {
        "message": "TaufikDownloader API is LIVE!",
        "status": "online"
    }

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/streams/{video_id}")
def get_streams(video_id: str):

    # Validasi ID video YouTube
    if not re.fullmatch(r"[a-zA-Z0-9_-]{11}", video_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid YouTube video ID"
        )

    url = f"https://www.youtube.com/watch?v={video_id}"

    cookie_file = None

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "skip_download": True,
        "socket_timeout": 20,
        "retries": 2,

        # Pilih format MP4 dengan audio dan video
        "format": "best[ext=mp4][vcodec!=none][acodec!=none]/best",

    }

    try:
        # Cookie disimpan sebagai Fly.io secret
        cookies_b64 = os.getenv("YOUTUBE_COOKIES_B64")

        if cookies_b64:
            cookie_data = base64.b64decode(
                cookies_b64,
                validate=True
            )

            with tempfile.NamedTemporaryFile(
                mode="wb",
                suffix=".txt",
                delete=False
            ) as temp:
                temp.write(cookie_data)
                cookie_file = temp.name

            ydl_opts["cookiefile"] = cookie_file

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(
                url,
                download=False
            )

            formats = info.get("formats", [])

            video_streams = []

            for f in formats:

                if not f.get("url"):
                    continue

                if f.get("ext") != "mp4":
                    continue

                # Pastikan stream memiliki audio dan video
                if f.get("vcodec") == "none":
                    continue

                if f.get("acodec") == "none":
                    continue

                height = f.get("height")

                quality = (
                    f"{height}p"
                    if height
                    else f.get("format_note", "HD")
                )

                video_streams.append({
                    "quality": quality,
                    "format": "MP4",
                    "url": f["url"]
                })

            # Hilangkan kualitas duplikat
            unique = {}

            for stream in video_streams:
                unique[stream["quality"]] = stream

            video_streams = list(unique.values())

            video_streams.sort(
                key=lambda x: int(
                    re.search(r"\d+", x["quality"]).group()
                ) if re.search(r"\d+", x["quality"]) else 0,
                reverse=True
            )

            if not video_streams:
                raise HTTPException(
                    status_code=404,
                    detail="No compatible MP4 streams found."
                )

            return {
                "videoStreams": video_streams
            }

    except HTTPException:
        raise

    except Exception as e:

        error = str(e)

        if "Sign in to confirm" in error:
            raise HTTPException(
                status_code=403,
                detail="YouTube meminta autentikasi. Periksa konfigurasi cookie backend."
            )

        raise HTTPException(
            status_code=500,
            detail=error[:1000]
        )

    finally:
        if cookie_file and os.path.exists(cookie_file):
            os.remove(cookie_file)
