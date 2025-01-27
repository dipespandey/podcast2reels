import subprocess
import os
import re
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound

def download_youtube_video(url, output_path="downloaded_video.mp4"):
    """
    Downloads the best available YouTube video via yt-dlp.
    """
    try:
        command = [
            "yt-dlp",
            "-f", "best",
            "--output", output_path,
            url
        ]
        subprocess.run(command, check=True)
        return os.path.abspath(output_path)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Download failed: {e}")
        return None

def fetch_youtube_transcript(video_id, language_code='en'):
    """
    Attempts to retrieve the official transcript from YouTube.
    Returns list of dict: {text, start, duration}
    """
    try:
        transcripts = YouTubeTranscriptApi.get_transcript(
            video_id, languages=[language_code])
        return transcripts
    except NoTranscriptFound:
        return None
    except Exception as e:
        print(f"[ERROR] fetch_youtube_transcript: {e}")
        return None

def get_transcript(url):
    """
    1) Extract video ID
    2) Attempt official transcript
    """
    match = re.search(r"v=([^&]+)", url)
    if not match:
        raise ValueError("Couldn't extract video_id from URL.")
    video_id = match.group(1)

    data = fetch_youtube_transcript(video_id)
    if data:
        print("[INFO] Found official YouTube transcript.")
        return data

    print("[INFO] No official transcript found; returning None.")
    return None 