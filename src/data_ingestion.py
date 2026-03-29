from googleapiclient.discovery import build
import re
import os

API_KEY = os.environ.get("YOUTUBE_API_KEY", "AIzaSyAnc6ioj8X4sL_t9s98ZXnaXAiA2U_Vhp")

def get_video_id(url):
    match = re.search(r"v=([a-zA-Z0-9_-]{11})", url)
    return match.group(1) if match else None

def get_comments(video_url, max_comments=200):
    video_id = get_video_id(video_url)
    if not video_id:
        return []
    try:
        youtube = build("youtube", "v3", developerKey=API_KEY)
        comments = []
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100,
            textFormat="plainText"
        )
        while request and len(comments) < max_comments:
            response = request.execute()
            for item in response.get("items", []):
                text = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                comments.append(text)
            request = youtube.commentThreads().list_next(request, response)
        return comments[:max_comments]
    except Exception as e:
        print(f"Error fetching comments: {e}")
        return []


