#!/usr/bin/env python3
"""Keep Review pages consistent and remove the retired audio player."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
FONT_R = "https://raw.githubusercontent.com/whispermmepub/myanmar-yoe-shin-fonts/main/fonts/Walone-Regular.ttf"
FONT_B = "https://raw.githubusercontent.com/whispermmepub/myanmar-yoe-shin-fonts/main/fonts/Walone-Bold.ttf"

FONT_BLOCK = f'''@font-face {{ font-family: "Walone"; src: url("{FONT_R}") format("truetype"); font-weight: 400; font-style: normal; font-display: swap; }}
        @font-face {{ font-family: "Walone"; src: url("{FONT_B}") format("truetype"); font-weight: 700; font-style: normal; font-display: swap; }}'''

def post_pages():
    """Return post pages, excluding the root site and wow-reader pages."""
    return sorted(
        (p for p in ROOT.rglob("index.html")
         if p.parent != ROOT and "wow-reader" not in p.parts),
        key=lambda p: str(p.relative_to(ROOT)),
    )

for path in post_pages():
    s = path.read_text(encoding="utf-8")
    old = s

    # Remove old font imports/definitions.
    s = re.sub(
        r'\s*@import\s+url\(["\']https://fonts\.googleapis\.com/css2\?family=Noto\+Sans\+Myanmar[^"\']*["\']\);?',
        '',
        s,
        flags=re.I,
    )
    s = re.sub(
        r'\s*@font-face\s*\{[^{}]*font-family\s*:\s*["\']?(?:Burma001|Walone|PyidaungsuMM|MyanmarAyar)["\']?[^{}]*\}',
        '',
        s,
        flags=re.I,
    )

    if '<style>' in s:
        s = s.replace('<style>', '<style>\n        ' + FONT_BLOCK, 1)

    s = re.sub(
        r'font-family\s*:\s*["\'](?:Burma001|Noto Sans Myanmar|PyidaungsuMM|MyanmarAyar|Walone)["\']\s*,?\s*sans-serif',
        'font-family: "Walone", sans-serif',
        s,
        flags=re.I,
    )
    s = re.sub(
        r'font-family\s*:\s*["\'](?:Burma001|Noto Sans Myanmar|PyidaungsuMM|MyanmarAyar)["\']',
        'font-family: "Walone"',
        s,
        flags=re.I,
    )

    # Permanently remove the old source link.
    s = re.sub(
        r'\s*<p>\s*<a href="[^"]*"[^>]*>\s*မူရင်းကို\s*ဖတ်ရန်\s*→\s*</a>\s*</p>',
        '',
        s,
        flags=re.I | re.S,
    )

    # Permanently remove Telegram/Facebook/Viber share buttons and their CSS.
    s = re.sub(
        r'\s*<div class="share-section">.*?</div>\s*',
        '\n\n',
        s,
        flags=re.I | re.S,
    )
    s = re.sub(
        r'\s*/\* Share Buttons \*/.*?(?=\n\s*</style>)',
        '',
        s,
        flags=re.I | re.S,
    )
    s = re.sub(
        r'\n\s*// Share URLs.*?\n\s*\}\)\(\);',
        '',
        s,
        flags=re.I | re.S,
    )

    if s != old:
        path.write_text(s, encoding="utf-8")
        print("Migrated:", path)

# Force a smaller, consistent mobile reading size for normal and Telegram in-app browsers.
MOBILE_POST_CSS = '''
        /* Mobile browser + Telegram in-app browser typography */
        @media (max-width: 600px) {
            body { font-size: 14px; }
            header { margin: 12px 10px 10px; padding: 26px 14px 22px; }
            header h1 { font-size: 1.25rem !important; line-height: 1.35; }
            .post-meta { font-size: 0.80rem !important; }
            .post-body { padding: 22px 10px; }
            .post-body p { font-size: 1.00rem !important; line-height: 1.78 !important; }
            .back-link { font-size: 0.85rem; padding: 8px 14px; }
            .reviewer-credit { font-size: 0.78rem; }
        }
'''
for path in post_pages():
    s = path.read_text(encoding="utf-8")
    if "Mobile browser + Telegram in-app browser typography" not in s:
        s = s.replace("</style>", MOBILE_POST_CSS + "    </style>", 1)
        path.write_text(s, encoding="utf-8")


def remove_retired_audio(s: str) -> str:
    """Strip only the legacy audio player and its dedicated styles/scripts."""
    # Remove the original player styles; the comment section starts immediately after them.
    s = re.sub(
        r'^[ \t]*\.read-aloud-player\s*\{.*?(?=^[ \t]*\.comments-panel\s*\{)',
        '',
        s,
        count=1,
        flags=re.I | re.S | re.M,
    )
    # Remove the later, standalone audio-only CSS block.
    s = re.sub(
        r'^[ \t]*/\* Browser Read Aloud player \*/.*?(?=^[ \t]*</style>)',
        '',
        s,
        count=1,
        flags=re.I | re.S | re.M,
    )
    # Remove the audio controls, if present.
    s = re.sub(
        r'\s*<section\b(?=[^>]*\bclass=["\'][^"\']*\bread-aloud-player\b[^"\']*["\'])[^>]*>.*?</section>\s*',
        '\n',
        s,
        flags=re.I | re.S,
    )
    s = re.sub(
        r'\s*<audio\b(?=[^>]*\bclass=["\'][^"\']*\bread-audio\b[^"\']*["\'])[^>]*>.*?</audio>\s*',
        '\n',
        s,
        flags=re.I | re.S,
    )

    def drop_audio_script(match: re.Match) -> str:
        opening, body, closing = match.groups()
        if re.search(r'audio-player\.js', opening, re.I) or re.search(
            r'read-aloud-player|data-audio-base|read-audio|read-voice|read-rate|read-play|read-pause|read-stop',
            body,
            re.I,
        ):
            return '\n'
        return match.group(0)

    s = re.sub(r'(<script\b[^>]*>)([\s\S]*?)(</script\s*>)', drop_audio_script, s, flags=re.I)
    s = re.sub(r'\s+data-audio-base=["\'][^"\']*["\']', '', s, flags=re.I)
    # Avoid leaving whitespace-only lines where the removed player used to be.
    s = re.sub(r'(?m)^[ \t]+(?=\r?\n[ \t]*</style>)', '', s)
    s = re.sub(
        r'(?is)(<script\b[^>]*firebase-comments\.js[^>]*></script>)[ \t\r\n]*(<script\b[^>]*reading-stats\.js[^>]*></script>)',
        r'\1\n        \2',
        s,
    )
    s = re.sub(
        r'(?is)(</script>)[ \t\r\n]+(?=</body>)',
        r'\1\n\n',
        s,
    )
    s = re.sub(
        r'(?m)^[ \t]+(?=(?:\r?\n[ \t]*)+</body>\s*</html>\s*\Z)',
        '',
        s,
        flags=re.I,
    )
    return s


cleaned_pages = 0
for path in post_pages():
    s = path.read_text(encoding="utf-8")
    cleaned = remove_retired_audio(s)
    if cleaned != s:
        path.write_text(cleaned, encoding="utf-8")
        cleaned_pages += 1
        print("Removed retired audio UI:", path)

print(f"Migration complete. Audio UI cleaned from {cleaned_pages} post page(s).")
