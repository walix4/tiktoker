from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
import subprocess
import json
import logging
import tempfile
import os
import urllib.parse

app = FastAPI()

# Basic logging setup
logging.basicConfig(level=logging.INFO)

@app.get("/")
def root():
    return {"message": "TikTok Downloader is running!"}

@app.get("/tiktok")
def get_video(url: str = Query(...)):
    try:
        # Run the yt-dlp command with more headers to mimic browser behavior
        result = subprocess.run(
            ['yt-dlp', '-j', '--no-check-certificate', '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36', '--referer', 'https://www.tiktok.com/', '--cookies', 'cookies.txt', url],
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8'  # Set encoding to utf-8 to handle all characters
        )
        
        logging.info(f"yt-dlp output: {result.stdout}")
        
        # Parse the JSON output from yt-dlp
        video_json = json.loads(result.stdout)
        
        # Log the successful retrieval of video data
        logging.info(f"Video URL retrieved: {video_json['url']}")
        
        return {"url": video_json["url"]}
    
    except subprocess.CalledProcessError as e:
        logging.error(f"yt-dlp failed with error: {e.stderr}")
        return {"error": "Failed to fetch video data. Please check the URL."}
    except json.JSONDecodeError:
        logging.error("Failed to parse JSON response from yt-dlp.")
        return {"error": "Failed to parse video data. The URL might be incorrect."}
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}

@app.post("/download")
async def download_video(url: str = Query(...)):
    try:
        # Create a temporary directory to store the downloaded video
        with tempfile.TemporaryDirectory() as temp_dir:
            # Run yt-dlp to download the video file into the temporary directory
            result = subprocess.run(
                ['yt-dlp', '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36', '--referer', 'https://www.tiktok.com/', '--cookies', 'cookies.txt', '-o', os.path.join(temp_dir, '%(title)s.%(ext)s'), url],
                capture_output=True,
                text=True,
                check=True,
                encoding='utf-8'  # Set encoding to utf-8 for yt-dlp output
            )
            
            logging.info(f"yt-dlp download output: {result.stdout}")
            
            # Find the downloaded file in the temporary directory
            video_file_path = None
            for file_name in os.listdir(temp_dir):
                video_path = os.path.join(temp_dir, file_name)
                if os.path.isfile(video_path):
                    video_file_path = video_path
                    break

            if not video_file_path:
                logging.error("No video file found after download.")
                return {"error": "Failed to download video. No video file found."}
            
            logging.info(f"Video downloaded successfully: {video_file_path}")
            
            # Open the file as a streaming response
            video_file = open(video_file_path, 'rb')
            return StreamingResponse(video_file, media_type="video/mp4", headers={"Content-Disposition": f"attachment; filename={urllib.parse.quote(os.path.basename(video_file_path))}"})
        
    except subprocess.CalledProcessError as e:
        logging.error(f"yt-dlp download failed with error: {e.stderr}")
        return {"error": "Failed to download video. Please check the URL."}
    except Exception as e:
        logging.error(f"Unexpected error during download: {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}
