from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
import subprocess
import json
import logging
import tempfile
import os

app = FastAPI()

# Basic logging setup
logging.basicConfig(level=logging.INFO)

@app.get("/")
def root():
    return {"message": "TikTok Downloader is running!"}

@app.get("/tiktok")
def get_video(url: str = Query(...)):
    try:
        # Log the incoming request
        logging.info(f"Request received for URL: {url}")
        
        # Run the yt-dlp command to get video information in JSON format
        result = subprocess.run(
            ['yt-dlp', '-j', url],
            capture_output=True,
            text=True,
            check=True,  # Raise CalledProcessError on non-zero exit code
            encoding='utf-8'  # Set encoding to utf-8 to handle all characters
        )
        
        # Parse the JSON output from yt-dlp
        video_json = json.loads(result.stdout)
        
        # Log the successful retrieval of video data
        logging.info(f"Video retrieved: {video_json['url']}")
        
        return {"url": video_json["url"]}
    
    except subprocess.CalledProcessError as e:
        # Handle yt-dlp errors
        logging.error(f"yt-dlp failed with error: {e.stderr}")
        return {"error": "Failed to fetch video data. Please check the URL."}
    except json.JSONDecodeError:
        # Handle JSON parsing errors
        logging.error("Failed to parse JSON response from yt-dlp.")
        return {"error": "Failed to parse video data. The URL might be incorrect."}
    except Exception as e:
        # Catch any other exceptions
        logging.error(f"Unexpected error: {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}

@app.post("/download")
async def download_video(url: str = Query(...)):
    try:
        # Log the incoming request
        logging.info(f"Download request received for URL: {url}")
        
        # Create a temporary directory to store the downloaded video
        with tempfile.TemporaryDirectory() as temp_dir:
            # Run yt-dlp to download the video file into the temporary directory
            result = subprocess.run(
                ['yt-dlp', '-o', os.path.join(temp_dir, '%(title)s.%(ext)s'), url],
                capture_output=True,
                text=True,
                check=True,
                encoding='utf-8'  # Set encoding to utf-8 for yt-dlp output
            )
            
            # Find the downloaded file in the temporary directory
            video_file = None
            for file_name in os.listdir(temp_dir):
                video_path = os.path.join(temp_dir, file_name)
                if os.path.isfile(video_path):
                    video_file = video_path
                    break
            
            if not video_file:
                return {"error": "Video download failed. No file found."}
            
            # Open the file as a streaming response
            with open(video_file, 'rb') as video:
                return StreamingResponse(video, media_type="video/mp4", headers={"Content-Disposition": f"attachment; filename={os.path.basename(video_file)}"})
        
    except subprocess.CalledProcessError as e:
        # Handle yt-dlp errors
        logging.error(f"yt-dlp failed with error: {e.stderr}")
        return {"error": "Failed to download video. Please check the URL."}
    except Exception as e:
        # Catch any other exceptions
        logging.error(f"Unexpected error: {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}

