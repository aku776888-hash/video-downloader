from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def root():
    return {"message": "Video Downloader API from Semarang is LIVE!"}

@app.get("/health")
def health():
    return {"status": "ok"}
