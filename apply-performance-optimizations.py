#!/usr/bin/env python3
"""Idempotent performance patches that keep the current visual design unchanged."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent


def patch_sync_posts():
    path = ROOT / "sync-posts.py"
    text = path.read_text(encoding="utf-8")
    changed = False

    # 1) Make the reading progress bar compositor-friendly.
    if "/* Performance: GPU reading progress */" not in text:
        pattern = re.compile(
            r"        /\* Reading Progress Bar \*/\n"
            r"        \.reading-progress \{\{.*?\n"
            r"        \}\}\n\n"
            r"        /\* Reading Time \*/",
            re.DOTALL,
        )
        replacement = '''        /* Reading Progress Bar */
        /* Performance: GPU reading progress */
        .reading-progress {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 3px;
            background: linear-gradient(90deg, #8b5cf6, #ec4899);
            z-index: 9999;
            transform: scaleX(0);
            transform-origin: left center;
            will-change: transform;
        }}

        /* Reading Time */'''
        text, count = pattern.subn(replacement, text, count=1)
        if count != 1:
            raise SystemExit("Could not patch reading-progress CSS")
        changed = True

    # 2) Merge both scroll handlers into one passive requestAnimationFrame loop.
    if "// Performance: one passive RAF scroll handler" not in text:
        pattern = re.compile(
            r"        window\.addEventListener\('scroll', function\(\) \{\{.*?"
            r"        // Reading Time",
            re.DOTALL,
        )
        replacement = '''        // Performance: one passive RAF scroll handler
        var backToTopBtn = document.getElementById('backToTop');
        var readingProgress = document.getElementById('readingProgress');
        var scrollTicking = false;

        function updateScrollUI() {{
            var scrollTop = window.pageYOffset || document.documentElement.scrollTop || 0;
            if (backToTopBtn) {{
                backToTopBtn.style.display = scrollTop > 300 ? 'flex' : 'none';
            }}

            var scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
            var progress = scrollHeight > 0 ? Math.min(scrollTop / scrollHeight, 1) : 0;
            if (readingProgress) {{
                readingProgress.style.transform = 'scaleX(' + progress + ')';
            }}
            scrollTicking = false;
        }}

        window.addEventListener('scroll', function() {{
            if (!scrollTicking) {{
                scrollTicking = true;
                requestAnimationFrame(updateScrollUI);
            }}
        }}, {{ passive: true }});

        function scrollToTop() {{ window.scrollTo({{ top: 0, behavior: 'smooth' }}); }}
        updateScrollUI();

        // Reading Time'''
        text, count = pattern.subn(replacement, text, count=1)
        if count != 1:
            raise SystemExit("Could not patch scroll handlers")
        changed = True

    # 3) Avoid a JS exception when the optional bookmark button is absent.
    bookmark_old = "            var btn = document.getElementById('bookmarkBtn');\n            if (bookmarks.indexOf(pid) > -1) {{"
    bookmark_new = "            var btn = document.getElementById('bookmarkBtn');\n            if (!btn) return;\n            if (bookmarks.indexOf(pid) > -1) {{"
    if bookmark_old in text and "if (!btn) return;" not in text:
        text = text.replace(bookmark_old, bookmark_new, 1)
        changed = True

    if changed:
        path.write_text(text, encoding="utf-8")
        print("Applied post-page performance optimizations")
    else:
        print("Post-page performance optimizations already applied")


def patch_homepage():
    path = ROOT / "index.html"
    text = path.read_text(encoding="utf-8")
    changed = False

    # Build cards off-DOM and append them in one batch.
    if "// Performance: batch DOM insertion" not in text:
        old = "            posts.forEach(post => {"
        new = "            // Performance: batch DOM insertion\n            const fragment = document.createDocumentFragment();\n\n            posts.forEach(post => {"
        if old not in text:
            raise SystemExit("Could not find homepage post loop")
        text = text.replace(old, new, 1)

        old_tail = "                container.appendChild(card);\n            });\n        }"
        new_tail = "                fragment.appendChild(card);\n            });\n            container.appendChild(fragment);\n        }"
        if old_tail not in text:
            raise SystemExit("Could not patch homepage batched append")
        text = text.replace(old_tail, new_tail, 1)
        changed = True

    # Decode lazy card images asynchronously without changing appearance.
    old_img = '<img src="${post.image}" class="card-img" alt="${post.title}" loading="lazy">'
    new_img = '<img src="${post.image}" class="card-img" alt="${post.title}" loading="lazy" decoding="async" fetchpriority="low">'
    if old_img in text:
        text = text.replace(old_img, new_img, 1)
        changed = True

    # Debounce search so rapid typing does not rebuild ~160 cards on every keystroke.
    if "// Performance: debounced search" not in text:
        pattern = re.compile(
            r"        document\.getElementById\('search-input'\)\.addEventListener\('input', function\(\) \{.*?"
            r"        \}\);\n\n        loadPosts\(\);",
            re.DOTALL,
        )
        replacement = '''        // Performance: debounced search
        const searchInput = document.getElementById('search-input');
        let searchTimer = null;

        searchInput.addEventListener('input', function() {{
            const value = this.value;
            clearTimeout(searchTimer);
            searchTimer = setTimeout(function() {{
                const query = value.toLowerCase().trim();
                if (!query) {{
                    renderPosts(allPosts);
                    return;
                }}
                const filtered = allPosts.filter(p =>
                    (p.title && p.title.toLowerCase().includes(query)) ||
                    (p.author && p.author.toLowerCase().includes(query)) ||
                    (p.excerpt && p.excerpt.toLowerCase().includes(query))
                );
                renderPosts(filtered);
            }}, 120);
        }});

        loadPosts();'''
        text, count = pattern.subn(replacement, text, count=1)
        if count != 1:
            raise SystemExit("Could not patch homepage search handler")
        changed = True

    if changed:
        path.write_text(text, encoding="utf-8")
        print("Applied homepage performance optimizations")
    else:
        print("Homepage performance optimizations already applied")


if __name__ == "__main__":
    patch_sync_posts()
    patch_homepage()
