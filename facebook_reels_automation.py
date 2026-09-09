"""
Facebook Reels Automation - Bilingual English/Japanese Content Generator
IMPROVED VERSION: Better backgrounds, English categories, no repeats, Velocity Japanese branding
"""

import os
import sys
import re
import json
import random
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "gemini-fast")

def has_japanese_characters(text: str) -> bool:
    """Check if string contains at least one Japanese character (Hiragana, Katakana, or Kanji)."""
    if not text:
        return False
    return bool(re.search(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]', text))

def sanitize_text(text: str, is_romaji: bool = False) -> str:
    """Clean text string, removing high-plane emoji artifacts and normalizing punctuation."""
    if not text:
        return ""
    text = re.sub(r'[\r\n]+', ' ', text)
    # Remove emoji & symbols that cause tofu rectangle boxes
    text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
    text = re.sub(r'[\u2600-\u26ff\u2700-\u27bf\u2300-\u23ff]', '', text)
    if is_romaji:
        trans = {
            '！': '!', '？': '?', '、': ', ', '。': '. ', '・': ' ',
            '〜': '~', '～': '~', '「': '"', '」': '"', '『': '"', '』': '"',
            '（': '(', '）': ')', '［': '[', '］': ']', '　': ' '
        }
        for k, v in trans.items():
            text = text.replace(k, v)
        text = re.sub(r'\s+', ' ', text)
    return text.strip()

# Directories
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
IMAGES_DIR = OUTPUT_DIR / "images"
AUDIO_DIR = OUTPUT_DIR / "audio"
VIDEO_DIR = OUTPUT_DIR / "video"
HISTORY_DIR = OUTPUT_DIR / "history"

for d in [OUTPUT_DIR, IMAGES_DIR, AUDIO_DIR, VIDEO_DIR, HISTORY_DIR]:
    d.mkdir(exist_ok=True)

# Video settings (9:16 vertical)
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30

# English category names (for American/European learners)
# Essential Japanese Learning + Viral Culture + Real-Life Practical Categories (inspired by HablaVerse)
CATEGORIES_ENGLISH = [
    # Core Japanese Learning & Daily Life
    "Greetings", "Basic Phrases", "Common Expressions", "Food & Dining",
    "Travel Japanese", "Restaurant Japanese", "Shopping Japanese", "Directions & Transit",
    "Emergency Japanese", "Family Terms", "Numbers Japanese", "Time Japanese",
    "Weather & Seasons", "Emotions & Feelings", "Work & Business", "Health & Body",
    "Hobbies & Activities",
    # Viral Japanese Culture & Native Expressions (High Retention & Social Shares)
    "Tokyo Street Japanese", "Native Slang", "Anime Quotes", "Foodie Reactions",
    "Kawaii Japanese", "Izakaya & Nightlife", "Convenience Store Hacks", "Heartfelt Romance",
    "Polite vs Casual", "Untranslatable Japanese", "Zen Wisdom", "Deep Encouragement"
]

# Japanese translations for display
CATEGORIES_JAPANESE = {
    # Core Japanese Learning & Daily Life
    "Greetings": "日常の挨拶",
    "Basic Phrases": "基本フレーズ",
    "Common Expressions": "よく使う表現",
    "Food & Dining": "グルメ・食事",
    "Travel Japanese": "旅行日本語",
    "Restaurant Japanese": "レストラン日本語",
    "Shopping Japanese": "ショッピング日本語",
    "Directions & Transit": "道案内・電車案内",
    "Emergency Japanese": "緊急日本語",
    "Family Terms": "家族用語",
    "Numbers Japanese": "数字日本語",
    "Time Japanese": "時間日本語",
    "Weather & Seasons": "天気・四季の表現",
    "Emotions & Feelings": "感情・リアクション",
    "Work & Business": "ビジネス・職場の表現",
    "Health & Body": "健康・体の表現",
    "Hobbies & Activities": "趣味・エンタメ",
    # Viral Japanese Culture & Native Expressions
    "Tokyo Street Japanese": "東京ストリート会話",
    "Native Slang": "リアル若者言葉",
    "Anime Quotes": "アニメ名言・名セリフ",
    "Foodie Reactions": "絶品グルメ表現",
    "Kawaii Japanese": "可愛いリアクション",
    "Izakaya & Nightlife": "居酒屋・夜の会話",
    "Convenience Store Hacks": "コンビニで使える技",
    "Heartfelt Romance": "胸キュン・愛の言葉",
    "Polite vs Casual": "丁寧語とタメ口",
    "Untranslatable Japanese": "言葉の美学・日本語の深み",
    "Zen Wisdom": "禅の知恵・日本の精神",
    "Deep Encouragement": "心に響く励まし",
}

# Viral hook styles for engagement (from HablaVerse & customized for Japanese learning reels)
VIRAL_STYLES = [
    "surprising cultural fact",
    "common beginner mistake correction",
    "quick native speaker hack",
    "must-know essential phrase",
    "local Tokyo insider secret",
    "travel & transit hack",
    "flirty & romantic phrase",
    "funny & relatable expression",
    "cultural insight & nuance",
    "slang & casual banter",
    "foodie reaction that impresses locals",
    "anime vs real life difference",
    "polite vs casual switch"
]

# Edge TTS voices
ENGLISH_VOICE = "en-US-GuyNeural"
JAPANESE_VOICE = "ja-JP-NanamiNeural"

# Phrase history file (NEVER delete this!)
PHRASE_HISTORY_FILE = HISTORY_DIR / "all_generated_phrases.json"

# Recent categories file (for rotation - prevents category repeats)
RECENT_CATEGORIES_FILE = HISTORY_DIR / "recent_categories.json"
MAX_RECENT_CATEGORIES = 15  # Track last 15 categories to avoid repeats


# ============== PHRASE HISTORY MANAGEMENT (Prevent Repeats) ==============

def load_phrase_history():
    """Load all previously generated phrases"""
    if PHRASE_HISTORY_FILE.exists():
        with open(PHRASE_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"phrases": [], "last_updated": None}


def save_phrase_history(data):
    """Save phrase history"""
    data["last_updated"] = datetime.now().isoformat()
    with open(PHRASE_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def is_phrase_duplicate(new_phrase: str, used_phrases: list, similarity_threshold: float = 0.6) -> bool:
    """Check if phrase is too similar to previously used phrases using Jaccard word similarity."""
    new_words = set(re.findall(r'\w+', new_phrase.lower()))
    if len(new_words) < 3:
        for used in used_phrases:
            if new_phrase.lower() in used.lower() or used.lower() in new_phrase.lower():
                return True
        return False

    for used in used_phrases:
        used_words = set(re.findall(r'\w+', used.lower()))
        if not used_words:
            continue
        intersection = len(new_words.intersection(used_words))
        union = len(new_words.union(used_words))
        if union > 0 and (intersection / union) >= similarity_threshold:
            return True
    return False


def is_phrase_used(english_phrase: str) -> bool:
    """Check if phrase was already generated (exact match or near-duplicate)"""
    history = load_phrase_history()
    phrases = history.get("phrases", [])
    used_list = [p.get("english", "") for p in phrases if p.get("english")]
    english_lower = english_phrase.lower().strip()
    # 1. Exact match check against recent 800 phrases
    for u in used_list[-800:]:
        if u.lower().strip() == english_lower:
            return True
    # 2. Fuzzy Jaccard duplicate check against recent 300 phrases
    return is_phrase_duplicate(english_phrase, used_list[-300:], similarity_threshold=0.6)


def add_phrases_to_history(phrases, category):
    """Add new phrases to history"""
    history = load_phrase_history()
    for phrase in phrases:
        history["phrases"].append({
            "english": phrase["english"],
            "japanese": phrase["japanese"],
            "romaji": phrase.get("romaji", ""),
            "category": category,
            "generated_at": datetime.now().isoformat()
        })
    save_phrase_history(history)
    print(f"[history] Added {len(phrases)} phrases to history (total: {len(history['phrases'])})")


# ============== CATEGORY ROTATION MANAGEMENT (Prevent Repeats) ==============

def load_recent_categories():
    """Load recently used categories"""
    if RECENT_CATEGORIES_FILE.exists():
        with open(RECENT_CATEGORIES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"recent_categories": [], "last_updated": None}


def save_recent_categories(data):
    """Save recent categories"""
    data["last_updated"] = datetime.now().isoformat()
    with open(RECENT_CATEGORIES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_available_category():
    """Get a category that hasn't been used recently - ensures rotation across ALL 35 categories"""
    recent_data = load_recent_categories()
    recent = recent_data.get("recent_categories", [])

    # Get all categories that are NOT in recent list
    available = [cat for cat in CATEGORIES_ENGLISH if cat not in recent]

    # If all categories have been used recently, clear the oldest ones
    if not available:
        # Keep only the most recent 5, clear the rest
        recent_data["recent_categories"] = recent[-5:]
        save_recent_categories(recent_data)
        available = [cat for cat in CATEGORIES_ENGLISH if cat not in recent_data["recent_categories"]]
        print(f"[rotation] All categories used recently - cleared old ones, {len(available)} available")

    # Random selection from available (non-recent) categories
    selected = random.choice(available)

    # Add to recent list
    recent.append(selected)

    # Keep only the last MAX_RECENT_CATEGORIES
    if len(recent) > MAX_RECENT_CATEGORIES:
        recent = recent[-MAX_RECENT_CATEGORIES:]

    recent_data["recent_categories"] = recent
    save_recent_categories(recent_data)

    print(f"[rotation] Selected '{selected}' ({len(available)} available, {len(recent)} in recent history)")
    return selected


# ============== CONTENT GENERATION ==============

def generate_phrases(category_english: str, num_phrases: int = 5) -> list:
    """Generate unique bilingual phrases with natural pauses, ensuring no repeats and valid Japanese."""

    category_japanese = CATEGORIES_JAPANESE.get(category_english, "日本語")

    # Priority models on Pollinations: gemini-fast prioritized first, with resilient fallbacks
    models_to_try = ["gemini-fast", "openai", "mistral"]
    if AI_MODEL in models_to_try:
        models_to_try.remove(AI_MODEL)
        models_to_try.insert(0, AI_MODEL)
    elif AI_MODEL:
        models_to_try.insert(0, AI_MODEL)

    import requests

    # Category-specific viral styles to guarantee 100% realistic, natural, authentic Japanese
    CATEGORY_VIRAL_STYLES = {
        "Heartfelt Romance": [
            "sweet romantic confession", "heartfelt romantic expression", "subtle Japanese love nuance", "cute date conversation"
        ],
        "Tokyo Street Japanese": [
            "real modern street slang", "casual banter between friends", "youth culture reaction in Shibuya/Shinjuku"
        ],
        "Native Slang": [
            "trendy youth slang", "viral Japanese slang on social media", "funny casual exclamation"
        ],
        "Foodie Reactions": [
            "mind-blowing food reaction", "compliment to the chef", "authentic gourmet expression"
        ],
        "Convenience Store Hacks": [
            "smart konbini ordering trick", "convenience store survival phrase", "quick counter secret"
        ],
        "Anime Quotes": [
            "iconic heroic determination line", "memorable emotional quote", "classic famous catchphrase"
        ],
        "Izakaya & Nightlife": [
            "drinking party toast & reaction", "ordering favorite bar snacks", "casual pub conversation"
        ],
        "Kawaii Japanese": [
            "adorable friendly reaction", "cute compliment", "wholesome happy expression"
        ],
        "Polite vs Casual": [
            "how to switch from formal to friendly", "polite staff phrase vs casual friend reply"
        ],
        "Untranslatable Japanese": [
            "untranslatable cultural aesthetic (mono no aware, komorebi, ikigai)"
        ],
        "Zen Wisdom": [
            "mindful present-moment wisdom", "peaceful acceptance philosophy"
        ],
        "Deep Encouragement": [
            "gentle supportive words for tough times", "warm comforting reassurance"
        ]
    }

    CORE_PRACTICAL_STYLES = [
        "must-know essential phrase that locals appreciate",
        "common beginner mistake correction (how natives actually say it)",
        "quick native speaker hack (natural conversational shortcut)",
        "real-life practical situation natives encounter daily",
        "polite, natural phrase that makes Japanese locals smile",
        "insider tip for sounding natural and respectful in Japan"
    ]

    # Pick dynamic viral hook style tailored to this category
    category_styles = CATEGORY_VIRAL_STYLES.get(category_english, CORE_PRACTICAL_STYLES)
    viral_style = random.choice(category_styles)

    # Build exclusion list from recent history so model actively avoids repeating recent phrases
    history = load_phrase_history()
    recent_used = [p.get("english", "") for p in history.get("phrases", []) if p.get("english")]
    exclusion_note = ""
    if recent_used:
        sample_avoid = recent_used[-20:]
        exclusion_note = f"\n\nAVOID these phrases (already recently used):\n" + "\n".join(f"- {p}" for p in sample_avoid)

    system_prompt = (
        "You are an elite native Japanese language educator creating practical educational content for social media (TikTok, Reels, Shorts). "
        "Generate 100% REALISTIC, NATURAL, everyday Japanese phrases that people actually speak in real daily life in Japan. "
        "STRICT REALISM & AUTHENTICITY RULES: "
        "1. Real-life authenticity: Every phrase must be something a real person would genuinely say in Japan today. "
        "   NEVER generate awkward, bizarre, stiff, or unrealistic sentences (e.g. no calling cashiers 'darling', no stiff textbook jargon). "
        "2. NO placeholders whatsoever: NO [Name], NO [Item], NO brackets [], NO fill-in-the-blanks (____). "
        "   Always use concrete, natural words (e.g., 'Nice to meet you, I'm Ken' or 'Do you have this in a medium size?'). "
        "3. Contextual Politeness: "
        "   - Use natural polite Japanese (Desu/Masu) for stores, restaurants, transit, strangers, and office. "
        "   - Use natural casual Japanese only for street slang, anime quotes, and close friends. "
        "4. High retention: Short, punchy (max 8-12 words in English), with natural commas so text-to-speech sounds like a real human. "
        f"5. Strict Category Focus: Every single phrase MUST directly match the theme of '{category_english}'. "
        "   DO NOT write generic motivational or inspirational quotes unless the category explicitly asks for it."
    )

    user_prompt = (
        f"Create {num_phrases * 2} 100% REALISTIC, ESSENTIAL, and VIRAL {category_english} ({category_japanese}) phrases for English speakers learning Japanese.\n"
        f"Focus strictly on realistic real-world usage for '{category_english}'.\n\n"
        f"For each phrase, provide:\n"
        f"1. english: Natural, conversational English (COMPLETE sentence with NO blanks or underscores, MAX 8-12 WORDS).\n"
        f"2. japanese: Authentic native Japanese characters (Kanji, Hiragana, Katakana). NEVER empty, NEVER Romaji in this field.\n"
        f"3. romaji: Clean Hepburn Romaji pronunciation for English speakers.\n\n"
        f"CRITICAL RULES:\n"
        f"- DIRECT CATEGORY RELEVANCE & REALISM: Phrases MUST be 100% authentic and realistic for '{category_english}' (how people genuinely speak in Japan).\n"
        f"- NO placeholders (NO [Name], NO [Item]), NO brackets, NO fill-in-the-blanks. Always use concrete words.\n"
        f"- Natural pauses: Use natural commas in English so text-to-speech has great pacing.\n"
        f"- Style angle: {viral_style}.\n"
        f"{exclusion_note}\n\n"
        f"Return strictly as a JSON array of objects:\n"
        f'[\n  {{"english": "...", "japanese": "...", "romaji": "..."}}\n]'
    )

    for model in models_to_try:
        for attempt in range(2):
            try:
                print(f"  [content] Requesting '{category_english}' ({viral_style}) via {model} (attempt {attempt + 1})...")
                url = "https://gen.pollinations.ai/v1/chat/completions"
                headers = {
                    "Content-Type": "application/json"
                }
                if POLLINATIONS_API_KEY:
                    headers["Authorization"] = f"Bearer {POLLINATIONS_API_KEY}"

                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 1.0
                }

                response = requests.post(url, headers=headers, json=payload, timeout=60)
                response.raise_for_status()

                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()

                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                phrases = None
                try:
                    phrases = json.loads(content)
                except Exception as parse_err:
                    print(f"  [content] Direct JSON parse failed ({parse_err}), attempting regex object recovery for {model}...")
                    obj_matches = re.findall(r'\{[^{}]*(?:"english"|"English")[^{}]*(?:"japanese"|"Japanese"|"kanji")[^{}]*\}', content, re.DOTALL)
                    if obj_matches:
                        recovered = []
                        for m in obj_matches:
                            try:
                                recovered.append(json.loads(m))
                            except Exception:
                                continue
                        if recovered:
                            phrases = recovered
                            print(f"  [content] Successfully recovered {len(phrases)} phrases via regex!")

                if isinstance(phrases, dict):
                    # In case model wrapped it in an object like {"phrases": [...]}
                    for k in ["phrases", "items", "data", "result"]:
                        if k in phrases and isinstance(phrases[k], list):
                            phrases = phrases[k]
                            break

                if not isinstance(phrases, list):
                    continue

                unique_phrases = []
                for p in phrases:
                    if not isinstance(p, dict):
                        continue

                    eng = sanitize_text(p.get("english") or p.get("English") or "")
                    jap = sanitize_text(p.get("japanese") or p.get("Japanese") or p.get("kanji") or p.get("nihongo") or p.get("translation") or "")
                    rom = sanitize_text(p.get("romaji") or p.get("Romaji") or p.get("pronunciation") or p.get("transliteration") or "", is_romaji=True)

                    if not eng or len(eng.split()) > 15:
                        continue

                    # CRITICAL: Verify Japanese characters exist
                    if not has_japanese_characters(jap):
                        print(f"  [content] Skipping item missing Japanese kana/kanji: {eng} -> '{jap}'")
                        continue

                    # CRITICAL: Reject placeholders like [Name], [Item], brackets, or blanks
                    if re.search(r'[\[\]{}|_\_]', eng) or re.search(r'[\[\]{}|_\_]', jap):
                        print(f"  [content] Skipping item with placeholders/brackets: {eng} -> '{jap}'")
                        continue

                    if not is_phrase_used(eng):
                        unique_phrases.append({
                            "english": eng,
                            "japanese": jap,
                            "romaji": rom or eng
                        })

                    if len(unique_phrases) >= num_phrases:
                        break

                if len(unique_phrases) >= num_phrases:
                    selected = unique_phrases[:num_phrases]
                    add_phrases_to_history(selected, category_english)
                    return selected

            except Exception as e:
                print(f"[content] {model} attempt {attempt + 1} failed: {e}")

    # Fallback to fresh phrases
    print("[content] Using fallback phrases...")
    return get_fresh_fallback_phrases(category_english, num_phrases)


def get_fresh_fallback_phrases(category: str, num_phrases: int) -> list:
    """Get fallback phrases, filtering out used ones"""

    all_fallbacks = {
        # Essential Japanese Learning Categories
        "Greetings": [
            {"english": "Hello, nice to meet you.", "japanese": "こんにちは、はじめまして。", "romaji": "Konnichiwa, hajimemashite."},
            {"english": "Good morning!", "japanese": "おはようございます！", "romaji": "Ohayou gozaimasu!"},
            {"english": "Good evening, how are you?", "japanese": "こんばんは、お元気ですか？", "romaji": "Konbanwa, ogenki desu ka?"},
            {"english": "See you tomorrow!", "japanese": "また明日！", "romaji": "Mata ashita!"},
            {"english": "Goodbye, take care.", "japanese": "さようなら、お元気で。", "romaji": "Sayounara, ogenki de."},
            {"english": "How have you been?", "japanese": "お元気でしたか？", "romaji": "Ogenki deshita ka?"},
            {"english": "Long time no see.", "japanese": "久しぶりです。", "romaji": "Hisashiburi desu."},
            {"english": "Have a nice day!", "japanese": "良い一日を！", "romaji": "Yoi ichinichi o!"},
            {"english": "See you later!", "japanese": "また後で！", "romaji": "Mata atode!"},
            {"english": "Welcome to Japan!", "japanese": "日本へようこそ！", "romaji": "Nihon e youkoso!"},
            {"english": "Talk to you soon.", "japanese": "また話しましょう。", "romaji": "Mata hanashimashou."},
        ],
        "Basic Phrases": [
            {"english": "Thank you very much.", "japanese": "ありがとうございます。", "romaji": "Arigatou gozaimasu."},
            {"english": "You're welcome, no problem.", "japanese": "どういたしまして。", "romaji": "Dou itashimashite."},
            {"english": "I'm sorry, excuse me.", "japanese": "すみません、ごめんなさい。", "romaji": "Sumimasen, gomennasai."},
            {"english": "Yes, that's correct.", "japanese": "はい、そうです。", "romaji": "Hai, sou desu."},
            {"english": "No, I don't think so.", "japanese": "いいえ、ちがいます。", "romaji": "Iie, chigaimasu."},
            {"english": "Please give me this.", "japanese": "これをください。", "romaji": "Kore o kudasai."},
            {"english": "I don't understand.", "japanese": "わかりません。", "romaji": "Wakarimasen."},
            {"english": "Please speak slowly.", "japanese": "ゆっくり話してください。", "romaji": "Yukkuri hanashite kudasai."},
            {"english": "Can you repeat that?", "japanese": "もう一度言ってください。", "romaji": "Mou ichido itte kudasai."},
            {"english": "I understand now.", "japanese": "わかりました。", "romaji": "Wakarimashita."},
            {"english": "What does this mean?", "japanese": "これはどういう意味ですか？", "romaji": "Kore wa dou iu imi desu ka?"},
            {"english": "Is that okay?", "japanese": "大丈夫ですか？", "romaji": "Daijoubu desu ka?"},
            {"english": "Wait a moment, please.", "japanese": "ちょっと待ってください。", "romaji": "Chotto matte kudasai."},
            {"english": "Let's go together.", "japanese": "一緒に行きましょう。", "romaji": "Issho ni ikimashou."},
        ],
        "Common Expressions": [
            {"english": "How are you doing today?", "japanese": "今日はお元気ですか？", "romaji": "Kyou wa ogenki desu ka?"},
            {"english": "I'm fine, thank you.", "japanese": "元気です、ありがとう。", "romaji": "Genki desu, arigatou."},
            {"english": "What's your name?", "japanese": "お名前は何ですか？", "romaji": "Onamae wa nan desu ka?"},
            {"english": "My name is...", "japanese": "私の名前は...です。", "romaji": "Watashi no namae wa... desu."},
            {"english": "Nice to meet you too.", "japanese": "こちらこそ、はじめまして。", "romaji": "Kochira koso, hajimemashite."},
        ],
        "Travel Japanese": [
            {"english": "Where is the bathroom?", "japanese": "トイレはどこですか？", "romaji": "Toire wa doko desu ka?"},
            {"english": "How do I get there?", "japanese": "どうやって行きますか？", "romaji": "Douyatte ikimasu ka?"},
            {"english": "I need a taxi, please.", "japanese": "タクシーが必要です。", "romaji": "Takushii ga hitsuyou desu."},
            {"english": "Take me to the hotel.", "japanese": "ホテルまでお願いします。", "romaji": "Hoteru made onegaishimasu."},
            {"english": "How much does it cost?", "japanese": "いくらですか？", "romaji": "Ikura desu ka?"},
        ],
        "Restaurant Japanese": [
            {"english": "Can I see the menu?", "japanese": "メニューを見せてください。", "romaji": "Menyu o misete kudasai."},
            {"english": "This looks delicious!", "japanese": "美味しそうですね！", "romaji": "Oishisou desu ne!"},
            {"english": "Water, please.", "japanese": "お水をください。", "romaji": "Omizu o kudasai."},
            {"english": "Check, please.", "japanese": "お会計をお願いします。", "romaji": "Okaikei o onegaishimasu."},
            {"english": "It was delicious!", "japanese": "ごちそうさまでした！", "romaji": "Gochisousama deshita!"},
        ],
        "Shopping Japanese": [
            {"english": "How much is this?", "japanese": "これはいくらですか？", "romaji": "Kore wa ikura desu ka?"},
            {"english": "Can I try this on?", "japanese": "試着してもいいですか？", "romaji": "Shichaku shite mo ii desu ka?"},
            {"english": "Do you have a smaller size?", "japanese": "もっと小さいサイズはありますか？", "romaji": "Motto chiisai saizu wa arimasu ka?"},
            {"english": "I'll take this one.", "japanese": "これをお願いします。", "romaji": "Kore o onegaishimasu."},
            {"english": "Can I pay by card?", "japanese": "カードで払えますか？", "romaji": "Kaado de haraemasu ka?"},
        ],
        "Emergency Japanese": [
            {"english": "Help me, please!", "japanese": "助けてください！", "romaji": "Tasukete kudasai!"},
            {"english": "Call the police!", "japanese": "警察を呼んでください！", "romaji": "Keisatsu o yonde kudasai!"},
            {"english": "I need a doctor.", "japanese": "医者が必要です。", "romaji": "Isha ga hitsuyou desu."},
            {"english": "Where is the hospital?", "japanese": "病院はどこですか？", "romaji": "Byouin wa doko desu ka?"},
            {"english": "I'm lost, can you help?", "japanese": "道に迷いました、助けてくれますか？", "romaji": "Michi ni mayoimashita, tasukete kuremasu ka?"},
        ],
        "Family Terms": [
            {"english": "This is my mother.", "japanese": "これは私の母です。", "romaji": "Kore wa watashi no haha desu."},
            {"english": "This is my father.", "japanese": "これは私の父です。", "romaji": "Kore wa watashi no chichi desu."},
            {"english": "I have an older brother.", "japanese": "私には兄がいます。", "romaji": "Watashi ni wa ani ga imasu."},
            {"english": "I have a younger sister.", "japanese": "私には妹がいます。", "romaji": "Watashi ni wa imouto ga imasu."},
            {"english": "These are my parents.", "japanese": "これは私の両親です。", "romaji": "Kore wa watashi no ryoushin desu."},
        ],
        "Numbers Japanese": [
            {"english": "One, two, three.", "japanese": "一、二、三。", "romaji": "Ichi, ni, san."},
            {"english": "Four, five, six.", "japanese": "四、五、六。", "romaji": "Yon, go, roku."},
            {"english": "Seven, eight, nine, ten.", "japanese": "七、八、九、十。", "romaji": "Nana, hachi, kyuu, juu."},
            {"english": "What number is this?", "japanese": "これはいくつですか？", "romaji": "Kore wa ikutsu desu ka?"},
            {"english": "Give me two, please.", "japanese": "二つください。", "romaji": "Futatsu kudasai."},
        ],
        "Time Japanese": [
            {"english": "What time is it?", "japanese": "今何時ですか？", "romaji": "Ima nanji desu ka?"},
            {"english": "It's three o'clock.", "japanese": "三時です。", "romaji": "Sanji desu."},
            {"english": "See you at noon.", "japanese": "正午に会いましょう。", "romaji": "Shougo ni aimashou."},
            {"english": "I'll be there in five minutes.", "japanese": "5 分後に行きます。", "romaji": "Go-fun-go ni ikimasu."},
            {"english": "What day is today?", "japanese": "今日は何曜日ですか？", "romaji": "Kyou wa nan'youbi desu ka?"},
        ],
        # Viral & Cultural Phenomenon Categories
        "Untranslatable Japanese": [
            {"english": "Cherish every unrepeatable encounter.", "japanese": "一期一会の出会いを大切に。", "romaji": "Ichigo ichie no deai o taisetsu ni."},
            {"english": "Finding beauty in imperfection.", "japanese": "侘び寂びの心を感じる。", "romaji": "Wabi-sabi no kokoro o kanjiru."},
            {"english": "Sunlight filtering through trees.", "japanese": "木漏れ日がとても綺麗ですね。", "romaji": "Komorebi ga totemo kirei desu ne."},
            {"english": "Finding your true reason for being.", "japanese": "自分だけの生きがいを見つけよう。", "romaji": "Jibun dake no ikigai o mitsukeyou."},
            {"english": "Healing with gold, stronger than before.", "japanese": "金継ぎのように、傷も美しさに変わる。", "romaji": "Kintsugi no you ni, kizu mo utsukushisa ni kawaru."},
        ],
        "Anime Quotes": [
            {"english": "I will never give up, no matter what.", "japanese": "絶対に諦めない、何があっても。", "romaji": "Zettai ni akiramenai, nani ga attemo."},
            {"english": "Believe in the you that believes in yourself.", "japanese": "自分を信じる自分を信じろ。", "romaji": "Jibun o shinjiru jibun o shinjiro."},
            {"english": "I will protect what matters most.", "japanese": "一番大切なものを守り抜く。", "romaji": "Ichiban taisetsu na mono o mamorinuku."},
            {"english": "Even in darkness, light always shines.", "japanese": "暗闇の中でも、必ず光は射す。", "romaji": "Kurayami no naka demo, kanarazu hikari wa sasu."},
            {"english": "Our true story begins right now.", "japanese": "ここから、本当の物語が始まる。", "romaji": "Koko kara, hontou no monogatari ga hajimaru."},
        ],
        "Zen Wisdom": [
            {"english": "A quiet mind, like clear water.", "japanese": "明鏡止水の心を持つ。", "romaji": "Meikyou shisui no kokoro o motsu."},
            {"english": "Every single day is a good day.", "japanese": "日々是好日、今日を愛そう。", "romaji": "Nichi nichi kore koujitsu, kyou o aisou."},
            {"english": "Live completely in this present moment.", "japanese": "今この瞬間に全力を尽くす。", "romaji": "Ima kono shunkan ni zenryoku o tsukusu."},
            {"english": "True richness lies in simplicity.", "japanese": "簡素の中にこそ、真の豊かさがある。", "romaji": "Kanso no naka ni koso, shin no yutakasa ga aru."},
            {"english": "Let your attachments drift away freely.", "japanese": "雲のように、執着を手放す。", "romaji": "Kumo no you ni, shuuchaku o tebanasu."},
        ],
        "Heartfelt Romance": [
            {"english": "Please stay by my side, always.", "japanese": "ずっとそばにいてほしい。", "romaji": "Zutto soba ni ite hoshii."},
            {"english": "The moon is beautiful tonight, isn't it?", "japanese": "今夜は月がとても綺麗ですね。", "romaji": "Konya wa tsuki ga totemo kirei desu ne."},
            {"english": "I am so grateful to have met you.", "japanese": "あなたに出会えて、本当によかった。", "romaji": "Anata ni deaete, hontou ni yokatta."},
            {"english": "Whenever I see you, my heart races.", "japanese": "あなたを見るたび、胸がドキドキします。", "romaji": "Anata o miru tabi, mune ga dokidoki shimasu."},
            {"english": "You bring warmth into my world.", "japanese": "あなたが私の世界を温かくしてくれる。", "romaji": "Anata ga watashi no sekai o atatakaku shite kureru."},
        ],
        "Native Slang": [
            {"english": "Are you seriously telling the truth?", "japanese": "マジで言ってるの？", "romaji": "Maji de itteru no?"},
            {"english": "That is insanely amazing!", "japanese": "それ、ヤバすぎるでしょ！", "romaji": "Sore, yaba sugiru desho!"},
            {"english": "No way, you must be kidding!", "japanese": "嘘でしょ、信じられない！", "romaji": "Uso desho, shinjirarenai!"},
            {"english": "As expected of you, you're the best!", "japanese": "さすが、頼りになるね！", "romaji": "Sasuga, tayori ni naru ne!"},
            {"english": "I totally, completely agree with that!", "japanese": "それな、完全に同感！", "romaji": "Sore na, kanzen ni doukan!"},
        ],
        "Deep Encouragement": [
            {"english": "You don't have to carry it all alone.", "japanese": "一人で抱え込まなくて大丈夫だよ。", "romaji": "Hitori de kakae komana kute daijoubu da yo."},
            {"english": "Take it easy, at your own pace.", "japanese": "焦らず、自分のペースで進もう。", "romaji": "Aserazu, jibun no peesu de susumou."},
            {"english": "Your best is more than enough today.", "japanese": "今日の頑張りは、十分素晴らしい。", "romaji": "Kyou no ganbari wa, juubun subarashii."},
            {"english": "After the heaviest rain comes the rainbow.", "japanese": "やまない雨は、絶対にない。", "romaji": "Yamanai ame wa, zettai ni nai."},
            {"english": "Be proud of how far you've come.", "japanese": "ここまで歩んできた自分を誇ろう。", "romaji": "Koko made ayunde kita jibun o hokorou."},
        ],
        "Food & Dining": [
            {"english": "I'd like to order ramen, please.", "japanese": "ラーメンをお願いします。", "romaji": "Raamen o onegaishimasu."},
            {"english": "This sushi is incredibly fresh!", "japanese": "この寿司、信じられないほど新鮮！", "romaji": "Kono sushi, shinjirarenai hodo shinsen!"},
            {"english": "Is this dish spicy at all?", "japanese": "この料理は辛いですか？", "romaji": "Kono ryouri wa karai desu ka?"},
            {"english": "Can I have another beer, please?", "japanese": "ビールをもう一杯ください。", "romaji": "Biiru o mou ippai kudasai."},
            {"english": "Thank you for the delicious meal!", "japanese": "ごちそうさまでした、美味しかったです！", "romaji": "Gochisousama deshita, oishikatta desu!"},
        ],
        "Tokyo Street Japanese": [
            {"english": "Are you seriously doing this right now?", "japanese": "マジで今それやるの？", "romaji": "Maji de ima sore yaru no?"},
            {"english": "That is insanely cool, show me!", "japanese": "それ、ヤバいくらいかっこいい！見せて！", "romaji": "Sore, yabai kurai kakkoii! Misete!"},
            {"english": "Let's meet up at Shibuya crossing.", "japanese": "渋谷のスクランブル交差点で合流しよう。", "romaji": "Shibuya no sukuranburu kousaten de gouryuu shiyou."},
            {"english": "I totally agree with that idea.", "japanese": "それな、完全にその通り。", "romaji": "Sore na, kanzen ni sono toori."},
            {"english": "That was so hilarious, I can't stop laughing.", "japanese": "ウケる、笑いが止まらないんだけど。", "romaji": "Ukeru, warai ga tomaranai n da kedo."},
        ],
        "Foodie Reactions": [
            {"english": "This broth is insanely rich and flavorful!", "japanese": "このスープ、めちゃくちゃ濃厚でうまい！", "romaji": "Kono suupu, mechakucha noukou de umai!"},
            {"english": "It literally melts in your mouth!", "japanese": "口の中でとろける美味しさ！", "romaji": "Kuchi no naka de torokeru oishisa!"},
            {"english": "The balance of flavors is perfection.", "japanese": "味のバランスが完璧です。", "romaji": "Aji no baransu ga kampeki desu."},
            {"english": "I could eat this every single day.", "japanese": "これ、毎日でも食べられます。", "romaji": "Kore, mainichi demo taberaremasu."},
            {"english": "The texture is wonderfully crispy and light.", "japanese": "食感がサクサクで最高です。", "romaji": "Shokkan ga sakusaku de saikou desu."},
        ],
        "Kawaii Japanese": [
            {"english": "That is so adorable, I love it!", "japanese": "それ、めっちゃ可愛い！大好き！", "romaji": "Sore, meccha kawaii! Daisuki!"},
            {"english": "Look at that cute little puppy!", "japanese": "あの子犬、すごく可愛くない？", "romaji": "Ano koinu, sugoku kawaikunai?"},
            {"english": "Your outfit is super stylish and cute.", "japanese": "今日のコーデ、超可愛いね。", "romaji": "Kyou no koode, chou kawaii ne."},
            {"english": "My heart is completely melting right now.", "japanese": "キュンキュンして胸がいっぱい。", "romaji": "Kyunkyun shite mune ga ippai."},
            {"english": "Thank you so much, you're the sweetest!", "japanese": "本当にありがとう、優しすぎる！", "romaji": "Hontou ni arigatou, yasashisugiru!"},
        ],
        "Izakaya & Nightlife": [
            {"english": "Cheers to everyone, let's have fun tonight!", "japanese": "みんなで乾杯！今夜は楽しもう！", "romaji": "Minna de kampai! Konya wa tanoshimou!"},
            {"english": "Could we get five skewers of yakitori?", "japanese": "焼き鳥を五本お願いします。", "romaji": "Yakitori o gohon onegaishimasu."},
            {"english": "What is the recommended drink tonight?", "japanese": "今夜のおすすめのお酒は何ですか？", "romaji": "Konya no osusume no osake wa nan desu ka?"},
            {"english": "Can we get another round of highballs?", "japanese": "ハイボールのおかわりをお願いします。", "romaji": "Haibooru no okawari o onegaishimasu."},
            {"english": "Let's split the bill evenly.", "japanese": "割り勘にしましょう。", "romaji": "Warikan ni shimashou."},
        ],
        "Convenience Store Hacks": [
            {"english": "No bag needed, I have my own.", "japanese": "レジ袋は大丈夫です、持ってます。", "romaji": "Rejibukuro wa daijoubu desu, mottemasu."},
            {"english": "Could you warm up this bento, please?", "japanese": "このお弁当を温めていただけますか？", "romaji": "Kono obentou o atatamete itadakemasu ka?"},
            {"english": "Can I pay with Suica card?", "japanese": "Suica で払えますか？", "romaji": "Suica de haraemasu ka?"},
            {"english": "Please give me one piece of fried chicken.", "japanese": "ファミチキを一つください。", "romaji": "Famichiki o hitotsu kudasai."},
            {"english": "Can I have a spoon and chopsticks?", "japanese": "スプーンとお箸を付けてください。", "romaji": "Supuun to ohashi o tsukete kudasai."},
        ],
        "Directions & Transit": [
            {"english": "Excuse me, which line goes to Tokyo station?", "japanese": "すみません、東京駅行きはどの線ですか？", "romaji": "Sumimasen, Toukyou-eki yuki wa dono sen desu ka?"},
            {"english": "Is this platform for the Yamanote line?", "japanese": "このホームは山手線ですか？", "romaji": "Kono houmu wa Yamanote-sen desu ka?"},
            {"english": "Where can I recharge my transit card?", "japanese": "ICカードはどこでチャージできますか？", "romaji": "Aishii kaado wa doko de chaaji dekimasu ka?"},
            {"english": "Go straight and turn left at the corner.", "japanese": "まっすぐ行って、角を左に曲がってください。", "romaji": "Massugu itte, kado o hidari ni magatte kudasai."},
            {"english": "How many stops until Shinjuku?", "japanese": "新宿まであと何駅ですか？", "romaji": "Shinjuku made ato nan'eki desu ka?"},
        ],
        "Polite vs Casual": [
            {"english": "Thank you so much vs Thanks a bunch!", "japanese": "ありがとうございます / ありがとね！", "romaji": "Arigatou gozaimasu / Arigato ne!"},
            {"english": "Is that true? vs No way, really?", "japanese": "本当ですか？ / マジで？", "romaji": "Hontou desu ka? / Maji de?"},
            {"english": "Excuse me vs Sorry about that!", "japanese": "失礼します / ごめんね！", "romaji": "Shitsurei shimasu / Gomen ne!"},
            {"english": "Good morning formal vs Morning casual!", "japanese": "おはようございます / おはよー！", "romaji": "Ohayou gozaimasu / Ohayoo!"},
            {"english": "Delicious formal vs Yummy casual!", "japanese": "美味しいです / うまっ！", "romaji": "Oishii desu / Uma'!"},
        ],
        "Weather & Seasons": [
            {"english": "The cherry blossoms are blooming beautifully today.", "japanese": "今日は桜がとても綺麗に咲いています。", "romaji": "Kyou wa sakura ga totemo kirei ni saiteimasu."},
            {"english": "It is surprisingly hot outside today!", "japanese": "今日は外が意外と暑いですね！", "romaji": "Kyou wa soto ga igai to atsui desu ne!"},
            {"english": "Don't forget your umbrella, it might rain.", "japanese": "雨が降るかもしれないので傘を忘れずに。", "romaji": "Ame ga furu kamo shirenai node kasa o wasurezu ni."},
            {"english": "The autumn leaves look absolutely stunning.", "japanese": "紅葉が信じられないほど鮮やかです。", "romaji": "Kouyou ga shinjirarenai hodo azayaka desu."},
            {"english": "The weather is perfect for a walk.", "japanese": "散歩するのに最高の天気ですね。", "romaji": "Sampo suru no ni saikou no tenki desu ne."},
        ],
        "Emotions & Feelings": [
            {"english": "I am so relieved to hear that!", "japanese": "それを聞いて、本当に安心しました！", "romaji": "Sore o kiite, hontou ni anshin shimashita!"},
            {"english": "I am so excited for this weekend!", "japanese": "今週末が楽しみで待ちきれない！", "romaji": "Konshuumatsu ga tanoshimi de machikirenai!"},
            {"english": "What a pleasant surprise, thank you!", "japanese": "嬉しいサプライズ、ありがとうございます！", "romaji": "Ureshii sapuraizu, arigatou gozaimasu!"},
            {"english": "I feel so grateful for your kindness.", "japanese": "あなたの優しさに心から感謝しています。", "romaji": "Anata no yasashisa ni kokoro kara kansha shiteimasu."},
            {"english": "Don't worry, everything will turn out fine.", "japanese": "大丈夫、きっとすべて上手くいきます。", "romaji": "Daijoubu, kitto subete umaku ikimasu."},
        ],
        "Work & Business": [
            {"english": "Thank you for your hard work today.", "japanese": "今日もお疲れ様でした。", "romaji": "Kyou mo otsukaresama deshita."},
            {"english": "Excuse me for leaving before you.", "japanese": "お先に失礼します。", "romaji": "Osaki ni shitsurei shimasu."},
            {"english": "Could you check this document, please?", "japanese": "この書類をご確認いただけますか？", "romaji": "Kono shorui o gokakunin itadakemasu ka?"},
            {"english": "I will send you the email shortly.", "japanese": "後ほどメールをお送りいたします。", "romaji": "Nochihodo meeru o o-okuri itashimasu."},
            {"english": "Thank you for your continuous support.", "japanese": "いつもお世話になっております。", "romaji": "Itsumo osewa ni natte orimasu."},
        ],
        "Health & Body": [
            {"english": "I have a slight headache today.", "japanese": "今日は少し頭痛がします。", "romaji": "Kyou wa sukoshi zutsuu ga shimasu."},
            {"english": "Take good care of yourself and rest.", "japanese": "お大事に、ゆっくり休んでくださいね。", "romaji": "Odaiji ni, yukkuri yasunde kudasai ne."},
            {"english": "Do you have any stomach medicine?", "japanese": "胃腸薬はありますか？", "romaji": "Ichouyaku wa arimasu ka?"},
            {"english": "I feel completely refreshed after sleeping well.", "japanese": "しっかり寝て、すっかり元気になりました。", "romaji": "Shikkari nete, sukkari genki ni narimashita."},
            {"english": "Please stay hydrated during hot days.", "japanese": "暑い日はしっかり水分補給してください。", "romaji": "Atsui hi wa shikkari suibun hokyuu shite kudasai."},
        ],
        "Hobbies & Activities": [
            {"english": "Let's go to karaoke after work!", "japanese": "仕事の後にカラオケに行きましょう！", "romaji": "Shigoto no ato ni karaoke ni ikimashou!"},
            {"english": "I love listening to Japanese music.", "japanese": "日本の音楽を聴くのが大好きです。", "romaji": "Nihon no ongaku o kiku no ga daisuki desu."},
            {"english": "What video games do you play recently?", "japanese": "最近どんなゲームをやっていますか？", "romaji": "Saikin donna geemu o yatteimasu ka?"},
            {"english": "Taking photos around Tokyo is so fun.", "japanese": "東京の街で写真を撮るのが楽しいです。", "romaji": "Toukyou no machi de shashin o toru no ga tanoshii desu."},
            {"english": "I enjoy watching anime on weekends.", "japanese": "週末にアニメを見るのが楽しみです。", "romaji": "Shuumatsu ni anime o miru no ga tanoshimi desu."},
        ],
    }

    try:
        from fallback_phrases import FALLBACK_PHRASES as EXTERNAL_FALLBACKS
    except Exception:
        EXTERNAL_FALLBACKS = {}

    category_aliases = {
        "Food & Dining": "Restaurant Japanese",
        "Directions & Transit": "Direction Japanese",
        "Weather & Seasons": "Weather Japanese",
        "Emotions & Feelings": "Feelings Japanese",
        "Work & Business": "Work Japanese",
        "Health & Body": "Health Japanese",
        "Hobbies & Activities": "Hobbies Japanese",
    }

    fallbacks = (
        all_fallbacks.get(category)
        or all_fallbacks.get(category_aliases.get(category, ""))
        or EXTERNAL_FALLBACKS.get(category)
        or EXTERNAL_FALLBACKS.get(category_aliases.get(category, ""))
        or all_fallbacks.get("Common Expressions", [])
    )
    fresh_phrases = [p for p in fallbacks if not is_phrase_used(p["english"])]

    # If all unused phrases for this category are exhausted, recycle from fallbacks
    if len(fresh_phrases) < num_phrases:
        remaining = [p for p in fallbacks if p not in fresh_phrases]
        random.shuffle(remaining)
        fresh_phrases.extend(remaining[:num_phrases - len(fresh_phrases)])

    # If still not enough, pool from other categories
    if len(fresh_phrases) < num_phrases:
        all_pool = []
        for cat_list in all_fallbacks.values():
            all_pool.extend(cat_list)
        random.shuffle(all_pool)
        fresh_phrases.extend(all_pool[:num_phrases - len(fresh_phrases)])

    result = []
    for p in fresh_phrases[:num_phrases]:
        result.append({
            "english": sanitize_text(p.get("english", "")),
            "japanese": sanitize_text(p.get("japanese", "")),
            "romaji": sanitize_text(p.get("romaji", ""), is_romaji=True)
        })
    return result


# ============== AUDIO GENERATION ==============

async def generate_single_audio(text: str, voice: str, output_path: str) -> bool:
    """Generate audio using Edge TTS with strict verification"""
    if not text or not text.strip():
        return False
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text.strip(), voice)
        await communicate.save(output_path)
        out = Path(output_path)
        if out.exists() and out.stat().st_size > 500:
            return True
        return False
    except Exception as e:
        print(f"    TTS error: {e}")
        return False


def generate_all_audio(phrases: list, output_dir: str):
    """Generate audio for all phrases with proper timing and seamless concatenation"""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_files = []

    for i, phrase in enumerate(phrases):
        english_file = output_dir / f"english_{i}.mp3"
        japanese_file = output_dir / f"japanese_{i}.mp3"
        pause_file = output_dir / f"pause_{i}.mp3"
        combined_file = output_dir / f"combined_{i}.mp3"

        print(f"\n  Phrase {i+1}:")
        print(f"    EN: {phrase['english']}")
        print(f"    JP: {phrase['japanese']}")

        # Generate English audio
        en_success = asyncio.run(generate_single_audio(phrase["english"], ENGLISH_VOICE, str(english_file)))
        if en_success:
            print(f"    ✓ English: {english_file.name}")
        else:
            print(f"    ⚠️ English TTS unavailable, generating clean silence")
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "2.0", "-c:a", "libmp3lame", "-b:a", "192k", str(english_file)]
            subprocess.run(cmd, capture_output=True)

        # Generate Japanese audio
        jp_success = asyncio.run(generate_single_audio(phrase["japanese"], JAPANESE_VOICE, str(japanese_file)))
        if jp_success:
            print(f"    ✓ Japanese: {japanese_file.name}")
        else:
            print(f"    ⚠️ Japanese TTS unavailable, generating clean silence")
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "2.0", "-c:a", "libmp3lame", "-b:a", "192k", str(japanese_file)]
            subprocess.run(cmd, capture_output=True)

        # Generate 0.5s pause audio
        pause_between = 0.5
        cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", str(pause_between), "-c:a", "libmp3lame", "-b:a", "192k", str(pause_file)]
        subprocess.run(cmd, capture_output=True)

        # Get ACTUAL durations
        en_duration = get_audio_duration(str(english_file))
        jp_duration = get_audio_duration(str(japanese_file))
        total_duration = en_duration + pause_between + jp_duration

        print(f"    ⏱️  Total: {total_duration:.2f}s (EN: {en_duration:.2f}s + pause: {pause_between}s + JP: {jp_duration:.2f}s)")

        # Combine audio files (English + Pause + Japanese) with normalized stereo 44.1kHz
        cmd = [
            "ffmpeg", "-y",
            "-i", str(english_file),
            "-i", str(pause_file),
            "-i", str(japanese_file),
            "-filter_complex",
            "[0:a]aformat=sample_rates=44100:channel_layouts=stereo[a0];"
            "[1:a]aformat=sample_rates=44100:channel_layouts=stereo[a1];"
            "[2:a]aformat=sample_rates=44100:channel_layouts=stereo[a2];"
            "[a0][a1][a2]concat=n=3:v=0:a=1[out]",
            "-map", "[out]",
            "-c:a", "libmp3lame",
            "-b:a", "192k",
            str(combined_file)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0 or not combined_file.exists() or combined_file.stat().st_size == 0:
            concat_file = output_dir / f"concat_{i}.txt"
            with open(concat_file, "w", encoding="utf-8") as f:
                f.write(f"file '{english_file.as_posix()}'\n")
                f.write(f"file '{pause_file.as_posix()}'\n")
                f.write(f"file '{japanese_file.as_posix()}'\n")

            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(concat_file),
                "-c:a", "libmp3lame",
                "-ar", "44100",
                "-ac", "2",
                "-b:a", "192k",
                str(combined_file)
            ]
            subprocess.run(cmd, capture_output=True)
            if concat_file.exists():
                concat_file.unlink()

        actual_duration = get_audio_duration(str(combined_file))
        print(f"    ✓ Combined verified: {actual_duration:.2f}s")

        audio_files.append({
            "index": i,
            "english": str(english_file),
            "japanese": str(japanese_file),
            "combined": str(combined_file),
            "duration": actual_duration,
            "en_duration": en_duration,
            "jp_duration": jp_duration
        })

    print(f"\n[audio] ✓ Generated {len(audio_files)} phrase audios")
    return audio_files


def get_audio_duration(audio_file: str) -> float:
    """Get audio duration in seconds"""
    if not Path(audio_file).exists() or Path(audio_file).stat().st_size == 0:
        return 2.0
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        val = float(result.stdout.strip())
        return val if val > 0 else 2.0
    except Exception:
        return 2.0


def create_final_narration(audio_files: list, output_file: str) -> bool:
    """Combine all audio files with fallback re-encoding"""
    output_path = Path(output_file)
    valid_files = [Path(a["combined"]) for a in audio_files if Path(a["combined"]).exists() and Path(a["combined"]).stat().st_size > 500]
    if not valid_files:
        raise RuntimeError("No valid combined audio files to create final narration")

    n = len(valid_files)
    print(f"[audio] Combining {n} audio files...")

    concat_file = output_path.parent / "narration_list.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for p in valid_files:
            path_str = str(p.resolve()).replace("\\", "/").replace("'", "'\\''")
            f.write(f"file '{path_str}'\n")

    # Attempt 1: Fast stream copy
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c:a", "copy", str(output_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Attempt 2: Re-encode with standard MP3 settings
    if result.returncode != 0 or not output_path.exists() or output_path.stat().st_size == 0:
        print("[audio] Stream copy concat failed, re-encoding narration with libmp3lame...")
        cmd2 = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file),
            "-c:a", "libmp3lame", "-ar", "44100", "-ac", "2", "-b:a", "192k",
            str(output_path)
        ]
        result2 = subprocess.run(cmd2, capture_output=True, text=True)
        if result2.returncode != 0:
            print(f"[audio] Re-encode failed: {result2.stderr[-400:] if result2.stderr else ''}")

    if concat_file.exists():
        concat_file.unlink()

    if output_path.exists() and output_path.stat().st_size > 0:
        size = output_path.stat().st_size
        print(f"\n[audio] ✓ Final narration: {output_path.name} ({size/1024:.1f} KB)")
        return True

    raise RuntimeError(f"Narration audio creation failed: {output_file}")


# ============== IMAGE GENERATION ==============

def create_impressive_background(category_english: str):
    """Create stunning gradient background with geometric patterns and glow"""
    from PIL import Image, ImageDraw

    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT))
    draw = ImageDraw.Draw(img)

    # HIGH CONTRAST vibrant gradients for all learning & viral categories
    category_colors = {
        # Core Japanese Learning & Daily Life
        "Greetings": [(70, 130, 180), (255, 140, 0), (255, 255, 0), (255, 99, 71)],  # Steel Blue → Orange → Yellow → Tomato
        "Basic Phrases": [(60, 179, 113), (255, 215, 0), (144, 238, 144), (255, 140, 0)],  # Medium Sea Green → Gold → Light Green → Orange
        "Common Expressions": [(138, 43, 226), (255, 20, 147), (75, 0, 130), (255, 105, 180)],  # Dark Violet → Deep Pink → Dark Purple → Hot Pink
        "Food & Dining": [(255, 69, 0), (255, 140, 0), (255, 215, 0), (220, 20, 60)],  # Red Orange → Orange → Gold → Crimson
        "Travel Japanese": [(0, 191, 255), (255, 255, 0), (70, 130, 180), (255, 215, 0)],  # Deep Sky Blue → Yellow → Steel Blue → Gold
        "Restaurant Japanese": [(255, 99, 71), (255, 215, 0), (220, 20, 60), (255, 140, 0)],  # Tomato → Gold → Crimson → Orange
        "Shopping Japanese": [(255, 105, 180), (0, 100, 80), (255, 192, 203), (0, 200, 160)],  # Hot Pink → Dark Teal → Pink → Medium Teal
        "Directions & Transit": [(30, 144, 255), (0, 206, 209), (70, 130, 180), (255, 215, 0)],  # Dodger Blue → Dark Turquoise → Steel Blue → Gold
        "Emergency Japanese": [(255, 0, 0), (139, 0, 0), (255, 69, 0), (220, 20, 60)],  # Red → Dark Red → Red Orange → Crimson
        "Family Terms": [(255, 182, 193), (138, 43, 226), (255, 160, 122), (75, 0, 130)],  # Light Pink → Dark Purple → Light Salmon → Dark Purple
        "Numbers Japanese": [(255, 215, 0), (0, 0, 139), (255, 140, 0), (70, 130, 180)],  # Gold → Dark Blue → Orange → Steel Blue
        "Time Japanese": [(0, 0, 100), (255, 255, 0), (70, 130, 180), (255, 215, 0)],  # Dark Blue → Yellow → Steel Blue → Gold
        "Weather & Seasons": [(64, 224, 208), (255, 182, 193), (135, 206, 235), (255, 105, 180)],  # Turquoise → Light Pink → Sky Blue → Hot Pink
        "Emotions & Feelings": [(255, 105, 180), (138, 43, 226), (255, 165, 0), (75, 0, 130)],  # Hot Pink → Purple → Orange → Dark Purple
        "Work & Business": [(47, 79, 79), (70, 130, 180), (255, 215, 0), (0, 128, 128)],  # Dark Slate Gray → Steel Blue → Gold → Teal
        "Health & Body": [(46, 139, 87), (255, 99, 71), (152, 251, 152), (178, 34, 34)],  # Sea Green → Tomato → Pale Green → Firebrick
        "Hobbies & Activities": [(255, 20, 147), (30, 144, 255), (255, 215, 0), (138, 43, 226)],  # Deep Pink → Dodger Blue → Gold → Purple
        # Viral Japanese Culture & Native Expressions
        "Tokyo Street Japanese": [(138, 43, 226), (0, 206, 209), (255, 20, 147), (25, 25, 112)],  # Purple → Cyan → Hot Pink → Midnight Blue (Cyberpunk Tokyo)
        "Native Slang": [(255, 69, 0), (148, 0, 211), (255, 215, 0), (0, 0, 128)],  # Orange Red → Violet → Gold → Navy
        "Anime Quotes": [(255, 0, 128), (0, 0, 139), (255, 215, 0), (75, 0, 130)],  # Hot Pink → Dark Blue → Gold → Dark Purple
        "Foodie Reactions": [(255, 140, 0), (255, 0, 0), (255, 215, 0), (139, 0, 0)],  # Orange → Red → Gold → Dark Red
        "Kawaii Japanese": [(255, 192, 203), (255, 105, 180), (255, 240, 245), (186, 85, 211)],  # Pink → Hot Pink → Lavender Blush → Orchid
        "Izakaya & Nightlife": [(184, 134, 11), (139, 0, 0), (255, 165, 0), (47, 79, 79)],  # Dark Goldenrod → Dark Red → Orange → Dark Slate
        "Convenience Store Hacks": [(0, 168, 150), (242, 100, 25), (245, 245, 245), (31, 36, 33)],  # Teal → Vibrant Orange → Off-white → Charcoal
        "Heartfelt Romance": [(255, 20, 147), (139, 0, 0), (255, 182, 193), (75, 0, 130)],  # Deep Pink → Dark Red → Light Pink → Dark Purple
        "Polite vs Casual": [(72, 61, 139), (255, 140, 0), (106, 90, 205), (255, 215, 0)],  # Dark Slate Blue → Orange → Slate Blue → Gold
        "Untranslatable Japanese": [(112, 128, 144), (218, 165, 32), (47, 79, 79), (255, 228, 181)],  # Slate Gray → Goldenrod → Dark Slate → Moccasin
        "Zen Wisdom": [(47, 79, 79), (218, 165, 32), (107, 142, 35), (245, 245, 220)],  # Dark Slate → Goldenrod → Olive Drab → Beige
        "Deep Encouragement": [(255, 127, 80), (75, 0, 130), (255, 215, 0), (138, 43, 226)],  # Coral → Dark Purple → Gold → Blue Violet
    }

    colors = category_colors.get(category_english, [(138, 43, 226), (75, 0, 130), (255, 20, 147), (147, 112, 219)])

    # Create smooth multi-stop gradient
    for y in range(VIDEO_HEIGHT):
        ratio = y / VIDEO_HEIGHT
        if ratio < 0.33:
            r = int(colors[0][0] + (colors[1][0] - colors[0][0]) * (ratio * 3))
            g = int(colors[0][1] + (colors[1][1] - colors[0][1]) * (ratio * 3))
            b = int(colors[0][2] + (colors[1][2] - colors[0][2]) * (ratio * 3))
        elif ratio < 0.66:
            r = int(colors[1][0] + (colors[2][0] - colors[1][0]) * ((ratio - 0.33) * 3))
            g = int(colors[1][1] + (colors[2][1] - colors[1][1]) * ((ratio - 0.33) * 3))
            b = int(colors[1][2] + (colors[2][2] - colors[1][2]) * ((ratio - 0.33) * 3))
        else:
            r = int(colors[2][0] + (colors[3][0] - colors[2][0]) * ((ratio - 0.66) * 3))
            g = int(colors[2][1] + (colors[3][1] - colors[2][1]) * ((ratio - 0.66) * 3))
            b = int(colors[2][2] + (colors[3][2] - colors[2][2]) * ((ratio - 0.66) * 3))
        draw.rectangle([(0, y), (VIDEO_WIDTH, y + 1)], fill=(r, g, b))

    # Add subtle geometric pattern for depth (circles)
    for i in range(0, VIDEO_WIDTH, 120):
        for j in range(0, VIDEO_HEIGHT, 120):
            draw.ellipse(
                [(i + 30, j + 30), (i + 90, j + 90)],
                outline=(255, 255, 255, 20),
                width=1
            )

    # Add radial glow effect from center
    glow = Image.new('RGBA', (VIDEO_WIDTH, VIDEO_HEIGHT), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)

    for radius in range(800, 0, -50):
        alpha = int(30 * (1 - radius / 800))
        glow_draw.ellipse(
            [(VIDEO_WIDTH//2 - radius, VIDEO_HEIGHT//3 - radius),
             (VIDEO_WIDTH//2 + radius, VIDEO_HEIGHT//3 + radius)],
            fill=(255, 255, 255, alpha)
        )

    # Composite glow over background
    img = img.convert('RGBA')
    img = Image.alpha_composite(img, glow)

    return img


def rounded_rect(draw, bbox, radius, fill=None):
    x1, y1, x2, y2 = bbox
    r = min(radius, (x2 - x1) // 2, (y2 - y1) // 2)
    draw.pieslice([x1, y1, x1 + r*2, y1 + r*2], 180, 270, fill=fill)
    draw.pieslice([x2 - r*2, y1, x2, y1 + r*2], 270, 360, fill=fill)
    draw.pieslice([x1, y2 - r*2, x1 + r*2, y2], 90, 180, fill=fill)
    draw.pieslice([x2 - r*2, y2 - r*2, x2, y2], 0, 90, fill=fill)
    draw.rectangle([x1 + r, y1, x2 - r, y2], fill=fill)
    draw.rectangle([x1, y1 + r, x2, y2 - r], fill=fill)


def generate_complete_image(phrase_data: dict, category_english: str, output_path: str, phrase_index: int = 0, total_phrases: int = 5):
    """Generate image with impressive background - Dutch-style centered containers"""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("PIL not available. Install: pip install Pillow")
        return None

    img = create_impressive_background(category_english)
    draw = ImageDraw.Draw(img)

    # Load fonts - Optimized for mobile viewing (INCREASED sizes)
    fonts_dir = Path(__file__).parent / "fonts"
    english_font_paths = [
        str(fonts_dir / "NotoSansDutch-Bold.ttf"),
        str(fonts_dir / "NotoSans-Bold.ttf"),
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/segoeuib.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]

    japanese_font_paths = [
        str(fonts_dir / "yugothb.ttc"),
        "C:/Windows/Fonts/yugothb.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "C:/Windows/Fonts/msgothic.ttc",
        "C:/Windows/Fonts/msmincho.ttc",
    ]

    def load_font(font_paths, size):
        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, size)
            except (IOError, OSError):
                continue
        return ImageFont.load_default()

    SIZE_CATEGORY = 64
    SIZE_NATIVE_L = 100
    SIZE_NATIVE_M = 82
    SIZE_NATIVE_S = 66
    SIZE_ENGLISH = 85
    SIZE_TRANSLITERATION = 55
    SIZE_BRANDING = 52
    SIZE_PROGRESS = 38

    font_category = load_font(english_font_paths, SIZE_CATEGORY)
    font_native_l = load_font(japanese_font_paths, SIZE_NATIVE_L)
    font_native_m = load_font(japanese_font_paths, SIZE_NATIVE_M)
    font_native_s = load_font(japanese_font_paths, SIZE_NATIVE_S)
    font_english = load_font(english_font_paths, SIZE_ENGLISH)
    font_romaji = load_font(english_font_paths, SIZE_TRANSLITERATION)
    font_branding = load_font(english_font_paths, SIZE_BRANDING)
    font_progress = load_font(english_font_paths, SIZE_PROGRESS)

    english = sanitize_text(phrase_data.get("english", ""))
    japanese = sanitize_text(phrase_data.get("japanese", ""))
    romaji = sanitize_text(phrase_data.get("romaji", ""), is_romaji=True)
    romaji_text = f"[{romaji}]" if romaji else ""

    def wrap_text(text, font, max_width):
        lines = []
        is_jp = any('\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff' or '\u4e00' <= c <= '\u9fff' for c in text)
        if is_jp:
            chunks = []
            buf = ''
            for ch in text:
                buf += ch
                if ch in '、。・ ':
                    chunks.append(buf)
                    buf = ''
            if buf:
                chunks.append(buf)
            if not chunks:
                chunks = [text]
            current_line = ''
            for chunk in chunks:
                test_line = current_line + chunk
                bbox = draw.textbbox((0, 0), test_line, font=font)
                w = bbox[2] - bbox[0]
                if w <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    # Check if chunk itself fits; if not, split char by char
                    bbox = draw.textbbox((0, 0), chunk, font=font)
                    if bbox[2] - bbox[0] <= max_width:
                        current_line = chunk
                    else:
                        # Split chunk char by char
                        current_line = ''
                        for ch in chunk:
                            test_line = current_line + ch
                            bbox = draw.textbbox((0, 0), test_line, font=font)
                            if bbox[2] - bbox[0] <= max_width:
                                current_line = test_line
                            else:
                                if current_line:
                                    lines.append(current_line)
                                current_line = ch
            if current_line:
                lines.append(current_line)

            # Kinsoku Shori: Never let closing punctuation start a new line alone
            cleaned_lines = []
            for l in lines:
                if l.strip() in '。、！？・!?~' and cleaned_lines:
                    cleaned_lines[-1] += l.strip()
                else:
                    cleaned_lines.append(l)
            lines = cleaned_lines
        else:
            words = text.split()
            current_line = []
            for word in words:
                test_line = ' '.join(current_line + [word])
                bbox = draw.textbbox((0, 0), test_line, font=font)
                width = bbox[2] - bbox[0]
                if width <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
            if current_line:
                lines.append(' '.join(current_line))
        return lines

    def pick_native_font(text, max_w):
        # Prefer single-line display if possible (L -> M -> S)
        for font, name in [(font_native_l, 'L'), (font_native_m, 'M'), (font_native_s, 'S')]:
            lines = wrap_text(text, font, max_w)
            if len(lines) == 1:
                return font, lines
        # Otherwise pick font that fits in at most 2 balanced lines
        for font, name in [(font_native_m, 'M'), (font_native_s, 'S')]:
            lines = wrap_text(text, font, max_w)
            if len(lines) <= 2:
                return font, lines
        return font_native_s, wrap_text(text, font_native_s, max_w)

    def measure_text_width(text, font):
        b = draw.textbbox((0, 0), text, font=font)
        return b[2] - b[0]

    def measure_line_h(font, is_jp=False):
        if is_jp:
            return int(font.size * 1.6)
        b = draw.textbbox((0, 0), "Ag", font=font)
        h = b[3] - b[1]
        return max(h, font.size + 10)

    max_text_w = VIDEO_WIDTH - 140
    en_lines = wrap_text(english, font_english, max_text_w)
    jp_font, jp_lines = pick_native_font(japanese, max_text_w - 20)
    romaji_lines = wrap_text(romaji_text, font_romaji, max_text_w - 60) if romaji_text else []

    en_lh = measure_line_h(font_english)
    jp_lh = measure_line_h(jp_font, is_jp=True)
    romaji_lh = measure_line_h(font_romaji)

    en_box_pad = 40
    jp_box_pad = 60
    romaji_box_pad = 35

    en_box_h = len(en_lines) * en_lh + en_box_pad * 2
    jp_box_h = len(jp_lines) * jp_lh + jp_box_pad * 2
    romaji_box_h = len(romaji_lines) * romaji_lh + romaji_box_pad * 2 if romaji_lines else 0

    gap_cat_en = 50
    gap_en_jp = 35
    gap_jp_romaji = 30
    gap_romaji_prog = 25
    gap_prog_brand = 40
    prog_bar_h = 30

    total_center_h = (0 + gap_cat_en + en_box_h + gap_en_jp +
                      jp_box_h + gap_jp_romaji + romaji_box_h + gap_romaji_prog +
                      prog_bar_h + gap_prog_brand)

    start_y = int((VIDEO_HEIGHT - total_center_h) * 0.38)
    if start_y < 200:
        start_y = 200

    cy = start_y

    # Category bar (rounded, fixed position)
    cat_text = category_english
    cat_bb = draw.textbbox((0, 0), cat_text, font=font_category)
    cat_tw = cat_bb[2] - cat_bb[0]
    cat_th = cat_bb[3] - cat_bb[1]
    cat_cx = VIDEO_WIDTH // 2
    cat_cy = 185
    cat_pad = 28
    cat_box_x1 = cat_cx - cat_tw // 2 - cat_pad
    cat_box_y1 = cat_cy - cat_th // 2 - cat_pad
    cat_box_x2 = cat_cx + cat_tw // 2 + cat_pad
    cat_box_y2 = cat_cy + cat_th // 2 + cat_pad
    rounded_rect(draw, (cat_box_x1, cat_box_y1, cat_box_x2, cat_box_y2),
                 25, fill=(0, 0, 0, 190))
    draw.text((cat_cx, cat_cy), cat_text,
              fill=(255, 255, 255), font=font_category, anchor="mm",
              stroke_width=3, stroke_fill=(0, 0, 0))

    cy += gap_cat_en

    # English phrase (top)
    en_margin = 50
    rounded_rect(draw, (en_margin, cy, VIDEO_WIDTH - en_margin, cy + en_box_h), 28,
                 fill=(20, 40, 100, 220))
    for i, line in enumerate(en_lines):
        ly = cy + en_box_pad + i * en_lh + en_lh // 2
        draw.text((VIDEO_WIDTH // 2, ly), line,
                  fill=(255, 255, 255), font=font_english, anchor="mm",
                  stroke_width=4, stroke_fill=(0, 0, 40))

    cy += en_box_h + gap_en_jp

    # Japanese phrase (below English)
    jp_margin = 40
    rounded_rect(draw, (jp_margin, cy, VIDEO_WIDTH - jp_margin, cy + jp_box_h), 24,
                 fill=(139, 0, 0, 220))
    for i, line in enumerate(jp_lines):
        ly = cy + jp_box_pad + i * jp_lh + jp_lh // 2
        draw.text((VIDEO_WIDTH // 2, ly), line,
                  fill=(255, 255, 200), font=jp_font, anchor="mm",
                  stroke_width=4, stroke_fill=(60, 0, 0))

    cy += jp_box_h + gap_jp_romaji

    # Romaji
    if romaji_lines:
        romaji_margin = 70
        rounded_rect(draw, (romaji_margin, cy, VIDEO_WIDTH - romaji_margin, cy + romaji_box_h), 18,
                     fill=(40, 40, 40, 220))
        for i, line in enumerate(romaji_lines):
            ly = cy + romaji_box_pad + i * romaji_lh + romaji_lh // 2
            draw.text((VIDEO_WIDTH // 2, ly), line,
                      fill=(255, 255, 255), font=font_romaji, anchor="mm",
                      stroke_width=3, stroke_fill=(20, 20, 20))
        cy += romaji_box_h + gap_romaji_prog
    else:
        cy += gap_romaji_prog

    # Progress
    prog_text = f"{phrase_index + 1} / {total_phrases}"
    prog_bb = draw.textbbox((0, 0), prog_text, font=font_progress)
    prog_h = prog_bb[3] - prog_bb[1]
    draw.text((VIDEO_WIDTH // 2, cy + prog_h // 2), prog_text,
              fill=(180, 180, 180), font=font_progress, anchor="mm")

    # Branding (rounded)
    brand_text = "VELOCITY JAPANESE"
    brand_bb = draw.textbbox((0, 0), brand_text, font=font_branding)
    brand_tw = brand_bb[2] - brand_bb[0]
    brand_th = brand_bb[3] - brand_bb[1]
    brand_cx = VIDEO_WIDTH // 2
    brand_cy = VIDEO_HEIGHT - 120
    brand_pad = 32
    brand_box_x1 = brand_cx - brand_tw // 2 - brand_pad
    brand_box_y1 = brand_cy - brand_th // 2 - brand_pad
    brand_box_x2 = brand_cx + brand_tw // 2 + brand_pad
    brand_box_y2 = brand_cy + brand_th // 2 + brand_pad
    rounded_rect(draw, (brand_box_x1, brand_box_y1, brand_box_x2, brand_box_y2),
                 30, fill=(0, 0, 0, 195))
    draw.text((brand_cx, brand_cy), brand_text,
              fill=(255, 215, 0), font=font_branding, anchor="mm",
              stroke_width=2, stroke_fill=(0, 0, 0))

    if img.mode == 'RGBA':
        img = img.convert('RGB')

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    print(f"  ✓ Image: {Path(output_path).name}")
    return output_path


# ============== VIDEO CREATION ==============

def _run_ffmpeg(cmd, max_retries: int = 3, timeout: int = 600):
    """Run an ffmpeg command with retries. Returns True on success."""
    import time
    for attempt in range(1, max_retries + 1):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            rc = result.returncode
            out = Path(cmd[-1])
            if rc == 0 and out.exists() and out.stat().st_size > 0:
                return True
            stderr_tail = (result.stderr or "")[-600:].replace("\n", " ")
            print(f"[video] ffmpeg attempt {attempt}/{max_retries} failed (rc={rc}): {stderr_tail}")
        except subprocess.TimeoutExpired as e:
            print(f"[video] ffmpeg attempt {attempt}/{max_retries} timed out: {e}")
        except Exception as e:
            print(f"[video] ffmpeg attempt {attempt}/{max_retries} exception: {e}")
        try:
            partial = Path(cmd[-1])
            if partial.exists():
                partial.unlink()
        except Exception:
            pass
        if attempt < max_retries:
            time.sleep(3)
    return False


def create_video_from_images_audio(image_files: list, audio_files: list, combined_audio: str, output_file: str):
    """Create video from images and audio with PERFECT synchronization"""

    print(f"\n[video] Creating video from {len(image_files)} images...")
    print(f"[video] Ensuring complete audio playback and sync...")

    temp_clips = []

    for i, (img_path, audio_info) in enumerate(zip(image_files, audio_files)):
        duration = audio_info['duration']
        print(f"  Image {i+1}/{len(image_files)}: {duration:.2f}s (EN: {audio_info.get('en_duration', 0):.1f}s + JP: {audio_info.get('jp_duration', 0):.1f}s)")

        temp_clip = Path(output_file).parent / f"temp_clip_{i:02d}.mp4"
        temp_clips.append(temp_clip)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps={FPS}",
            "-t", str(duration),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            str(temp_clip)
        ]

        if not _run_ffmpeg(cmd):
            raise RuntimeError(f"Failed to create clip {i+1} after retries")

    # Concatenate clips
    print("[video] Concatenating clips...")
    temp_video = Path(output_file).parent / "temp_video.mp4"
    concat_file = Path(output_file).parent / "concat_list.txt"

    with open(concat_file, "w") as f:
        for clip in temp_clips:
            f.write(f"file '{clip.resolve().as_posix()}'\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(temp_video)]
    if not _run_ffmpeg(cmd):
        raise RuntimeError("Failed to concatenate clips after retries")

    # Add audio
    print("[video] Adding audio (ensuring complete playback)...")
    audio_duration = get_audio_duration(combined_audio)
    print(f"[video] Audio duration: {audio_duration:.2f}s")

    if not Path(combined_audio).exists() or Path(combined_audio).stat().st_size == 0:
        raise RuntimeError(f"Narration audio missing or empty: {combined_audio}")

    cmd = [
        "ffmpeg", "-y",
        "-i", str(temp_video),
        "-i", str(combined_audio),
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        str(output_file)
    ]
    mux_ok = _run_ffmpeg(cmd)
    if not mux_ok:
        print("[video] Mux with -c:v copy failed, retrying with re-encode...")
        cmd = [
            "ffmpeg", "-y",
            "-i", str(temp_video),
            "-i", str(combined_audio),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast",
            "-c:a", "aac",
            "-shortest",
            str(output_file)
        ]
        if not _run_ffmpeg(cmd):
            raise RuntimeError("Failed to mux video+audio after retries")

    # Verify
    video_duration = get_audio_duration(str(output_file).replace(".mp4", ".mp4"))
    print(f"[video] ✓ Video created: {Path(output_file).name} ({video_duration:.2f}s)")

    # Cleanup
    for clip in temp_clips:
        if clip.exists():
            clip.unlink()
    if temp_video.exists():
        temp_video.unlink()
    if concat_file.exists():
        concat_file.unlink()


# ============== MAIN WORKFLOW ==============

def generate_reel(category_english: str = None):
    """Generate complete Facebook Reel"""

    if not category_english:
        # Use smart category rotation to prevent repeats
        category_english = get_available_category()

    print(f"\n{'='*80}")
    print(f"Category: {category_english} ({CATEGORIES_JAPANESE[category_english]})")
    print(f"{'='*80}\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    reel_dir = VIDEO_DIR / f"{category_english}_{timestamp}"
    reel_dir.mkdir(exist_ok=True)

    # Step 1: Generate unique phrases
    print("[1/4] Generating unique phrases (checking history)...")
    phrases = generate_phrases(category_english, num_phrases=5)

    for i, phrase in enumerate(phrases, 1):
        print(f"  {i}. {phrase['english']} → {phrase['japanese']}")

    # Step 2: Generate images
    print("\n[2/4] Generating images with impressive backgrounds...")
    for i, phrase in enumerate(phrases):
        output_path = reel_dir / f"phrase_{i:02d}.jpg"
        generate_complete_image(phrase, category_english, str(output_path), phrase_index=i, total_phrases=len(phrases))
        print(f"  ✓ Image {i+1}: {phrase['english'][:40]}...")

    # Step 3: Generate audio
    print("\n[3/4] Generating audio (English + Japanese with 500ms pause)...")
    audio_files = generate_all_audio(phrases, str(reel_dir))

    final_audio = reel_dir / "narration.mp3"
    create_final_narration(audio_files, str(final_audio))

    # Step 4: Create video - CRITICAL: Sort images for correct order
    print("\n[4/4] Creating video...")
    output_video = reel_dir / "final_reel.mp4"

    image_files = sorted([str(p) for p in reel_dir.glob("phrase_*.jpg")])

    create_video_from_images_audio(
        image_files,
        audio_files,
        str(final_audio),
        str(output_video)
    )

    # Save metadata
    metadata = {
        "category_english": category_english,
        "category_japanese": CATEGORIES_JAPANESE[category_english],
        "timestamp": timestamp,
        "phrases": phrases,
        "video": str(output_video),
        "audio": str(final_audio)
    }

    with open(reel_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*80}")
    print(f"✅ REEL COMPLETE!")
    print(f"  📁 {reel_dir}")
    print(f"  🎬 {output_video.name}")
    print(f"  🏷️  Branding: Velocity Japanese")
    print(f"{'='*80}\n")

    return metadata


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🇯🇵 VELOCITY JAPANESE - FACEBOOK REELS AUTOMATION 🇯🇵")
    print("="*80)
    print("\n✨ IMPROVED FEATURES:")
    print("  ✓ Natural pauses with commas (non-robotic TTS)")
    print("  ✓ Perfect audio-video synchronization")
    print("  ✓ Complete audio playback guaranteed")
    print("  ✓ English category names (for American/European learners)")
    print("  ✓ Velocity Japanese branding at bottom")
    print("  ✓ NEVER repeats phrases (permanent history tracking)")
    print(f"\n📊 AVAILABLE CATEGORIES ({len(CATEGORIES_ENGLISH)} total):")
    for i, cat in enumerate(CATEGORIES_ENGLISH, 1):
        print(f"   {i:2d}. {cat} ({CATEGORIES_JAPANESE[cat]})")
    print(f"\n📅 DAILY CAPACITY:")
    print(f"  • 4 reels per day = 20 unique phrases daily")
    print(f"  • {len(CATEGORIES_ENGLISH)} categories = Over 6 days before any category repeats")
    print(f"  • Phrase history is PERMANENT (never deletes)")
    print(f"  • AI generates FRESH phrases every time")
    print("="*80)

    generate_reel()

    print("\n" + "="*80)
    print("✅ READY FOR DAILY AUTOMATION!")
    print("="*80)
    print("\nTo generate 4 reels for today:")
    print("  from facebook_reels_automation import generate_daily_content")
    print("  generate_daily_content(times_per_day=4)")
    print("\nTo generate a single reel:")
    print("  generate_reel('Love')  # Or any category from the list above")
    print("="*80)
