import schedule
import time
from datetime import datetime
from upload_to_youtube import get_latest_video, upload_video

def job():
    print("\n📦 Görev başladı.")
    video = get_latest_video()
    if video:
        upload_video(video)
    else:
        print("⚠️ Yüklenecek video bulunamadı.")
    print("✅ Görev tamamlandı.\n")

# İlk çalıştırma
#job()

# 8 saatte bir çalışacak şekilde görevi planla
schedule.every(8).hours.do(job)

# Sonsuz döngü: schedule çalışırken geri sayım da göster
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
