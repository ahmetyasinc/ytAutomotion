import requests
from config import RAPIDAPI_KEY, RAPIDAPI_HOST

def get_challenge_id(hashtag: str) -> str | None:
    url = f"https://{RAPIDAPI_HOST}/challenge/search"
    querystring = {"keywords": hashtag}
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST
    }

    response = requests.get(url, headers=headers, params=querystring)
    #print("🔍 API yanıtı:", response.text)

    if response.status_code != 200:
        print("Challenge search hatası:", response.text)
        return None

    try:
        data = response.json()
        challenge_id = data["data"]["challenge_list"][0]["id"]
        print("✅ Challenge ID bulundu:", challenge_id)
        return challenge_id
    except Exception as e:
        print("Challenge ID alınamadı. Hata:", str(e))
        return None


def get_latest_video_url_by_hashtag(hashtag: str) -> str | None:
    challenge_id = get_challenge_id(hashtag)
    if not challenge_id:
        return None

    url = f"https://{RAPIDAPI_HOST}/challenge/posts"
    querystring = {
        "challenge_id": challenge_id,
        "count": "1"
    }
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST
    }

    response = requests.get(url, headers=headers, params=querystring)
    #print("📦 Challenge Posts Yanıtı:", response.text)

    if response.status_code != 200:
        print("Challenge post hatası:", response.text)
        return None

    try:
        data = response.json()
        video_url = data["data"]["videos"][0]["play"]  # ✅ DOĞRU YOL
        print("🎥 Video URL:", video_url)
        return video_url
    except Exception as e:
        print("Video URL alınamadı. Hata:", str(e))
        return None


