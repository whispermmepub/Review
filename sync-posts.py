#!/usr/bin/env python3
"""
Sync Blogspot book review posts to the Review GitHub site.
Fetches RSS feed, identifies book review posts, generates posts.json and HTML files.
Directory names use English romanized slugs for clean URLs.

This script is designed to be run by GitHub Actions workflow on a schedule
or on push events to keep the Review site in sync with the Blogspot blog.
"""

import xml.etree.ElementTree as ET
import json
import re
import os
import hashlib
from datetime import datetime
from urllib.parse import quote

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = SCRIPT_DIR
# Multiple blog sources - add more feeds here
FEEDS = [
    {
        'feed_url': 'https://whisper1of.blogspot.com/feeds/posts/default?alt=rss&max-results=100',
        'blog_url': 'https://whisper1of.blogspot.com',
        'name': 'Whisper Of Words',
    },
    {
        'feed_url': 'https://youthsbookreflections.blogspot.com/feeds/posts/default?alt=rss&max-results=100',
        'blog_url': 'https://youthsbookreflections.blogspot.com',
        'name': 'Youths Book Reflections',
    },
]

# Known non-review posts to exclude (catalogs, lists)
EXCLUDE_TITLES = [
    'WoW',
    'Whisper Of Words epub',
    'Epub Kfx အဖြစ် ရှိပြီး စာအုပ်များ',
]

# Manual mapping of blog posts to clean English slugs based on known book titles
SLUG_MAP = {
    'ဆန့်ကျင်ဘက်၏ သမီးပျို': 'daughter-of-the-opposite',
    'ပါစီဂျက်ဆန်နှင့် အိုလံပစ်နတ်ဘုရားများ - ကျိန်စာသင့်ဓား - ကောင်းမြတ်လွန်းသော်': 'percy-jackson-curse-killer',
    'ကမ်းခြေပေါ်မှာ ကက်ဖကာ - မိုးသက်ဟန်': 'kafka-on-the-shore',
    'အလ်ဘတ်ကမူး၏အရေးအသားများ - မြင့်သန်း': 'selected-works-albert-camus',
    'တောမင်းသမီး - ခင်ခင်ထူး': 'forest-princess-king-kin',
    'ဒဗ္ဗလင်မြို့ကလူများ - မြင့်သန်း': 'dubliners-joyce',
    'မာနနဲ့ အာဃာတ - တင့်တယ်': 'pride-and-prejudice-tint-te',
    'ပါစီဂျက်ဆန်နှင့် အိုလံပစ်နတ်ဘုရားများ - မှော်ဝင်္ကပါတိုက်ပွဲ - ကောင်းမြတ်လွန်းသော်': 'percy-jackson-magic-battle',
    'အငို အရယ် နည်းသော ရက်များ - သန်းတင့် - book review': 'days-with-few-tears-laughs',
    'တသိမ့်သိမ့်ဒွန် - တက္ကသိုလ် နန္ဒမိတ် ၊ မြတ်ငြိမ်း၊  တင်မောင်မြင့်': 'and-quiet-flows-the-don',
    'ဟင်္သာငှက်တို့ အမြင့်ပျံကြရာ အရပ်ဝယ် - သန်းတင့်': 'swans-soaring-high',
    'ထက်ဝက်စား_သန်းတင့်': 'eat-half-myan',
    'အနော်မာရှင်းတမ်း - သန်းတင့်': 'annomars-timeline',
    'ကြက်တွန်သံလေးတွေ - သန်းတင့်': 'little-rooster-crows',
    'မင်းရယ် သူရယ် မိုးပြေးလေးတွေရယ် - သန်းတင့်': 'you-me-and-rain',
    'လူလိမ် - သန်းတင့်': 'the-liar-myan',
    'အငိုအရယ်နည်းသော ရက်များ/ သန်းတင့်': 'few-tears-laughs-thant',
    'The Reader - စာဖတ်သူ - သူရိန်ဝင်း(မြန်မာပြန်)': 'the-reader-myanmar',
    'ကွယ်လွန်သူတို့ ဝိညာဉ် - သတိုးတေဇ': 'souls-of-the-deceased',
    'ကဘူးလ်မြို့က စာအုပ်ဆိုင်ပိုင်ရှင် - စိန်ဝင်းစိန်': 'kabul-bookshop-owner',
    'ပန်းပန်လျှက်ပါ - ခင်နှင်းယု': 'pan-pan-lyak-par',
    'မွှေး၊ ကုသိုလ်ကြမ္မာ မမီပါခဲ့၊ အတွတ်ရေ… ကျွန်တော် တင်အောင်ထွန်း - ခင်နှင်းယု': 'fragrant-merit-fate',
        'ရယ်မောခြင်းပေါင်းချုပ် - မင်းလူ': 'min-lu-laughing-collection',
        'မင်းလူ ၏ ရယ်မောခြင်းပေါင်းချုပ် စာအုပ်အညွှန်း': 'min-lu-laughing-collection',
}

def get_slug_from_title(title):
    """Get a clean English slug for the post directory."""
    clean_title = re.sub(r'&\w+;', '', title).strip()
    if clean_title in SLUG_MAP:
        return SLUG_MAP[clean_title]
    slug = clean_title.strip()
    if len(slug) > 30:
        slug = slug[:30]
    slug = slug.replace(' ', '-')
    slug = re.sub(r'[^\w\-]', '', slug)
    if not slug:
        slug = hashlib.md5(clean_title.encode()).hexdigest()[:8]
    return slug

def extract_image(description):
    """Extract the first image URL from the post description."""
    img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', description)
    if img_match:
        return img_match.group(1)
    return ''

def extract_reviewer(description, blog_name=''):
    """Extract reviewer name from the post content."""
    # For Youths Book Reflections blog, always use blog name as reviewer
    if blog_name == 'Youths Book Reflections':
        return blog_name
    patterns = [
        r'Review\s+By\s+([^\n<]+)',
        r'ပြန်လည်သုံးသပ်သူ[.:]?\s*([^\n<]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    # Default: use blog name if available
    if blog_name:
        return blog_name
    return 'Whisper Of Words'

def is_book_review(title, description, excerpt):
    """Determine if a post is a book review (not a catalog/list)."""
    clean_title = re.sub(r'&\w+;', '', title).strip()
    if clean_title in EXCLUDE_TITLES:
        return False
    if 'စာအုပ်အရေအတွက်' in excerpt or 'Books (' in excerpt:
        return False
    return True

def bold_quotes(text):
    """Wrap text inside quotation marks with <strong> tags."""
    # Match “ ” (curly quotes)
    text = re.sub(r'“([^”]+)”', lambda m: '<strong>“' + m.group(1) + '”</strong>', text)
    # Match " " (straight double quotes) - only multi-char content
    text = re.sub(r'"([^"]{2,})"', lambda m: '<strong>"' + m.group(1) + '"</strong>', text)
    return text

def clean_text(text):
    """Remove HTML tags and clean up text, preserving paragraph breaks and links."""
    # Convert <br> and <p> to newlines before stripping other tags
    text = re.sub(r"""<br\s*/?>""", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"""<p[^>]*>""", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"""</p>""", "\n", text, flags=re.IGNORECASE)
    # Convert <a> tags to clickable links before stripping other tags
    text = re.sub(r"""<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>""", r"""<a href="\1" target="_blank" rel="noopener">\2</a>""", text, flags=re.IGNORECASE)
    # Strip remaining HTML tags except <a> links
    text = re.sub(r"""</?((?!a|/a)[^>]+)>""", "", text)
    text = re.sub(r"""&nbsp;""", " ", text)
    text = re.sub(r"""&#\d+;""", "", text)
    # Collapse multiple newlines but keep paragraph breaks
    text = re.sub(r"""\n{3,}""", "\n\n", text)
    text = re.sub(r"""[ \t]+""", " ", text)
    text = re.sub(r""" \n""", "\n", text)
    text = re.sub(r"""\n """, "\n", text)
    return text.strip()

def generate_post_html(post):
    """Generate a static HTML file for a blog post."""
    image_html = ''
    if post['image']:
        image_html = f'\n        <img src="{post["image"]}" alt="{post["title"]}" class="post-image">'

    html = f'''<!DOCTYPE html>
<html lang="my">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{post["title"]} - 𝐖𝐡𝐢𝐬𝐩𝐞𝐫 𝐎𝐟 𝐖𝐨𝐫𝐝𝐬 - 𝐦𝐦 𝐄𝐩𝐮𝐛</title>
    <style>
        @font-face {{
            font-family: 'PyidaungsuMM';
            src: url('https://raw.githubusercontent.com/WoWepub/Font/main/subset-Pyidaungsu.woff2') format('woff2');
            font-display: swap;
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'PyidaungsuMM', sans-serif;
            background: linear-gradient(135deg, #0d0b1e 0%, #151328 100%);
            color: #e0e0e0;
            line-height: 2;
            padding: 10px;
        }}

        .container {{
            max-width: 1600px;
            margin: 0 auto;
            background: #1a1830;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.4);
            overflow: hidden;
        }}

        header {{
            background: linear-gradient(135deg, #d84315 0%, #bf360c 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }}

        header h1 {{
            font-size: 1.8rem;
            margin-bottom: 10px;
            font-weight: 800;
        }}

        .post-meta {{
            font-size: 0.9rem;
            opacity: 0.9;
        }}

        .post-image {{
            width: 100%;
            height: auto;
            display: block;
            max-height: 600px;
            object-fit: contain;
            background: #151328;
        }}

        .post-body {{
            padding: 40px 60px;
            text-align: left;
            word-break: keep-all;
            overflow-wrap: break-word;
            font-kerning: normal;
            -webkit-font-smoothing: antialiased;
        }}

        .post-body p {{
            margin-bottom: 0.8em;
            padding: 0;
            letter-spacing: 0;
            word-spacing: 0.02em;
            font-size: 1.0rem;
            line-height: 1.85;
            color: #d0d0d0;

            text-rendering: optimizeLegibility;
        }}

        .post-body p + p {{

        }}

        .post-body p:first-child {{
            text-indent: 0;
        }}

        .post-body a {{
            color: #ff8a65;
            text-decoration: underline;
            text-decoration-color: rgba(255, 138, 101, 0.4);
            transition: all 0.2s ease;
        }}

        .post-body a:hover {{
            color: #ffab91;
            text-decoration-color: #ffab91;
        }}

        .back-link {{
            display: inline-block;
            margin-top: 30px;
            padding: 10px 20px;
            background: #ff8a65;
            color: #0d0b1e;
            text-decoration: none;
            border-radius: 5px;
            font-weight: 600;
        }}

        .reviewer-credit {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 2px solid #333;
            text-align: center;
            color: #666;
            font-style: italic;
        }}

        .social-links {{
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 20px 0 0;
            flex-wrap: wrap;
        }}
        .social-link {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 8px 16px;
            border-radius: 10px;
            font-size: 0.85em;
            text-decoration: none;
            transition: all 0.3s;
            font-weight: 500;
        }}
        .social-link.facebook {{ color: #fff; background: #1877f2; border: 1px solid #1877f2; }}
        .social-link.facebook:hover {{ background: #0d6efd; box-shadow: 0 4px 12px rgba(24,119,242,0.5); transform: translateY(-2px); }}
        .social-link.youtube {{ color: #fff; background: #ff0000; border: 1px solid #ff0000; }}
        .social-link.youtube:hover {{ background: #cc0000; box-shadow: 0 4px 12px rgba(255,0,0,0.5); transform: translateY(-2px); }}
        .social-link.twitter {{ color: #000; background: #fff; border: 1px solid #fff; }}
        .social-link.twitter:hover {{ background: #e0e0e0; box-shadow: 0 4px 12px rgba(255,255,255,0.3); transform: translateY(-2px); }}
        .social-link.telegram {{ color: #fff; background: #0088cc; border: 1px solid #0088cc; }}
        .social-link.telegram:hover {{ background: #006da3; box-shadow: 0 4px 12px rgba(0,136,204,0.5); transform: translateY(-2px); }}
        .social-icon {{ width: 18px; height: 18px; fill: currentColor; }}

        @media (max-width: 600px) {{
            header h1 {{ font-size: 1.4rem; }}
            .post-body {{ padding: 20px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{post["title"]}</h1>
            <div class="post-meta">📅 {post["date"]} • ✍️ {post["author"]}</div>
            <div class="social-links">
                <a href="https://www.facebook.com/mmebookwhisper/" class="social-link facebook" target="_blank">
                    <svg class="social-icon" viewBox="0 0 24 24"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
                    Facebook
                </a>
                <a href="https://www.youtube.com/@whisperofwordsebook" class="social-link youtube" target="_blank">
                    <svg class="social-icon" viewBox="0 0 24 24"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
                    YouTube
                </a>
                <a href="https://x.com/whisperw69842" class="social-link twitter" target="_blank">
                    <svg class="social-icon" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
                    Twitter/X
                </a>
                <a href="https://t.me/TheBookR" class="social-link telegram" target="_blank">
                    <svg class="social-icon" viewBox="0 0 24 24"><path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.479.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/></svg>
                    Telegram
                </a>
            </div>
        </header>
{image_html}
        <div class="post-body">
            <div class="post-content">
{post["content"]}
            </div>

            <div class="reviewer-credit">
                <p>Review By {post["author"]}</p>
                <p><a href="{post["source_url"]}" target="_blank" style="color: #ff8a65;">မူရင်းကို ဖတ်ရန် →</a></p>
            </div>

            <a href="../index.html" class="back-link">← ပင်မစာမျက်နှာသို့</a>
        </div>
    </div>
</body>
</html>'''
    return html

def main():
    import subprocess

    print("=== Sync Blog Posts ===")

    posts = []
    seen_slugs = set()

    for feed_info in FEEDS:
        feed_url = feed_info['feed_url']
        blog_name = feed_info['name']
        print(f"\nFetching: {blog_name}...")

        feed_path = os.path.join('/tmp', f'feeds_{blog_name.replace(" ", "_")}.xml')
        result = subprocess.run(['curl', '-s', '-o', feed_path, '-L', '--max-time', '30', feed_url],
                                capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  ERROR: Failed to fetch feed: {result.stderr}")
            continue

        if not os.path.exists(feed_path) or os.path.getsize(feed_path) < 1000:
            print(f"  ERROR: Feed file is too small or missing")
            continue

        print(f"  Feed downloaded ({os.path.getsize(feed_path)} bytes)")

        tree = ET.parse(feed_path)
        root = tree.getroot()
        channel = root.find('channel')
        items = channel.findall('item')

        print(f"  Found {len(items)} total posts in feed")

        for item in items:
            title = item.find('title').text or ''
            link = item.find('link').text or ''
            pub_date = item.find('pubDate').text or ''
            description = item.find('description').text or ''

            title = re.sub(r'&\w+;', '', title).strip()

            if not is_book_review(title, description, clean_text(description)):
                print(f"  SKIP: {title[:50]}")
                continue

            slug = get_slug_from_title(title)
            if slug in seen_slugs:
                print(f"  DUPLICATE: {title[:50]} (already from another blog)")
                continue
            seen_slugs.add(slug)

            image_url = extract_image(description)
            reviewer = extract_reviewer(description, blog_name)
            clean_desc = bold_quotes(clean_text(description))
            excerpt = clean_desc[:200] + "..." if len(clean_desc) > 200 else clean_desc

            try:
                dt = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %z')
                date_str = dt.strftime('%Y-%m-%d')
            except:
                date_str = pub_date

            # Build content paragraphs
            content_blocks = re.split(r'\n+', clean_desc)
            content_html = ''
            for block in content_blocks:
                block = block.strip()
                if len(block) > 10:
                    block = re.sub(r'\s+', ' ', block)
                    content_html += f'            <p>{block}</p>\n'

            post = {
                'id': slug,
                'title': title,
                'date': date_str,
                'category': 'စာအုပ်အညွှန်း',
                'author': reviewer,
                'image': image_url,
                'excerpt': excerpt,
                'link': f"{slug}/index.html",
                'source_url': link,
                'content': content_html
            }
            posts.append(post)
            print(f"  OK: {slug} -> {title[:60]}")

    print(f"\nIdentified {len(posts)} book review posts (from {len(FEEDS)} blog(s))")

    # Save posts.json - preserve manual posts not from feed
    posts_json = []
    feed_ids = set()
    for p in posts:
        feed_ids.add(p['id'])
        posts_json.append({
            'id': p['id'],
            'title': p['title'],
            'date': p['date'],
            'category': p['category'],
            'author': p['author'],
            'image': p['image'],
            'excerpt': p['excerpt'],
            'link': p['link'],
            'tags': [p['category']]
        })

    # Load existing posts.json and keep manual posts (not from feed)
    assets_dir = os.path.join(REPO_DIR, 'assets')
    os.makedirs(assets_dir, exist_ok=True)
    posts_json_path = os.path.join(assets_dir, 'posts.json')
    if os.path.exists(posts_json_path):
        try:
            with open(posts_json_path, 'r', encoding='utf-8') as f:
                existing = json.load(f)
            for ep in existing:
                if ep.get('id') not in feed_ids:
                    posts_json.append(ep)
                    print(f"  PRESERVED: {ep.get('title', '?')[:40]}")
        except:
            pass

    with open(posts_json_path, 'w', encoding='utf-8') as f:
        json.dump(posts_json, f, ensure_ascii=False, indent=2)
    print(f"Saved posts.json ({len(posts_json)} posts)")

    # Generate individual post HTML files
    for post in posts:
        post_dir = os.path.join(REPO_DIR, post['id'])
        os.makedirs(post_dir, exist_ok=True)
        html = generate_post_html(post)
        html_path = os.path.join(post_dir, 'index.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)

    print(f"Generated {len(posts)} post HTML files")
    print("=== Sync Complete ===")

if __name__ == '__main__':
    main()
