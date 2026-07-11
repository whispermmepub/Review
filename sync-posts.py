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
            padding: 0;
        }}

        .container {{
            width: 100%;
            background: #1a1830;
            overflow: hidden;
        }}

        header {{
            background: linear-gradient(135deg, #d84315 0%, #bf360c 100%);
            color: white;
            padding: 30px 12px;
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
            padding: 30px 12px;
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
            background: #1a1830;
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
            font-family: 'PyidaungsuMM', sans-serif;
            transition: all 0.25s ease;
        }}
        .telegram-btn:hover {{
            background: #006da3;
            box-shadow: 0 2px 10px rgba(0, 136, 204, 0.35);
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
            font-family: 'PyidaungsuMM', sans-serif;
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

        /* Comment Section */
        .comment-section {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #333;
        }}
        .comment-section h3 {{
            color: #ccc;
            font-size: 1.1rem;
            margin-bottom: 15px;
        }}
        .comment-form {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        .comment-form input, .comment-form textarea {{
            width: 100%;
            padding: 12px 15px;
            background: #151328;
            border: 1px solid #333;
            border-radius: 8px;
            color: #e0e0e0;
            font-family: 'PyidaungsuMM', sans-serif;
            font-size: 0.95rem;
            outline: none;
            transition: border-color 0.3s;
        }}
        .comment-form input:focus, .comment-form textarea:focus {{
            border-color: #4a9eff;
        }}
        .comment-form textarea {{
            min-height: 80px;
            resize: vertical;
        }}
        .comment-submit {{
            background: #4a9eff;
            color: #fff;
            border: none;
            padding: 10px 25px;
            border-radius: 8px;
            cursor: pointer;
            font-family: 'PyidaungsuMM', sans-serif;
            font-size: 0.95rem;
            font-weight: 600;
            transition: background 0.2s;
            align-self: flex-start;
        }}
        .comment-submit:hover {{ background: #357abd; }}
        .comment-list {{
            margin-top: 20px;
        }}
        .comment-item {{
            background: #151328;
            border-radius: 8px;
            padding: 12px 15px;
            margin-bottom: 10px;
            border-left: 3px solid #4a9eff;
        }}
        .comment-author {{
            color: #4a9eff;
            font-weight: 700;
            font-size: 0.9rem;
        }}
        .comment-date {{
            color: #666;
            font-size: 0.8rem;
            margin-left: 10px;
        }}
        .comment-text {{
            color: #ccc;
            margin-top: 5px;
            line-height: 1.6;
            font-size: 0.95rem;
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
            font-size: 1.4rem;
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
                <p><a href="{post["source_url"]}" target="_blank" style="color: #ff8a65;">မူရင်းကို ဖတ်ရန် →</a></p>
            </div>

            <a href="../index.html" class="back-link">← ပင်မစာမျက်နှာသို့</a>

            <div class="view-count" id="viewCount"></div>

            <div class="love-section">
                <a href="https://t.me/+q4jx63Zt5LBiMmI1" target="_blank" class="telegram-btn">
                    <svg class="telegram-icon" viewBox="0 0 24 24"><path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.479.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/></svg>
                    Bookish Discussion
                </a>
            </div>

            <div class="comment-section">
                <h3>💬 မှတ်ချက်ရေးရန်</h3>
                <div class="comment-form">
                    <input type="text" id="commentName" placeholder="သင့်နာမည်">
                    <textarea id="commentText" placeholder="မှတ်ချက်ရေးပါ..."></textarea>
                    <button class="comment-submit" onclick="addComment()">ပေးပို့ရန်</button>
                </div>
                <div class="comment-list" id="commentList"></div>
            </div>
        </div>
    </div>

    <button class="back-to-top" id="backToTop" onclick="scrollToTop()">↑</button>

    <script src="https://www.gstatic.com/firebasejs/8.10.1/firebase-app.js"></script>
    <script src="https://www.gstatic.com/firebasejs/8.10.1/firebase-database.js"></script>
    <script src="https://www.gstatic.com/firebasejs/8.10.1/firebase-app.js"></script>
    <script src="https://www.gstatic.com/firebasejs/8.10.1/firebase-database.js"></script>
    <script>
        var postSlug = '{post["id"]}';

        var firebaseConfig = {{
            apiKey: "AIzaSyD_PLACEHOLDER_REPLACE_ME",
            authDomain: "book-review-comments.firebaseapp.com",
            databaseURL: "https://book-review-comments-default-rtdb.firebaseio.com",
            projectId: "book-review-comments",
            storageBucket: "book-review-comments.appspot.com",
            messagingSenderId: "000000000000",
            appId: "1:000000000000:web:placeholder"
        }};
        firebase.initializeApp(firebaseConfig);
        var db = firebase.database();

        var viewRef = db.ref('posts/' + postSlug + '/views');
        viewRef.transaction(function(current) {{
            return (current || 0) + 1;
        }});
        viewRef.on('value', function(snap) {{
            document.getElementById('viewCount').innerHTML = '👁️ <span>' + (snap.val() || 0) + '</span>';
        }});

        var commentsRef = db.ref('posts/' + postSlug + '/comments');
        commentsRef.on('value', function(snap) {{
            var data = snap.val() || [];
            var list = document.getElementById('commentList');
            var arr = Object.values(data);
            if (arr.length === 0) {{ list.innerHTML = ''; return; }}
            list.innerHTML = arr.map(function(c) {{
                return '<div class="comment-item"><span class="comment-author">' + c.name + '</span><span class="comment-date">' + c.date + '</span><div class="comment-text">' + c.text + '</div></div>';
            }}).reverse().join('');
        }});

        function addComment() {{
            var name = document.getElementById('commentName').value.trim();
            var text = document.getElementById('commentText').value.trim();
            if (!name || !text) {{ alert('Name and comment required'); return; }}
            commentsRef.push({{ name: name, text: text, date: new Date().toLocaleDateString() }});
            document.getElementById('commentName').value = '';
            document.getElementById('commentText').value = '';
        }}

        window.addEventListener('scroll', function() {{
            var btn = document.getElementById('backToTop');
            if (window.scrollY > 300) {{ btn.style.display = 'flex'; }} else {{ btn.style.display = 'none'; }}
        }});
        function scrollToTop() {{ window.scrollTo({{ top: 0, behavior: 'smooth' }}); }}
    </script>
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
            clean_desc = clean_text(description)
            # Bold quotes but skip <a> tags
            clean_desc = bold_quotes_skip_links(clean_desc)
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
