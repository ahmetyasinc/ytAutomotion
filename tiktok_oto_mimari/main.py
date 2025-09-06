# scheduler.py

import time
import schedule
from itertools import cycle
from datetime import datetime
from get_latest_video import get_latest_video_url_by_hashtag
from download_video import download_video

# Kullanılacak hashtag listesi
HASHTAGS = [
    # Türkçe
    "komik", "gülmekgaranti", "şaka", "mizah", "kediler", "köpekler", "hayvansever", "aşk",
    "duygusal", "motivasyon", "girişimcilik", "bilgiler", "eğitim", "dans", "müzik", "keşfet",
    "trending", "çocuk", "tatlıçocuk", "annebebek", "shortfilm", "kısavideo", "senaryo",

    # İngilizce
    "funny", "lol", "memes", "cats", "dogs", "pets", "love", "heartbroken", "motivation",
    "inspiration", "facts", "learnontiktok", "dance", "music", "viral", "foryou", "baby", "ytshorts"
]

hashtag_iterator = cycle(HASHTAGS)

def job():
    hashtag = next(hashtag_iterator)
    print(f"\n🔁 Yeni hashtag işleniyor: #{hashtag}")

    # TikTok videosu bul
    video_url = get_latest_video_url_by_hashtag(hashtag)
    if not video_url:
        print("❌ Video bulunamadı.")
        return

    # Video indir
    download_video(video_url, hashtag)

# Schedule ayarı (8 saatte bir çalıştır)
schedule.every(8).hours.do(job)

print("⏱️ Program başlatıldı. Her 8 saatte bir video paylaşımı yapılacak...\n")

# Sonsuz döngü + geri sayım
while True:
    schedule.run_pending()

    # Sonraki çalıştırma zamanı
    next_run = schedule.next_run()
    now = datetime.now()
    remaining = (next_run - now).total_seconds()

    if remaining > 0:
        mins = int(remaining // 60)
        secs = int(remaining % 60)
        print(f"⏳ Sonraki görev {mins:02d}:{secs:02d} içinde çalışacak...", end="\r")
    else:
        print("⌛ Görev zamanında çalışacak...                             ", end="\r")

    time.sleep(1)
