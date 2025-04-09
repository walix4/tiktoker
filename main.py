
from fastapi import FastAPI, Query
import subprocess
import json

app = FastAPI()

@app.get("/")
def root():
    return {"message": "TikTok Downloader is running!"}

@app.get("/tiktok")
def get_video(url: str = Query(...)):
    try:
        result = subprocess.run(
            ['yt-dlp', '-j', url],
            capture_output=True,
            text=True
        )
        video_json = json.loads(result.stdout)
        return {"url": video_json["url"]}
    except Exception as e:
        return {"error": str(e)}
