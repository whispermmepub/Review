#!/usr/bin/env python3
"""
Sync Blogspot book review posts to the Review GitHub site.
Fetches RSS feed, identifies book review posts, generates posts.json and HTML files.
Directory names use English romanized slugs for clean URLs.

This script is designed to be run by GitHub Actions workflow on a schedule
or on push events to keep the Review site in sync with the Blogspot blog.
"""


import json
import re
import os
import html as html_lib
import hashlib
import xml.etree.ElementTree as ET
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

def bold_quotes_skip_links(text):
    """Wrap text inside quotation marks with bold, but skip <a> tag content."""
    # Protect real <a> tags with placeholders
    links = []
    def save_link(m):
        links.append(m.group(0))
        return f'__LINK{len(links)-1}__'
    text = re.sub(r'<a [^>]*>.*?</a>', save_link, text, flags=re.DOTALL)
    # Match curly quotes
    text = re.sub(r'“([^”]+)”', lambda m: '<strong>“' + m.group(1) + '”</strong>', text)
    # Match straight double quotes - only multi-char content
    text = re.sub(r'"([^"]{2,})"', lambda m: '<strong>"' + m.group(1) + '"</strong>', text)
    # Restore <a> tags
    for i, link in enumerate(links):
        text = text.replace(f'__LINK{i}__', link)
    return text

def clean_text(text):
    """Remove HTML tags and clean up text, preserving paragraph breaks and content links."""
    # Convert <br> and <p> to newlines before stripping other tags
    text = re.sub(r"""<br\s*/?>""", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"""<p[^>]*>""", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"""</p>""", "\n", text, flags=re.IGNORECASE)
    # Remove <a> tags wrapping images (blogger image links)
    text = re.sub(r"""<a[^>]+href=["\'][^"\']*(blogger\.googleusercontent|googleusercontent)[^"\']*>\s*<img[^>]*>\s*</a>""", "", text, flags=re.IGNORECASE|re.DOTALL)
    # Remove <a> tags wrapping just images with no text
    text = re.sub(r"""<a[^>]+>\s*<img[^>]*>\s*</a>""", "", text, flags=re.IGNORECASE|re.DOTALL)
    # Remove <a name= anchors
    text = re.sub(r"""<a\s+name=["\'][^"\']*["\']\s*>\s*</a>""", "", text, flags=re.IGNORECASE)
    # Convert real <a> tags to clickable links
    text = re.sub(r"""<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>""", r"""<a href="\1" target="_blank" rel="noopener">\2</a>""", text, flags=re.IGNORECASE|re.DOTALL)
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

def build_preview_description(text, limit=140):
    """Build a short preview snippet for social sharing."""
    text = re.sub(r'\s+', ' ', text).strip()
    if not text:
        return 'စာအုပ်အညွှန်းများစုစည်းမှု'
    for separator in ['။', '.', '!', '?']:
        if separator in text:
            first_sentence = text.split(separator, 1)[0].strip()
            if len(first_sentence) >= 40:
                text = first_sentence + separator
                break
    if len(text) > limit:
        text = text[:limit].rsplit(' ', 1)[0].rstrip()
        text = text + '...'
    return text

def generate_post_html(post):
    """Generate a static HTML file for a blog post."""
    image_html = ''
    if post['image']:
        image_html = f'\n        <img src="{post["image"]}" alt="{post["title"]}" class="post-image">'
    preview_image = post['image'] or 'https://blogger.googleusercontent.com/img/a/AVvXsEiz-kPEUW-4PhZ-CEATRgvFzmaJfZ6mL3BQ8kXuRmav6CborPuAv7wTt4FaWY9pLZoluFx6_BqZMdtmsbnNswQleuyADOrI0l4t5hEGhzlFO4Vn9zvL20KrYPiyoGA8IBS52gKKsXx_TD5AtEj9Nmr7mWLLNgIdB1SkFZiWxOz_XMGiov2BBDi9tm9zhIA=rw'
    page_url = f'https://whispermmepub.github.io/Review/{post["link"]}'
    meta_title = html_lib.escape(f'{post["title"]} - 𝐖𝐡𝐢𝐬𝐩𝐞𝐫 𝐎𝐟 𝐖𝐨𝐫𝐝𝐬 - 𝐦𝐦 𝐄𝐩𝐮𝐛')
    meta_description = html_lib.escape(build_preview_description(re.sub(r'<[^>]+>', '', post.get("excerpt", ""))))
    preview_image_html = html_lib.escape(preview_image, quote=True)

    html = f'''<!DOCTYPE html>
<html lang="my">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{meta_title}</title>
    <meta name="description" content="{meta_description}">
    <link rel="canonical" href="{page_url}">
    <meta property="og:type" content="article">
    <meta property="og:title" content="{meta_title}">
    <meta property="og:description" content="{meta_description}">
    <meta property="og:url" content="{page_url}">
    <meta property="og:site_name" content="Whisper Of Words - mm Epub">
    <meta property="og:image" content="{preview_image}">
    <meta property="og:image:url" content="{preview_image_html}">
    <meta property="og:image:secure_url" content="{preview_image}">
    <meta property="og:image:type" content="image/jpeg">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta property="og:image:alt" content="{html_lib.escape(post['title'])}">
    <meta property="og:locale" content="my_MM">
    <meta name="twitter:card" content="summary_large_image">
    <link rel="manifest" href="/Review/manifest.json">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="theme-color" content="#141228">
    <meta name="google-site-verification" content="mss3y_pAIUpxusAJrt61me9Uy3G1PqsSe_WH_JP4SMA">
    <meta name="twitter:title" content="{meta_title}">
    <meta name="twitter:description" content="{meta_description}">
    <meta name="twitter:image" content="{preview_image}">
    <meta name="twitter:image:src" content="{preview_image_html}">
    <meta name="twitter:image:alt" content="{html_lib.escape(post['title'])}">
    <meta itemprop="image" content="{preview_image_html}">
    <link rel="image_src" href="{preview_image_html}">
    <style>
        @font-face {{
            font-family: 'Burma001';
            src: url('/Review/assets/Burma001-Regular.ttf') format('truetype');
            font-display: swap;
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Burma001', sans-serif;
            background: linear-gradient(135deg, #141228 0%, #1a1530 100%);
            color: #d0d0d0;
            line-height: 2;
            padding: 0;
        }}

        .container {{
            width: 100%;
            background: #1e1a35;
            overflow: hidden;
        }}

        header {{
            background: linear-gradient(135deg, #d84315 0%, #bf360c 100%);
            color: white;
            padding: 30px 12px;
            text-align: center;
        }}

        header h1 {{
            font-size: 1.5rem;
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
            padding: 30px 12px;
            text-align: left;
            word-break: keep-all;
            overflow-wrap: break-word;
            font-kerning: normal;
            -webkit-font-smoothing: antialiased;
        }}

        .post-body p {{
            margin-bottom: 1.2em;
            padding: 0;
            letter-spacing: 0.02em;
            word-spacing: 0.02em;
            font-size: 1.25rem;
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
            display: block;
            width: fit-content;
            margin: 30px auto 0;
            padding: 10px 20px;
            background: #1e1a35;
            color: #4a9eff;
            text-decoration: none;
            border-radius: 5px;
            font-weight: 700;
            border: 1px solid #4a9eff;
            transition: all 0.2s ease;
        }}

        .back-link:hover {{
            background: #4a9eff;
            color: #fff;
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
            gap: 4px;
            padding: 5px 10px;
            border-radius: 6px;
            font-size: 0.72em;
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
        .social-icon {{ width: 14px; height: 14px; fill: currentColor; }}

        @media (max-width: 600px) {{
            header h1 {{ font-size: 1.2rem; }}
            .post-body {{ padding: 20px; }}
        }}

        /* View Count & Love Button */
        .view-count {{
            text-align: center;
            padding: 15px 0 0;
            color: #888;
            font-size: 0.85rem;
        }}
        .view-count span {{ color: #4a9eff; font-weight: 700; }}
        .love-section {{
            text-align: center;
            padding: 30px 0;
            border-top: 1px solid #333;
            margin-top: 30px;
        }}
        .telegram-btn {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: #0088cc;
            color: #fff;
            padding: 8px 18px;
            border-radius: 6px;
            text-decoration: none;
            font-size: 0.9rem;
            font-weight: 600;
            font-family: 'Burma001', sans-serif;
            transition: all 0.25s ease;
        }}
        .telegram-btn:hover {{
            background: #006da3;
            box-shadow: 0 2px 10px rgba(0, 136, 204, 0.35);
        }}
        .help-blink {{
            text-align: center;
            margin: 18px 0 8px;
        }}
        .help-blink a {{
            display: inline-block;
            color: #00e676;
            font-weight: 700;
            font-size: 1rem;
            text-decoration: none;
            animation: blink-green 1.2s ease-in-out infinite;
        }}
        .help-blink a:hover {{
            text-shadow: 0 0 12px #00e676;
        }}
        @keyframes blink-green {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.3; }}
        }}
        .telegram-icon {{
            width: 14px;
            height: 14px;
            fill: currentColor;
            flex: 0 0 auto;
        }}
        .love-btn {{
            background: none;
            border: 2px solid #e74c3c;
            color: #e74c3c;
            font-size: 0.9rem;
            padding: 8px 20px;
            border-radius: 30px;
            cursor: pointer;
            transition: all 0.3s;
            font-family: 'Burma001', sans-serif;
        }}
        .love-btn:hover, .love-btn.liked {{
            background: #e74c3c;
            color: #fff;
            transform: scale(1.05);
            box-shadow: 0 4px 15px rgba(231, 76, 60, 0.4);
        }}
        .love-count {{
            color: #e74c3c;
            font-size: 0.9rem;
            margin-top: 8px;
        }}

        /* Back to Top */
        .back-to-top {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #4a9eff;
            color: #fff;
            border: none;
            width: 45px;
            height: 45px;
            border-radius: 50%;
            font-size: 1.2rem;
            cursor: pointer;
            display: none;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 12px rgba(74, 158, 255, 0.4);
            transition: all 0.3s;
            z-index: 999;
        }}
        .back-to-top:hover {{
            background: #357abd;
            transform: translateY(-3px);
        }}

        /* Reading Progress Bar */
        .reading-progress {{
            position: fixed;
            top: 0;
            left: 0;
            width: 0%;
            height: 3px;
            background: linear-gradient(90deg, #8b5cf6, #ec4899);
            z-index: 9999;
            transition: width 0.1s ease;
        }}

        /* Reading Time */
        .reading-time {{
            text-align: center;
            color: #888;
            font-size: 0.85rem;
            padding: 8px 0;
        }}
        .reading-time span {{ color: #8b5cf6; font-weight: 700; animation: blink-reading 1.5s ease-in-out infinite; }}
        @keyframes blink-reading {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.3; }}
        }}

        /* Share Buttons */
        .share-section {{
            display: flex;
            justify-content: center;
            gap: 10px;
            flex-wrap: wrap;
            padding: 15px 0;
        }}
        .share-btn {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 5px 10px;
            border-radius: 6px;
            font-size: 0.72rem;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s;
            color: #fff;
        }}
        .share-btn.tg {{ background: #0088cc; }}
        .share-btn.tg:hover {{ background: #006da3; box-shadow: 0 4px 12px rgba(0,136,204,0.4); }}
        .share-btn.fb {{ background: #1877f2; }}
        .share-btn.fb:hover {{ background: #0d6efd; box-shadow: 0 4px 12px rgba(24,119,242,0.4); }}
        .share-btn.viber {{ background: #7360f2; }}
        .share-btn.viber:hover {{ background: #5a48d4; box-shadow: 0 4px 12px rgba(115,96,242,0.4); }}


    </style>
</head>
<body>
    <div class="reading-progress" id="readingProgress"></div>
    <div class="container">
        <header>
            <h1>{post["title"]}</h1>
            <div class="post-meta">📅 {post["date"]} • ✍️ {post["author"]}</div>

        </header>

        <div class="reading-time" id="readingTime">📖 <span id="readTime"></span> ဖတ်ရန်အချိန်</div>

{image_html}
        <div class="post-body">
            <div class="post-content">
{post.get("content", "")}
            </div>

            <div class="reviewer-credit">
                <p>Review By {post["author"]}</p>
                <p><a href="{post["source_url"]}" target="_blank" style="color: #ff8a65;">မူရင်းကို ဖတ်ရန် →</a></p>
            </div>

            <a href="../index.html" class="back-link">← ပင်မစာမျက်နှာသို့</a>

            <div class="share-section">
                <a class="share-btn tg" id="shareTg" href="#" target="_blank">
                    📤 Telegram
                </a>
                <a class="share-btn fb" id="shareFb" href="#" target="_blank">
                    📤 Facebook
                </a>
                <a class="share-btn viber" id="shareViber" href="#" target="_blank">
                    📤 Viber
                </a>
            </div>


            <div class="love-section">
                <a href="https://t.me/+q4jx63Zt5LBiMmI1" target="_blank" class="telegram-btn">
                    <svg class="telegram-icon" viewBox="0 0 24 24"><path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.479.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/></svg>
                    Bookish Discussion
                </a>
            </div>

            <div class="help-blink">
                <a href="https://t.me/+q4jx63Zt5LBiMmI1" target="_blank">🔔 အကူအညီရယူရန် Discussion Group သို့ ဝင်ရောက်ပါ</a>
            </div>
        </div>
    </div>

    <button class="back-to-top" id="backToTop" onclick="scrollToTop()">↑</button>

    <script>


        window.addEventListener('scroll', function() {{
            var btn = document.getElementById('backToTop');
            if (window.scrollY > 300) {{ btn.style.display = 'flex'; }} else {{ btn.style.display = 'none'; }}
        }});
        function scrollToTop() {{ window.scrollTo({{ top: 0, behavior: 'smooth' }}); }}

        // Reading Progress
        window.addEventListener('scroll', function() {{
            var scrollTop = document.documentElement.scrollTop || document.body.scrollTop;
            var scrollHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
            var progress = (scrollTop / scrollHeight) * 100;
            document.getElementById('readingProgress').style.width = progress + '%';
        }});

        // Reading Time
        (function() {{
            var text = document.querySelector('.post-body').innerText;
            var words = text.split(/\s+/).length;
            var minutes = Math.ceil(words / 200);
            document.getElementById('readTime').textContent = minutes + ' min';
        }})();

        // Share URLs
        (function() {{
            var url = encodeURIComponent(window.location.href);
            var title = encodeURIComponent(document.title);
            document.getElementById('shareTg').href = 'https://t.me/share/url?url=' + url + '&text=' + title;
            document.getElementById('shareFb').href = 'https://www.facebook.com/sharer/sharer.php?u=' + url;
            document.getElementById('shareViber').href = 'viber://forward?text=' + title + '%20' + url;
        }})();

        // Bookmark
        var postId = window.location.pathname.match(/\/(\d+)\//);
        var pid = postId ? postId[1] : 'unknown';
        var bookmarks = JSON.parse(localStorage.getItem('bookmarks') || '[]');

        function updateBtn() {{
            var btn = document.getElementById('bookmarkBtn');
            if (bookmarks.indexOf(pid) > -1) {{
                btn.textContent = '🔖 Saved!';
                btn.classList.add('saved');
            }} else {{
                btn.textContent = '🔖 Save for Later';
                btn.classList.remove('saved');
            }}
        }}

        function toggleBookmark() {{
            var idx = bookmarks.indexOf(pid);
            if (idx > -1) {{
                bookmarks.splice(idx, 1);
            }} else {{
                bookmarks.push(pid);
            }}
            localStorage.setItem('bookmarks', JSON.stringify(bookmarks));
            updateBtn();
        }}

        updateBtn();
    </script>
    <script>
        if ('serviceWorker' in navigator) {{
            navigator.serviceWorker.register('/Review/sw.js')
            .then(function() {{ console.log('SW registered'); }})
            .catch(function(e) {{ console.log('SW failed:', e); }});
        }}
    </script>
</body>
</html>'''
    return html

def main():
    import subprocess

    print("=== Sync Blog Posts ===")

    posts = []
    seen_slugs = set()

    # Load existing posts.json to build title→post map and find highest ID
    assets_dir = os.path.join(REPO_DIR, 'assets')
    os.makedirs(assets_dir, exist_ok=True)
    posts_json_path = os.path.join(assets_dir, 'posts.json')
    existing_by_title = {}
    next_id = [0]
    if os.path.exists(posts_json_path):
        try:
            with open(posts_json_path, 'r', encoding='utf-8') as f:
                existing_posts = json.load(f)
            for ep in existing_posts:
                t = ep.get('title', '')
                if t:
                    existing_by_title[t] = ep
                try:
                    num = int(ep.get('id', '0'))
                    if num > next_id[0]:
                        next_id[0] = num
                except (ValueError, TypeError):
                    pass
            print(f"  Loaded existing posts.json: {len(existing_posts)} posts, highest ID = {next_id[0]}")
        except:
            pass

    # Build final posts list: update existing posts in-place, assign new IDs only for new posts
    posts_json = []
    updated_count = 0
    new_count = 0
    preserved_count = 0

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
            clean_desc = clean_text(description)
            clean_desc = bold_quotes_skip_links(clean_desc)
            excerpt = clean_desc[:200] + "..." if len(clean_desc) > 200 else clean_desc

            try:
                dt = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %z')
                date_str = dt.strftime('%Y-%m-%d')
            except:
                date_str = pub_date

            content_blocks = re.split(r'\n+', clean_desc)
            content_html = ''
            for block in content_blocks:
                block = block.strip()
                if len(block) > 10:
                    block = re.sub(r'\s+', ' ', block)
                    content_html += f'            <p>{block}</p>\n'

            # Check if post already exists by title — reuse its ID
            if title in existing_by_title:
                old = existing_by_title[title]
                numeric_id = old['id']
                print(f"  UPDATE: {numeric_id} -> {title[:60]}")
                updated_count += 1
                # Remove from existing so we don't double-add
                del existing_by_title[title]
            else:
                next_id[0] += 1
                numeric_id = str(next_id[0])
                new_count += 1
                print(f"  NEW: {numeric_id} -> {title[:60]}")

            posts.append({
                'id': numeric_id,
                'title': title,
                'date': date_str,
                'category': 'စာအုပ်အညွှန်း',
                'author': reviewer,
                'image': image_url,
                'excerpt': excerpt,
                'link': f"{numeric_id}/index.html",
                'source_url': link,
                'content': content_html
            })

    # Merge: updated/new feed posts + remaining existing posts (manual/not-from-feed)
    seen_ids = {p['id'] for p in posts}
    for title, ep in existing_by_title.items():
        if ep.get('id') not in seen_ids:
            # Ensure preserved posts have all required fields for HTML generation
            ep.setdefault('content', f'            <p>{ep.get("excerpt", "")}</p>')
            ep.setdefault('source_url', '')
            ep.setdefault('author', '')
            ep.setdefault('image', '')
            posts.append(ep)
            seen_ids.add(ep['id'])
            preserved_count += 1
            print(f"  PRESERVED: {ep.get('title', '?')[:40]}")

    # Build posts_json for saving
    posts_json = []
    for p in posts:
        posts_json.append({
            'id': p['id'],
            'title': p['title'],
            'date': p['date'],
            'category': p.get('category', ''),
            'author': p.get('author', ''),
            'image': p.get('image', ''),
            'excerpt': p.get('excerpt', ''),
            'link': p.get('link', ''),
            'tags': [p.get('category', '')]
        })

    # Sort posts by date descending (newest first) for homepage display
    posts_json.sort(key=lambda p: p.get('date', ''), reverse=True)

    with open(posts_json_path, 'w', encoding='utf-8') as f:
        json.dump(posts_json, f, ensure_ascii=False, indent=2)
    print(f"\nSaved posts.json ({len(posts_json)} posts) — {updated_count} updated, {new_count} new, {preserved_count} preserved")

    # Generate individual post HTML files
    for post in posts:
        post_dir = os.path.join(REPO_DIR, post['id'])
        os.makedirs(post_dir, exist_ok=True)
        html = generate_post_html(post)
        html_path = os.path.join(post_dir, 'index.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)

    print(f"Generated {len(posts)} post HTML files")

    # Generate sitemap.xml
    
    from xml.dom import minidom
    urlset = ET.Element('urlset')
    urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
    url = ET.SubElement(urlset, 'url')
    ET.SubElement(url, 'loc').text = 'https://whispermmepub.github.io/Review/'
    ET.SubElement(url, 'lastmod').text = datetime.now().strftime('%Y-%m-%d')
    ET.SubElement(url, 'changefreq').text = 'daily'
    ET.SubElement(url, 'priority').text = '1.0'
    for p in posts_json:
        url = ET.SubElement(urlset, 'url')
        ET.SubElement(url, 'loc').text = 'https://whispermmepub.github.io/Review/' + p['link']
        ET.SubElement(url, 'lastmod').text = p.get('date', datetime.now().strftime('%Y-%m-%d'))
        ET.SubElement(url, 'changefreq').text = 'monthly'
        ET.SubElement(url, 'priority').text = '0.8'
    sitemap_path = os.path.join(REPO_DIR, 'sitemap.xml')
    with open(sitemap_path, 'w', encoding='utf-8') as f:
        f.write(minidom.parseString(ET.tostring(urlset)).toprettyxml(indent='  '))
    print(f"Generated sitemap.xml ({len(posts_json) + 1} URLs)")
    print("=== Sync Complete ===")

if __name__ == '__main__':
    main()
