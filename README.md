# Velocity Japanese - Storybook Bot

Live Japanese short-form channel. Every run builds one storybook reel and
publishes it through the uploaders in `upload/`.

## What changed in the storybook version

- 3 phrases per reel, under 60 seconds (hard cap 59.4 s)
- 12 storybook worlds: garden, forest, beach, desert, snow, jungle, savanna,
  autumn, cherry, lavender, bamboo, market
- 13 curated colour palettes plus generated palettes
- rotating four-animal cast; no fox
- Japanese word/phrase tiles (never one character per box)
- Japanese TTS: `ja-JP-NanamiNeural`; English: `en-US-AvaNeural`
- Instagram-style storybook page, Velo mascot, local Noto Japanese fonts
- Facebook pinned comment includes `https://velocityjapanese.com`

## Schedule

The GitHub Actions workflow runs **3 times a day**:

- 07:00 Japan time
- 12:00 Japan time
- 19:00 Japan time

Cron: `0 22 * * *`, `0 3 * * *`, `0 10 * * *` (UTC).

Every run deals the next palette, world and cast from shuffled decks. State is
committed back to `output/history/` so the next run does not repeat the same
world, palette or cast.

## Run locally

```bash
pip install -r requirements.txt
python -m playwright install chromium

python build.py --recipe storybook-3           # auto theme, world and cast
python build.py --recipe storybook-3 --category Greetings --world cherry --theme duo
python validate.py
python upload_all_platforms.py --dry-run
```

Useful flags:

```bash
python build.py --list-categories
python build.py --list-palettes
python build.py --list-worlds
python build.py --recipe storybook-3 --new-theme
python build.py --recipe storybook-3 --cast panda,frog,penguin,cat
```

## Rotation state

- `output/history/storybook_theme_deck.json` - palette deck
- `output/history/storybook_set_deck.json` - world deck
- `output/history/storybook_cast.json` - recent cast signatures
- `output/history/all_generated_phrases.json` - permanent phrase history
- `output/history/recent_categories.json` - category rotation

The workflow commits all of these after every run. Do not delete them unless you
want the next post to repeat a recent theme or phrase.

## Manual publish

Use **Actions → Velocity Japanese - Storybook 3x Upload → Run workflow**. The
optional inputs let you pin a category, palette, world, cast or phrase count for
a one-off test; leave them empty for production rotation.

## Publish targets

`upload_all_platforms.py` attempts Facebook, Instagram, YouTube, VK, Telegram,
X/Twitter, Threads and TikTok. Platforms whose credentials are not configured
are skipped safely.

Facebook is the primary target. The uploader posts the lesson caption as a
pinned comment and appends:

```
🌐 Learn more at our website: https://velocityjapanese.com
Visit velocityjapanese.com for daily Japanese lessons!
```

## Validation

`validate.py` checks:

- duration is under 60 seconds and within the 59.4 s project cap
- 3-5 phrases are present
- recipe, theme, style and world metadata are consistent
- the encoded video length and loudness / true peak are in range

A failed validation blocks publishing.
