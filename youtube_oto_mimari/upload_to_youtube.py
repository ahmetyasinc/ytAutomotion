import os
import glob
import random
import regex as re
import shutil
from datetime import datetime
import subprocess

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.exceptions import RefreshError

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# ---- YOLLAR ----
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DOWNLOADS_FOLDER = os.path.normpath(os.path.join(BASE_DIR, "..", "tiktok_oto_mimari", "indirilenler"))
TOKEN_PATH = os.path.join(BASE_DIR, "token.json")
CLIENT_SECRET_PATH = os.path.join(BASE_DIR, "client_secret.json")

# ---- METADATA ----
HASHTAG_METADATA = {
    # ... (senin sözlüğün aynen burada kalsın)
}

def safe_exists(path: str) -> bool:
    return path and os.path.exists(path)

def get_latest_video():
    folder = os.path.abspath(DOWNLOADS_FOLDER)
    mp4_files = glob.glob(os.path.join(folder, "*.mp4"))
    if not mp4_files:
        print("⚠️ Hiç .mp4 dosyası bulunamadı. Klasör:", folder)
        return None
    latest_file = max(mp4_files, key=os.path.getctime)
    latest_file = os.path.abspath(latest_file)
    print(f"🎬 Son video bulundu: {latest_file}")
    return latest_file

def _guess_ffprobe_path():
    """PATH'te yoksa imageio-ffmpeg'in klasöründen tahmin etmeyi dener."""
    from shutil import which
    p = which("ffprobe")
    if p:
        return p
    # imageio_ffmpeg ile gelen ffmpeg yolu
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        folder = os.path.dirname(ffmpeg_exe)
        # Windows için
        cand_win = os.path.join(folder, "ffprobe.exe")
        if os.path.exists(cand_win):
            return cand_win
        # Unix için
        cand_unix = os.path.join(folder, "ffprobe")
        if os.path.exists(cand_unix):
            return cand_unix
    except Exception:
        pass
    return None

def get_video_duration(video_path):
    try:
        if not safe_exists(video_path):
            raise FileNotFoundError(f"Video dosyası bulunamadı: {video_path}")

        ffprobe = _guess_ffprobe_path()
        if not ffprobe:
            print("ℹ️ ffprobe bulunamadı; süre okunamayacak (Shorts tespiti atlanacak).")
            return None

        result = subprocess.run(
            [ffprobe, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", video_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        out = (result.stdout or "").strip()
        if not out:
            # Bazı container'larda format süresi yoksa stream üzerinden dene
            result = subprocess.run(
                [ffprobe, "-v", "error", "-select_streams", "v:0",
                 "-show_entries", "stream=duration", "-of", "default=nokey=1:noprint_wrappers=1", video_path],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            out = (result.stdout or "").strip()

        return float(out) if out else None
    except Exception as e:
        print(f"⛔ Video süresi alınamadı: {e}")
        return None

def get_hashtag_from_filename(filename):
    base = os.path.basename(filename)
    # Türkçe karakterler için \w çalışır (Unicode), yine de tire vb. için genişletildi
    m = re.search(r"_([A-Za-z0-9_\-\p{L}]+)\.mp4$", base)
    if not m:
        # Daha gevşek: son _ ile .mp4 arasını al
        m = re.search(r"_(.+)\.mp4$", base)
    tag = m.group(1).strip().lower() if m else None
    # YouTube'da 'tags' alanına None koymamak için temizle
    if tag:
        # Boşlukları tire yapalım
        tag = re.sub(r"\s+", "-", tag)
    return tag

def build_metadata(tag, is_shorts):
    title, description = ("Otomatik Yükleme", "Bu video otomatik olarak yüklendi.")
    category_id = "22"

    if tag and tag in HASHTAG_METADATA:
        title, description = random.choice(HASHTAG_METADATA[tag])

    if is_shorts:
        # 100 karakter sınırını aşmamak için kırp
        if not title.endswith(" #shorts"):
            title = (title + " #shorts")[:95]  # emniyet payı
        if "#shorts" not in description:
            description += "\n#shorts"

    return title, description, category_id

def _load_credentials():
    creds = None
    if safe_exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    else:
        if not safe_exists(CLIENT_SECRET_PATH):
            raise FileNotFoundError(f"client_secret.json bulunamadı: {CLIENT_SECRET_PATH}")
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_PATH, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
    return creds

def upload_video(video_path):
    video_path = os.path.abspath(video_path)
    if not safe_exists(video_path):
        print(f"⛔ Yükleme iptal: Dosya bulunamadı -> {video_path}")
        return

    # Süre ve shorts tespiti (opsiyonel)
    duration = get_video_duration(video_path)
    is_shorts = (duration is not None and duration <= 60.0)

    tag = get_hashtag_from_filename(video_path)
    title, description, category_id = build_metadata(tag, is_shorts)

    request_body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": [t for t in [tag, "auto-upload", "tiktok"] if t],  # None atılmasın
            "categoryId": category_id
        },
        "status": {
            "privacyStatus": "public"
        }
    }

    media_file = MediaFileUpload(video_path, resumable=True)

    print("⏫ Yükleme başlatılıyor...")
    try:
        creds = _load_credentials()
        youtube = build("youtube", "v3", credentials=creds)

        request = youtube.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=media_file
        )

        response = request.execute()
        print("✅ Yükleme tamamlandı:")
        print(f"https://www.youtube.com/watch?v={response['id']}")

    except RefreshError as e:
        # invalid_grant dahil tüm refresh hataları burada
        print(f"🔒 Yetki yenileme hatası: {e}. token.json silinip yeniden yetkilendirilecek.")
        try:
            if safe_exists(TOKEN_PATH):
                os.remove(TOKEN_PATH)
        except Exception:
            pass
        # Tek seferlik yeniden giriş
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_PATH, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w", encoding="utf-8") as f:
            f.write(creds.to_json())

        youtube = build("youtube", "v3", credentials=creds)
        response = youtube.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=media_file
        ).execute()
        print("✅ Yükleme tamamlandı (yeniden yetkilendirme sonrası):")
        print(f"https://www.youtube.com/watch?v={response['id']}")

    except FileNotFoundError as e:
        print(f"⛔ Dosya/Yol hatası: {e}")
    except Exception as e:
        print(f"❌ Yükleme hatası: {e}")

if __name__ == "__main__":
    video = get_latest_video()
    if video:
        upload_video(video)
    else:
        print("⏭️ Yüklenecek video bulunamadı.")
