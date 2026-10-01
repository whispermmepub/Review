#!/usr/bin/env python3
"""One-time migration for existing Review posts.

Keeps the existing post design/content, switches fonts to Walone, and
permanently removes the source link and social share buttons requested by
the site owner.
"""
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

# Force a smaller, consistent mobile reading size for both normal mobile browsers and Telegram in-app browsers.
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
for path in sorted(ROOT.glob("[0-9]*/index.html"), key=lambda p: int(p.parent.name)):
    s = path.read_text(encoding="utf-8")
    if "Mobile browser + Telegram in-app browser typography" not in s:
        s = s.replace("</style>", MOBILE_POST_CSS + "    </style>", 1)
        path.write_text(s, encoding="utf-8")


# Add lightweight browser Read Aloud player below each post cover image.
READ_ALOUD_CSS = '''
        /* Browser Read Aloud player */
        .read-aloud-player {
            width: calc(100% - 24px);
            max-width: 760px;
            margin: 0 auto 24px;
            padding: 14px;
            border: 1px solid rgba(74,158,255,0.35);
            border-radius: 16px;
            background: rgba(30,26,53,0.92);
            box-shadow: 0 10px 28px rgba(0,0,0,0.22);
            font-family: "Walone", sans-serif;
        }
        .read-aloud-title {
            font-size: 0.95rem;
            font-weight: 700;
            color: #fff;
            margin-bottom: 10px;
        }
        .read-aloud-controls {
            display: flex;
            gap: 8px;
            align-items: center;
            flex-wrap: wrap;
        }
        .read-aloud-player select,
        .read-aloud-player button {
            min-height: 38px;
            border: 1px solid rgba(255,255,255,0.16);
            border-radius: 10px;
            background: #24203f;
            color: #fff;
            padding: 7px 11px;
            font-family: "Walone", sans-serif;
            font-size: 0.84rem;
        }
        .read-aloud-player select { flex: 1 1 150px; }
        .read-aloud-player button { cursor: pointer; }
        .read-aloud-player .read-play {
            background: #4a9eff;
            border-color: #4a9eff;
            font-weight: 700;
        }
        .read-aloud-status {
            margin-top: 8px;
            color: #9fa4bd;
            font-size: 0.75rem;
            line-height: 1.5;
        }
        @media (max-width: 600px) {
            .read-aloud-player {
                width: calc(100% - 20px);
                margin-bottom: 18px;
                padding: 11px;
            }
            .read-aloud-controls { gap: 6px; }
            .read-aloud-player select,
            .read-aloud-player button {
                font-size: 0.78rem;
                min-height: 36px;
            }
        }
'''
READ_ALOUD_HTML = '''
        <section class="read-aloud-player" aria-label="အသံဖြင့်ဖတ်ရန်">
            <div class="read-aloud-title">🔊 အသံဖြင့်ဖတ်ရန်</div>
            <div class="read-aloud-controls">
                <select class="read-voice" aria-label="အသံရွေးရန်"></select>
                <select class="read-rate" aria-label="ဖတ်နှုန်း">
                    <option value="0.8">0.8×</option>
                    <option value="1" selected>1.0×</option>
                    <option value="1.2">1.2×</option>
                    <option value="1.5">1.5×</option>
                </select>
                <button type="button" class="read-play">▶ ဖတ်ရန်</button>
                <button type="button" class="read-pause">⏸ ခဏရပ်</button>
                <button type="button" class="read-stop">⏹ ရပ်ရန်</button>
            </div>
            <div class="read-aloud-status">Microsoft Edge / browser တွင် ရရှိနိုင်သော မြန်မာအသံကို အသုံးပြုပါမည်။</div>
        </section>
'''
READ_ALOUD_JS = r'''
    <script>
    (function () {
        var players = document.querySelectorAll('.read-aloud-player');
        if (!players.length || !('speechSynthesis' in window)) return;

        players.forEach(function (player) {
            var voiceSelect = player.querySelector('.read-voice');
            var rateSelect = player.querySelector('.read-rate');
            var playBtn = player.querySelector('.read-play');
            var pauseBtn = player.querySelector('.read-pause');
            var stopBtn = player.querySelector('.read-stop');
            var status = player.querySelector('.read-aloud-status');
            var textEl = document.querySelector('.post-body');
            var voices = [];

            function loadVoices() {
                voices = window.speechSynthesis.getVoices().filter(function (v) {
                    return /^my(?:-|_)/i.test(v.lang) || /burmese|myanmar|nilar|thiha/i.test(v.name);
                });
                voiceSelect.innerHTML = '';
                if (!voices.length) {
                    var none = document.createElement('option');
                    none.textContent = 'မြန်မာအသံ မတွေ့သေးပါ';
                    none.value = '';
                    voiceSelect.appendChild(none);
                    status.textContent = 'ဒီ browser/device မှာ Burmese voice မရသေးပါ။ Edge Read Aloud တွင် Burmese voice ရှိပါက အဲဒီ voice ကို အသုံးပြုနိုင်ပါသည်။';
                    return;
                }
                voices.forEach(function (voice, i) {
                    var opt = document.createElement('option');
                    opt.value = String(i);
                    opt.textContent = voice.name + ' (' + voice.lang + ')';
                    voiceSelect.appendChild(opt);
                });
                var preferred = voices.findIndex(function (v) { return /nilar/i.test(v.name); });
                if (preferred < 0) preferred = voices.findIndex(function (v) { return /thiha/i.test(v.name); });
                voiceSelect.value = String(preferred >= 0 ? preferred : 0);
                status.textContent = 'ရရှိနိုင်သော မြန်မာအသံ: ' + voices.length + ' ခု';
            }

            playBtn.addEventListener('click', function () {
                if (!voices.length || !textEl) return;
                window.speechSynthesis.cancel();
                var utterance = new SpeechSynthesisUtterance(textEl.innerText.trim());
                utterance.lang = 'my-MM';
                utterance.rate = parseFloat(rateSelect.value) || 1;
                var selected = voices[parseInt(voiceSelect.value, 10)];
                if (selected) utterance.voice = selected;
                utterance.onend = function () { status.textContent = 'ဖတ်ပြီးပါပြီ။'; };
                utterance.onerror = function () { status.textContent = 'အသံဖတ်ရာတွင် ပြဿနာရှိပါသည်။'; };
                window.speechSynthesis.speak(utterance);
                status.textContent = 'ဖတ်နေပါသည်…';
            });
            pauseBtn.addEventListener('click', function () {
                if (window.speechSynthesis.speaking) window.speechSynthesis.pause();
            });
            stopBtn.addEventListener('click', function () {
                window.speechSynthesis.cancel();
                status.textContent = 'ရပ်ထားပါပြီ။';
            });
            loadVoices();
            if (window.speechSynthesis.onvoiceschanged !== undefined) {
                window.speechSynthesis.onvoiceschanged = loadVoices;
            }
        });
    })();
    </script>
'''
for path in sorted(ROOT.glob("[0-9]*/index.html"), key=lambda p: int(p.parent.name)):
    s = path.read_text(encoding="utf-8")
    if 'class="read-aloud-player"' not in s:
        s = s.replace("</style>", READ_ALOUD_CSS + "    </style>", 1)
        s = re.sub(
            r'(<img\b[^>]*class="post-image"[^>]*>\s*)',
            r'\1' + READ_ALOUD_HTML + '\n',
            s,
            count=1,
            flags=re.I | re.S,
        )
        s = s.replace("</body>", READ_ALOUD_JS + "\n</body>", 1)
        path.write_text(s, encoding="utf-8")
        print("Added Read Aloud player:", path)

print("Migration complete.")
