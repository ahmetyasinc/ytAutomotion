import yt_dlp
import os
from datetime import datetime

def download_video(video_url: str, hashtag: str, output_dir: str = "indirilenler"):
    os.makedirs(output_dir, exist_ok=True)

    # Şu anki tarih ve saat bilgisi: YYYY-MM-DD_HH-MM-SS
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"tiktok_video_{timestamp}_{hashtag}.mp4"
    filepath = os.path.join(output_dir, filename)

    ydl_opts = {
        'outtmpl': filepath,
        'quiet': False,
        'force_generic_extractor': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        print(f"⬇️ Video indiriliyor: {filename}")
        ydl.download([video_url])
        print(f"✅ İndirildi: {filepath}")
