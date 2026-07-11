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
FEED_URL = 'https://whisper1of.blogspot.com/feeds/posts/default?alt=rss'
BLOG_URL = 'https://whisper1of.blogspot.com'

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

def extract_reviewer(description):
    """Extract reviewer name from the post content."""
    patterns = [
        r'Review\s+By\s+([^\n<]+)',
        r'ပြန်လည်သုံးသပ်သူ[.:]?\s*([^\n<]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return 'Whisper Of Words'

def is_book_review(title, description, excerpt):
    """Determine if a post is a book review (not a catalog/list)."""
    clean_title = re.sub(r'&\w+;', '', title).strip()
    if clean_title in EXCLUDE_TITLES:
        return False
    if 'စာအုပ်အရေအတွက်' in excerpt or 'Books (' in excerpt:
        return False
    return True

def clean_text(text):
    """Remove HTML tags and clean up text, preserving paragraph breaks."""
    # Convert <br> and <p> to newlines before stripping other tags
    text = re.sub(r"""<br\s*/?>""", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"""<p[^>]*>""", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"""</p>""", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"""<[^>]+>""", "", text)
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
    <title>{post["title"]} - Whisper Of Words Book Reviews</title>
    <style>
        @font-face {{
            font-family: 'PyidaungsuMM';
            src: url('https://raw.githubusercontent.com/WoWepub/Font/main/subset-Pyidaungsu.woff2') format('woff2');
            font-display: swap;
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'PyidaungsuMM', sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            color: #2c3e50;
            line-height: 2;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
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
            background: #f9f9f9;
        }}

        .post-body {{
            padding: 40px 50px;
        }}

        .post-body p {{
            margin-bottom: 1.5em;
            text-align: justify;
            letter-spacing: 0.02em;
            word-spacing: 0.02em;
            font-size: 1.1rem;
            line-height: 2;
        }}

        .back-link {{
            display: inline-block;
            margin-top: 30px;
            padding: 10px 20px;
            background: #d84315;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-weight: 600;
        }}

        .reviewer-credit {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 2px solid #eee;
            text-align: center;
            color: #888;
            font-style: italic;
        }}

        @media (max-width: 600px) {{
            header h1 {{ font-size: 1.4rem; }}
            .post-body {{ padding: 25px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{post["title"]}</h1>
            <div class="post-meta">📅 {post["date"]} • ✍️ {post["author"]}</div>
        </header>
{image_html}
        <div class="post-body">
            <div class="post-content">
{post["content"]}
            </div>

            <div class="reviewer-credit">
                <p>Review By {post["author"]}</p>
                <p><a href="{post["source_url"]}" target="_blank" style="color: #d84315;">မူရင်းကို ဖတ်ရန် →</a></p>
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
    print("Fetching Blogspot RSS feed...")

    feed_path = os.path.join('/tmp', 'feeds.xml')
    result = subprocess.run(['curl', '-s', '-o', feed_path, '-L', '--max-time', '30', FEED_URL],
                            capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR: Failed to fetch feed: {result.stderr}")
        exit(1)

    if not os.path.exists(feed_path) or os.path.getsize(feed_path) < 1000:
        print("ERROR: Feed file is too small or missing")
        exit(1)

    print(f"Feed downloaded ({os.path.getsize(feed_path)} bytes)")

    tree = ET.parse(feed_path)
    root = tree.getroot()
    channel = root.find('channel')
    items = channel.findall('item')

    print(f"Found {len(items)} total posts in feed")

    posts = []
    for item in items:
        title = item.find('title').text or ''
        link = item.find('link').text or ''
        pub_date = item.find('pubDate').text or ''
        description = item.find('description').text or ''

        title = re.sub(r'&\w+;', '', title).strip()

        if not is_book_review(title, description, clean_text(description)):
            print(f"  SKIP: {title[:50]}")
            continue

        image_url = extract_image(description)
        reviewer = extract_reviewer(description)
        clean_desc = clean_text(description)
        excerpt = clean_desc[:200] + "..." if len(clean_desc) > 200 else clean_desc

        try:
            dt = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %z')
            date_str = dt.strftime('%Y-%m-%d')
        except:
            date_str = pub_date

        slug = get_slug_from_title(title)

        # Build content paragraphs
        content_blocks = re.split(r'\n+', clean_desc)
        content_html = ''
        for block in content_blocks:
            block = block.strip()
            if len(block) > 10:
                # Remove extra spaces inside the block
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

    print(f"\nIdentified {len(posts)} book review posts")

    # Save posts.json
    posts_json = []
    for p in posts:
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

    assets_dir = os.path.join(REPO_DIR, 'assets')
    os.makedirs(assets_dir, exist_ok=True)
    posts_json_path = os.path.join(assets_dir, 'posts.json')
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
