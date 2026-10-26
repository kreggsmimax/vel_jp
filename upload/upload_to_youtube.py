"""
YouTube Upload Script - Updated for 2025

Uses refresh token from GitHub Secrets to upload videos.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import datetime

# Load environment variables
load_dotenv()

def get_authenticated_service():
    """Authenticate using refresh token from environment."""
    
    # Get credentials from GitHub Secrets
    client_id = (os.getenv('YOUTUBE_CLIENT_ID') or os.getenv('YT_CLIENT_ID', '')).strip()
    client_secret = (os.getenv('YOUTUBE_CLIENT_SECRET') or os.getenv('YT_CLIENT_SECRET', '')).strip()
    refresh_token = (os.getenv('YOUTUBE_REFRESH_TOKEN') or os.getenv('YT_REFRESH_TOKEN', '')).strip()
    
    # Debug info (masked)
    def mask(s): return f"{s[:4]}...{s[-4:]}" if s and len(s) > 8 else "MISSING"
    print(f"[youtube] Client ID: {mask(client_id)}")
    print(f"[youtube] Client Secret: {mask(client_secret)}")
    print(f"[youtube] Refresh Token: {mask(refresh_token)}")

    if not all([client_id, client_secret, refresh_token]):
        raise ValueError(
            "Missing credentials! Set these environment variables:\n"
            "  - YOUTUBE_CLIENT_ID\n"
            "  - YOUTUBE_CLIENT_SECRET\n"
            "  - YOUTUBE_REFRESH_TOKEN"
        )
    
    # Create credentials from refresh token
    creds = Credentials(
        None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=["https://www.googleapis.com/auth/youtube"]
    )
    
    try:
        # Refresh to get access token
        creds.refresh(Request())
    except Exception as e:
        if "invalid_grant" in str(e).lower():
            print("\n❌ [youtube] AUTH ERROR: Refresh token has EXPIRED or been REVOKED.")
            print("💡 SOLUTION: You must generate a NEW refresh token.")
            print("   1. Go to Google Cloud Console.")
            print("   2. Ensure your 'OAuth Consent Screen' is in 'Production' or add yourself as a test user.")
            print("   3. Run a local script to get a new refresh token.")
        raise
    
    return build('youtube', 'v3', credentials=creds)

def generate_video_metadata(category: str, num_phrases: int, phrases: list = None, lang_name: str = "Language"):
    try:
        import subprocess
        remote = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], stderr=subprocess.DEVNULL).decode().strip().lower()
        if "chin" in remote or "zh" in remote: lang_name = "Chinese"
        elif "jp" in remote or "ja" in remote or "jap" in remote: lang_name = "Japanese"
        elif "heb" in remote: lang_name = "Hebrew"
    except Exception:
        pass

    lang_lower = lang_name.lower()
    if "chin" in lang_lower or "zh" in lang_lower:
        name = "Chinese"
        flag = "🇨🇳"
        domain = "velocitychinese.com"
        pron_key = "pinyin"
        native_key = "chinese"
        keywords = "learn chinese, mandarin chinese for beginners, daily chinese phrases, hsk vocabulary, speak chinese fluently, pinyin guide, velocity chinese"
        tags = ["learn chinese", "chinese lessons", "chinese for beginners", "chinese phrases", "language learning", "chinese tutorial", "speak chinese", category.lower(), "education", "daily chinese", "velocity chinese", "chinese learning", "pinyin", "hsk 1"]
    elif "jap" in lang_lower or "ja" in lang_lower or "jp" in lang_lower:
        name = "Japanese"
        flag = "🇯🇵"
        domain = "velocityjapanese.com"
        pron_key = "romaji"
        native_key = "japanese"
        keywords = "learn japanese, japanese for beginners, daily japanese phrases, jlpt vocabulary, speak japanese fluently, romaji guide, velocity japanese"
        tags = ["learn japanese", "japanese lessons", "japanese for beginners", "japanese phrases", "language learning", "japanese tutorial", "speak japanese", category.lower(), "education", "daily japanese", "velocity japanese", "japanese learning", "romaji", "jlpt n5"]
    elif "heb" in lang_lower:
        name = "Hebrew"
        flag = "🇮🇱"
        domain = "velocityhebrew.com"
        pron_key = "transliteration"
        native_key = "hebrew"
        keywords = "learn hebrew, hebrew for beginners, daily hebrew phrases, hebrew cursive ktav, biblical hebrew, speak hebrew fluently, alef bet, velocity hebrew"
        tags = ["learn hebrew", "hebrew lessons", "hebrew for beginners", "hebrew phrases", "language learning", "hebrew tutorial", "speak hebrew", category.lower(), "education", "daily hebrew", "velocity hebrew", "hebrew learning", "hebrew cursive", "modern hebrew"]
    else:
        name = lang_name
        flag = "🌍"
        domain = f"velocity{name.lower()}.com"
        pron_key = "transliteration"
        native_key = "native"
        keywords = f"learn {name.lower()}, {name.lower()} for beginners, daily {name.lower()} phrases, velocity {name.lower()}"
        tags = [f"learn {name.lower()}", f"{name.lower()} lessons", f"{name.lower()} phrases", "language learning", category.lower(), "education", f"velocity {name.lower()}"]

    title = f"{num_phrases} Essential {name} Phrases: {category} | Learn {name} #Shorts"
    if len(title) > 95:
        title = f"{name} Phrases: {category} | Learn {name} #Shorts"

    description_lines = [
        f"{flag} Learn {name} with Velocity {name}!",
        f"👉 Free Interactive Lessons & Vocabulary Guides: https://{domain}/",
        f"📖 Read our latest {name} blog articles: https://{domain}/blog/",
        f"",
        f"📚 Category: {category}",
        f"🎯 Master {name} one phrase at a time! Today's {category} lesson:",
        f""
    ]
    if phrases:
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
        for i, phrase in enumerate(phrases[:5]):
            emoji = emojis[i] if i < len(emojis) else f"{i+1}."
            foreign_val = phrase.get(native_key) or phrase.get("target") or phrase.get("foreign") or phrase.get("chinese") or phrase.get("japanese") or phrase.get("hebrew") or ""
            pron_val = phrase.get(pron_key) or phrase.get("transliteration") or phrase.get("romaji") or phrase.get("pinyin") or phrase.get("pronunciation") or ""
            description_lines.append(f"{emoji} {phrase.get('english', '')}")
            if foreign_val:
                description_lines.append(f"   📍 {foreign_val}")
            if pron_val:
                description_lines.append(f"   🔊 [{pron_val}]")
            description_lines.append("")

    description_lines.extend([
        f"💡 Tip: Repeat each phrase out loud 3 times!",
        f"👍 Like this video if you learned something new!",
        f"💬 Comment your favorite phrase below!",
        f"🔔 Subscribe for daily {name} lessons!",
        f"",
        f"🔍 POPULAR SEARCH TOPICS:",
        f"{keywords}",
        f"",
        f"🌐 VISIT OUR WEBSITE:",
        f"https://{domain}/",
        f"",
        f"#Learn{name} #{name}Lessons #{name}ForBeginners #LanguageLearning #{name} #Education #Daily{name} #{category.replace(' ', '')} #Velocity{name} #Shorts"
    ])
    description = "\n".join(description_lines)
    return title, description, tags

def _post_comment(youtube, video_id, text):
    """Post a comment to the uploaded video."""
    print(f"[youtube] Posting comment...")
    try:
        request = youtube.commentThreads().insert(
            part="snippet",
            body={
                "snippet": {
                    "videoId": video_id,
                    "topLevelComment": {
                        "snippet": {
                            "textOriginal": text
                        }
                    }
                }
            }
        )
        response = request.execute()
        print(f"[youtube] ✅ Comment posted! ID: {response['id']}")
        print(f"[youtube] 📌 NOTE: YouTube API does not support pinning comments. Please pin manually if needed.")
        return response
    except Exception as e:
        print(f"[youtube] ❌ Failed to post comment: {e}")
        return None

def upload_to_youtube(video_path, title, description, tags=None, category_id='22'):
    """Upload video to YouTube and return result."""
    if tags is None:
        tags = ['slapstick', 'animation', 'funny']
    youtube = get_authenticated_service()
    
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': category_id
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False,
        }
    }
    
    if '#Shorts' not in body['snippet']['description']:
        body['snippet']['description'] += '\n\n#Shorts'
    
    media = MediaFileUpload(
        str(video_path),
        chunksize=-1,
        resumable=True,
        mimetype='video/mp4'
    )
    
    print(f"[youtube] Uploading: {title}")
    request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media
    )
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"[youtube] Progress: {int(status.progress() * 100)}%")
    
    print(f"[youtube] ✅ Uploaded! Video ID: {response['id']}")
    print(f"[youtube] URL: https://youtube.com/shorts/{response['id']}")
    
    # Post the title and description as a comment
    comment_text = f"🎥 {title}\n\n{description}"
    _post_comment(youtube, response['id'], comment_text)
    
    return response

def main():
    """Upload the generated video to YouTube."""
    video_file = Path('final_video.mp4')
    
    if not video_file.exists():
        print("[youtube] ❌ No video found at final_video.mp4")
        return
    
    # Simple test metadata
    title = "Slapstick Loops Daily"
    description = "#shorts #slapstick #cartoon #funny"
    tags = ['slapstick', 'cartoon', 'funny']
    
    # Upload
    try:
        upload_to_youtube(
            video_path=video_file,
            title=title,
            description=description,
            tags=tags,
            category_id='22'
        )
    except Exception as e:
        print(f"[youtube] ❌ Upload failed: {e}")
        raise

if __name__ == '__main__':
    main()
