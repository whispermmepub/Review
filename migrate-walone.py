#!/usr/bin/env python3
"""One-time migration: make every existing numbered Review post use Walone."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
FONT_R = "https://raw.githubusercontent.com/whispermmepub/myanmar-yoe-shin-fonts/main/fonts/Walone-Regular.ttf"
FONT_B = "https://raw.githubusercontent.com/whispermmepub/myanmar-yoe-shin-fonts/main/fonts/Walone-Bold.ttf"

FONT_BLOCK = f'''@font-face {{ font-family: "Walone"; src: url("{FONT_R}") format("truetype"); font-weight: 400; font-style: normal; font-display: swap; }}
        @font-face {{ font-family: "Walone"; src: url("{FONT_B}") format("truetype"); font-weight: 700; font-style: normal; font-display: swap; }}'''

for path in sorted(ROOT.glob("[0-9]*/index.html"), key=lambda p: int(p.parent.name)):
    s = path.read_text(encoding="utf-8")
    old = s

    s = re.sub(r'\s*@import\s+url\(["\']https://fonts\.googleapis\.com/css2\?family=Noto\+Sans\+Myanmar[^"\']*["\']\);?', '', s, flags=re.I)
    s = re.sub(r'\s*@font-face\s*\{[^{}]*font-family\s*:\s*[\'"]?(?:Burma001|Walone|PyidaungsuMM|MyanmarAyar)[\'"]?[^{}]*\}', '', s, flags=re.I)

    if '<style>' in s:
        s = s.replace('<style>', '<style>\n        ' + FONT_BLOCK, 1)

    s = re.sub(r'font-family\s*:\s*[\'"](?:Burma001|Noto Sans Myanmar|PyidaungsuMM|MyanmarAyar|Walone)[\'"]\s*,?\s*sans-serif',
               'font-family: "Walone", sans-serif', s, flags=re.I)
    s = re.sub(r'font-family\s*:\s*[\'"](?:Burma001|Noto Sans Myanmar|PyidaungsuMM|MyanmarAyar)[\'"]',
               'font-family: "Walone"', s, flags=re.I)

    # Permanently remove the old source link and social share controls.\n    s = re.sub(r'\\s*<p><a href="[^"]*"[^>]*>မူရင်းကို ဖတ်ရန် →</a></p>', '', s, flags=re.I)\n    s = re.sub(r'\\s*<div class="share-section">.*?</div>\\s*', '\\n\\n', s, flags=re.I | re.S)\n    s = re.sub(r'\\s*/\\* Share Buttons \\*/.*?(?=\\n\\s*</style>)', '', s, flags=re.I | re.S)\n    s = re.sub(r'\\n\\s*// Share URLs.*?\\n\\s*\\}\\)\\(\\);', '', s, flags=re.I | re.S)\n
    if s != old:
        path.write_text(s, encoding="utf-8")
        print("Walone:", path)

print("Migration complete.")
