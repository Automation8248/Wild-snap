import os
import requests
import random
import sys
import json
from moviepy import VideoFileClip, AudioFileClip, concatenate_audioclips

# API Keys
PIXABAY_KEY = os.getenv("PIXABAY_KEY")
FREESOUND_KEY = os.getenv("FREESOUND_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

def get_dynamic_metadata():
    """AI se Title, Caption aur Hashtags generate karna"""
    print("Generating AI Metadata...")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    
    prompt = "Generate a catchy title, a 1-sentence emotional caption, and exactly 8 trending hashtags for a short wildlife video about animals. Format: Title | Caption | Hashtags"
    
    payload = {
        "model": "google/gemini-2.0-flash-exp:free",
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload).json()
        content = response['choices'][0]['message']['content']
        parts = content.split('|')
        return {
            "title": parts[0].strip(),
            "caption": parts[1].strip(),
            "hashtags": parts[2].strip()
        }
    except:
        return {
            "title": "Amazing Wildlife",
            "caption": "Nature is truly beautiful and mysterious.",
            "hashtags": "#wildlife #nature #animals #shorts #discovery #earth #viral #beauty"
        }

def get_pixabay_video():
    url = f"https://pixabay.com/api/videos/?key={PIXABAY_KEY}&q=animals&per_page=30&video_type=film"
    data = requests.get(url).json()
    video_url = random.choice(data['hits'])['videos']['medium']['url']
    with open("raw_video.mp4", "wb") as f:
        f.write(requests.get(video_url).content)
    return "raw_video.mp4"

def get_freesound_audio():
    url = f"https://freesound.org/apiv2/search/text/?query=nature&token={FREESOUND_KEY}&fields=id,previews"
    data = requests.get(url).json()
    audio_url = random.choice(data['results'])['previews']['preview-hq-mp3']
    with open("raw_audio.mp3", "wb") as f:
        f.write(requests.get(audio_url).content)
    return "raw_audio.mp3"

def process_video(v_path, a_path):
    print("Editing video to 8 seconds...")
    video = VideoFileClip(v_path)
    audio = AudioFileClip(a_path)
    
    # 1. Duration 8 seconds par set karna
    duration = min(video.duration, 8)
    if duration < 7: duration = 7 # Minimum 7 sec
    
    # Subclip lena taaki exactly 7-8 sec ka ho
    final_video = video.subclipped(0, duration)
    
    # 2. Audio loop and set
    if audio.duration < duration:
        audio = concatenate_audioclips([audio] * 2)
    final_audio = audio.with_duration(duration)
    
    final_output = final_video.with_audio(final_audio)
    output_name = "final_short.mp4"
    final_output.write_videofile(output_name, codec="libx264", audio_codec="aac", fps=24, preset="ultrafast")
    return output_name

def upload_to_catbox(file_path):
    url = "https://catbox.moe/user/api.php"
    with open(file_path, 'rb') as f:
        response = requests.post(url, data={'reqtype': 'fileupload'}, files={'fileToUpload': f})
    return response.text

def post_content(video_url, file_path, meta):
    full_caption = f"✨ *{meta['title']}*\n\n{meta['caption']}\n\n{meta['hashtags']}"
    
    # 1. Telegram (Video + Caption)
    tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    with open(file_path, 'rb') as v:
        requests.post(tg_url, data={
            "chat_id": TELEGRAM_CHAT_ID, 
            "caption": full_caption, 
            "parse_mode": "Markdown"
        }, files={"video": v})
    
    # 2. Webhook (JSON Data)
    if WEBHOOK_URL:
        payload = {
            "video_url": video_url,
            "title": meta['title'],
            "description": meta['caption'],
            "hashtags": meta['hashtags']
        }
        requests.post(WEBHOOK_URL, json=payload)

if __name__ == "__main__":
    meta = get_dynamic_metadata()
    v = get_pixabay_video()
    a = get_freesound_audio()
    processed_v = process_video(v, a)
    catbox_link = upload_to_catbox(processed_v)
    post_content(catbox_link, processed_v, meta)
    print("Process Completed Successfully!")
