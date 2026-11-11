"""VELOCITY JAPANESE - language pack, brand and motion design constants."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

OUTPUT_DIR = BASE_DIR / "output"
LESSONS_DIR = OUTPUT_DIR / "lessons"
HISTORY_DIR = OUTPUT_DIR / "history"
SCENE_DIR = BASE_DIR / "scene"

VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30

# ---------------------------------------------------------------- brand

BRAND = "VELOCITY JAPANESE"
BRAND_LOCKUP_TOP = "VELOCITY"
BRAND_LOCKUP_BOTTOM = "JAPANESE"
HANDLE = "@velocityjapanese"
MASCOT_NAME = "Velo"

# ==== LANGUAGE PACK START ====
LANGUAGE = {
    "code": "ja",
    "name": "Japanese",
    "native_name": "日本語",
    "history_key": "japanese",
    "english_voice": "en-US-AvaNeural",
    "english_fallback_voice": "en-US-GuyNeural",
    "native_voice": "ja-JP-NanamiNeural",
    "native_fallback_voice": "ja-JP-KeitaNeural",
    "native_engine": "edge",
    "native_lang_code": "ja",
    "english_rate": "-2%",
    "native_rate": "-6%",
    "english_pitch": "+0Hz",
    "native_pitch": "+0Hz",
    "native_label": "日本語",
    "translit_label": "ROMAJI",
    "greeting": "こんにちは!",
    "encouragement": "すごい!",
    "rtl": False,
    "char_tiles": True,
    "script_font": "NotoSansJP-Bold.ttf",
}
# ==== LANGUAGE PACK END ====

AI_MODEL = os.getenv("AI_MODEL", "gemini-fast")
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "")

# ---------------------------------------------------------------- timing (seconds)

INTRO_DURATION = 4.0
OUTRO_DURATION = 5.2
EN_CARD_IN = 0.55
GAP_EN_NATIVE = 0.5
NATIVE_CARD_LEAD = 0.35
GAP_BEFORE_REPEAT = 0.8
TAIL_HOLD = 1.4
MAX_REEL_DURATION = 88.0

# ---------------------------------------------------------------- palette

INK = "#3C3C3C"
MUTED = "#8A8A8A"
CREAM = "#FFF8E7"
GREEN = "#58CC02"
GREEN_DARK = "#46A302"
GREEN_DEEP = "#3D8F00"
BLUE = "#1CB0F6"
PURPLE = "#A560E8"
ORANGE = "#FF7A00"
RED = "#FF4B4B"
YELLOW = "#F5A700"
TEAL = "#00A889"
PINK = "#E056A0"

PALETTE = [GREEN, BLUE, PURPLE, ORANGE, RED, YELLOW, TEAL, PINK]

# ---------------------------------------------------------------- categories
# (english, native, icon, accent)

# ==== CATEGORY TABLE START ====
CATEGORY_TABLE = [
    ("Greetings", "あいさつ", "hand", "#1CB0F6"),
    ("Basic Phrases", "基本フレーズ", "chat", "#58CC02"),
    ("Common Expressions", "よく使う表現", "chat", "#1CB0F6"),
    ("Travel", "旅行", "plane", "#1CB0F6"),
    ("Restaurant", "レストラン", "fork", "#FF7A00"),
    ("Shopping", "買い物", "bag", "#E056A0"),
    ("Emergency", "緊急", "siren", "#FF4B4B"),
    ("Family Terms", "家族", "heart", "#E056A0"),
    ("Numbers", "数字", "hash", "#A560E8"),
    ("Time", "時間", "clock", "#00A889"),
    ("Motivation", "やる気", "rocket", "#A560E8"),
    ("Love", "愛", "heart", "#FF4B4B"),
    ("Success", "成功", "trophy", "#F5A700"),
    ("Wisdom", "知恵", "book", "#A560E8"),
    ("Happiness", "幸せ", "smile", "#F5A700"),
    ("Self Improvement", "自己啓発", "leaf", "#58CC02"),
    ("Gratitude", "感謝", "heart", "#FF7A00"),
    ("Friendship", "友情", "users", "#00A889"),
    ("Hope", "希望", "sun", "#FF7A00"),
    ("Creativity", "創造性", "palette", "#E056A0"),
    ("Inner Peace", "内なる平和", "lotus", "#00A889"),
    ("Confidence", "自信", "shield", "#1CB0F6"),
    ("Perseverance", "忍耐", "mountain", "#FF7A00"),
    ("Inspiration", "インスピレーション", "sparkles", "#A560E8"),
    ("Positive Life", "ポジティブな人生", "sun", "#58CC02"),
    ("Courage", "勇気", "shield", "#FF4B4B"),
    ("Kindness", "優しさ", "heart", "#E056A0"),
    ("Patience", "辛抱", "hourglass", "#00A889"),
    ("Forgiveness", "許し", "hands", "#FF7A00"),
    ("Strength", "強さ", "dumbbell", "#FF4B4B"),
    ("Joy", "喜び", "smile", "#F5A700"),
    ("Balance", "バランス", "scale", "#00A889"),
    ("Growth", "成長", "sprout", "#58CC02"),
    ("Purpose", "目的", "target", "#A560E8"),
    ("Mindfulness", "マインドフルネス", "lotus", "#00A889"),
    ("Daily Routine", "日課", "calendar", "#1CB0F6"),
    ("Weather", "天気", "cloud", "#1CB0F6"),
    ("Feelings", "感情", "smile", "#E056A0"),
    ("Food", "食べ物", "fork", "#FF7A00"),
    ("Health", "健康", "heart", "#58CC02"),
    ("Work", "仕事", "briefcase", "#1CB0F6"),
    ("Technology", "テクノロジー", "chip", "#A560E8"),
    ("Nature", "自然", "leaf", "#58CC02"),
    ("Animals", "動物", "paw", "#FF7A00"),
    ("Colors", "色", "palette", "#E056A0"),
    ("Directions", "道案内", "compass", "#1CB0F6"),
    ("Body Parts", "体の部位", "hand", "#00A889"),
    ("Clothes", "服", "shirt", "#E056A0"),
    ("Music", "音楽", "music", "#A560E8"),
    ("Sports", "スポーツ", "ball", "#FF7A00"),
    ("Holidays", "祝日", "gift", "#FF4B4B"),
    ("Education", "教育", "book", "#1CB0F6"),
    ("Culture", "文化", "globe", "#00A889"),
    ("Finance", "金融", "coin", "#58CC02"),
    ("Relationships", "人間関係", "users", "#E056A0"),
]
# ==== CATEGORY TABLE END ====

CATEGORIES = [c[0] for c in CATEGORY_TABLE]
CATEGORIES_NATIVE = {c[0]: c[1] for c in CATEGORY_TABLE}
CATEGORY_META = {c[0]: {"native": c[1], "icon": c[2], "accent": c[3]} for c in CATEGORY_TABLE}
MAX_RECENT_CATEGORIES = 25

# ==== HASHTAGS START ====
HASHTAGS = [
    "#learnjapanese",
    "#japaneselessons",
    "#japaneseforbeginners",
    "#languagelearning",
    "#japanesevocabulary",
    "#velocityjapanese",
    "#dailyjapanese",
    "#japanese",
    "#learnlanguages",
    "#speakjapanese",
    "#bilingual",
    "#languagetips",
]
# ==== HASHTAGS END ====
