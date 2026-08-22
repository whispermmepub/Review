#!/usr/bin/env python3
"""One-time/idempotent patch for the generated post header glass style."""

from pathlib import Path
import re

path = Path(__file__).with_name("sync-posts.py")
text = path.read_text(encoding="utf-8")

marker = "/* iOS Glass Header */"
if marker in text:
    print("Glass header patch already applied")
    raise SystemExit(0)

pattern = re.compile(
    r"        \.container \{\{.*?        \.post-image \{\{",
    re.DOTALL,
)

replacement = r'''        .container {{
            width: 100%;
            background:
                radial-gradient(circle at 100% 5%, rgba(251, 146, 60, 0.09), transparent 24%),
                radial-gradient(circle at 0% 8%, rgba(236, 72, 153, 0.07), transparent 22%),
                #17142d;
            overflow: hidden;
        }}

        /* iOS Glass Header */
        header {{
            position: relative;
            isolation: isolate;
            overflow: hidden;
            margin: 18px 14px 14px;
            padding: 36px 20px 30px;
            text-align: center;
            color: #ffffff;
            border-radius: 26px;
            background:
                linear-gradient(135deg, rgba(255,255,255,0.13), rgba(255,255,255,0.045)),
                rgba(24, 21, 52, 0.72);
            border: 1px solid rgba(255,255,255,0.25);
            -webkit-backdrop-filter: blur(26px) saturate(150%);
            backdrop-filter: blur(26px) saturate(150%);
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,0.20),
                inset 0 -1px 0 rgba(255,255,255,0.05),
                0 18px 45px rgba(0,0,0,0.28),
                0 0 34px rgba(124, 58, 237, 0.10);
        }}

        header::before {{
            content: '';
            position: absolute;
            inset: -38%;
            z-index: -2;
            pointer-events: none;
            background:
                radial-gradient(circle at 19% 24%, rgba(236,72,153,0.18), transparent 31%),
                radial-gradient(circle at 84% 76%, rgba(251,146,60,0.38), transparent 29%),
                radial-gradient(circle at 52% 43%, rgba(99,102,241,0.30), transparent 39%);
            filter: blur(34px);
            transform: scale(1.08);
        }}

        header::after {{
            content: '';
            position: absolute;
            inset: 0;
            z-index: -1;
            pointer-events: none;
            border-radius: inherit;
            background:
                linear-gradient(180deg, rgba(255,255,255,0.09), transparent 34%),
                radial-gradient(circle at 92% 92%, rgba(255,183,94,0.14), transparent 28%);
        }}

        header h1 {{
            position: relative;
            z-index: 1;
            font-size: 1.5rem;
            margin-bottom: 14px;
            font-weight: 900;
            letter-spacing: 0.02em;
            line-height: 1.35;
            color: #ffffff;
            opacity: 1;
            -webkit-font-smoothing: antialiased;
            text-rendering: optimizeLegibility;
            text-shadow:
                0 1px 1px rgba(0,0,0,0.78),
                0 3px 10px rgba(0,0,0,0.42),
                0 0 1px rgba(255,255,255,0.50);
        }}

        .post-meta {{
            position: relative;
            z-index: 1;
            font-size: 0.92rem;
            line-height: 1.55;
            color: rgba(255,255,255,0.96);
            opacity: 1;
            font-weight: 600;
            letter-spacing: 0.01em;
            -webkit-font-smoothing: antialiased;
            text-shadow: 0 1px 5px rgba(0,0,0,0.55);
        }}

        @supports not ((-webkit-backdrop-filter: blur(1px)) or (backdrop-filter: blur(1px))) {{
            header {{
                background:
                    linear-gradient(135deg, rgba(52,47,82,0.98), rgba(25,22,51,0.98));
            }}
        }}

        .post-image {{'''

new_text, count = pattern.subn(replacement, text, count=1)
if count != 1:
    raise SystemExit("Could not find the post header CSS block; no changes made")

# Keep the mobile title readable and closer to the approved mockup.
new_text = new_text.replace(
    "            header h1 {{ font-size: 1.2rem; }}",
    "            header {{ margin: 14px 10px 12px; padding: 32px 16px 26px; border-radius: 23px; }}\n            header h1 {{ font-size: 1.32rem; margin-bottom: 12px; }}\n            .post-meta {{ font-size: 0.88rem; }}",
    1,
)

# Match browser/PWA chrome with the new header family.
new_text = new_text.replace(
    '<meta name="theme-color" content="#141228">',
    '<meta name="theme-color" content="#17142d">',
    1,
)

path.write_text(new_text, encoding="utf-8")
print("Applied iOS glass header patch to sync-posts.py")
