<div align="center">

<a href="https://whispermmepub.github.io/Review/">

<img src="https://blogger.googleusercontent.com/img/a/AVvXsEiz-kPEUW-4PhZ-CEATRgvFzmaJfZ6mL3BQ8kXuRmav6CborPuAv7wTt4FaWY9pLZoluFx6_BqZMdtmsbnNswQleuyADOrI0l4t5hEGhzlFO4Vn9zvL20KrYPiyoGA8IBS52gKKsXx_TD5AtEj9Nmr7mWLLNgIdB1SkFZiWxOz_XMGiov2BBDi9tm9zhIA=rw" width="100%" alt="Whisper Of Words Banner"/>

</a>

<br/>

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=28&duration=3000&pause=1000&color=00D4FF&center=true&vCenter=true&multiline=true&repeat=true&width=700&height=100&lines=%F0%9F%93%9A+Whisper+Of+Words+%E2%80%94+mm+Epub;Book+Review+Collection+for+Myanmar+Readers" alt="Typing SVG" />

<br/>

[![GitHub Pages](https://img.shields.io/badge/%F0%9F%8C%90_LIVE_SITE-Whisper_Of_Words-0ea5e9?style=for-the-badge&logo=githubpages&logoColor=white&labelColor=0c4a6e)](https://whispermmepub.github.io/Review/)
[![Blogspot](https://img.shields.io/badge/%F0%9F%93%9D_BLOG-Whisper1OF-f97316?style=for-the-badge&logo=blogger&logoColor=white&labelColor=c2410c)](https://whisper1of.blogspot.com)
[![Youths Book](https://img.shields.io/badge/%F0%9F%93%96_YOUTHS_BOOKS-Reflections-ef4444?style=for-the-badge&logo=blogger&logoColor=white&labelColor=dc2626)](https://youthsbookreflections.blogspot.com)

<br/>

[![GitHub Actions](https://img.shields.io/github/actions/workflow/status/whispermmepub/Review/sync-posts.yml?style=flat-square&logo=githubactions&logoColor=white&label=%F0%9F%94%84+AUTO+SYNC&color=238636)](https://github.com/whispermmepub/Review/actions)
[![GitHub Pages Status](https://img.shields.io/badge/%F0%9F%8C%8F+PAGES-ACTIVE-brightgreen?style=flat-square&logo=githubpages&logoColor=white)](https://whispermmepub.github.io/Review/)
[![Python](https://img.shields.io/badge/%F0%9F%90%8D+PYTHON-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org)
[![HTML5](https://img.shields.io/badge/%F0%9F%8C%90+HTML5-CSS3-E34F26?style=flat-square&logo=html5&logoColor=white)](https://developer.mozilla.org/en-US/docs/Glossary/HTML5)
[![License](https://img.shields.io/badge/%F0%9F%93%9C+LICENSE-MIT-blue?style=flat-square&logo=gitbook&logoColor=white)](LICENSE)
[![Posts](https://img.shields.io/badge/%F0%9F%93%96+POSTS-48+-9b59b6?style=flat-square&logo=bookstack&logoColor=white)](#-posts)

<br/>

<img src="https://komarev.com/ghpvc/?username=whispermmepub&label=Profile%20Views&color=0e75b6&style=flat-square&labelColor=1e293b" alt="Visitor Count" />

</div>

<br/>

<div align="center">

![Divider](https://img.shields.io/badge/_-0d1117?style=for-the-badge&labelColor=0d1117&label=═══════════════════════════════════════)

</div>

<br/>

## 🌟 About

<div align="center">

> *"စာဖတ်ခြင်းသည် ကမ္ဘာအနှံ့သို့ ခရီးထွက်ခြင်းပင်"*
> — Reading is traveling the world

**Whisper Of Words** သည် Blogspot မှ Book Reviews များကို **GitHub Actions** ဖြင့် Auto-Sync လုပ်ပြီး **GitHub Pages** တွင် **Myanmar Unicode Font** ဖြင့် လှပစွာ ပြသထားသည့် Book Review Collection ဖြစ်ပါသည်။

</div>

<br/>

---

<div align="center">

## 🎯 Features

</div>

<table>
<tr>
<td align="center" width="50%">

### ✨ Design
| Feature | Detail |
|:--------|:-------|
| 🎨 **Dark Theme** | Modern gradient home page |
| 📱 **Responsive** | Mobile · Tablet · Desktop |
| 🔤 **Pyidaungsu Font** | Myanmar Unicode native |
| 📐 **Justify Layout** | Professional text alignment |
| 🖼️ **Hero Banner** | Eye-catching header image |

</td>
<td align="center" width="50%">

### ⚡ Technology
| Feature | Detail |
|:--------|:-------|
| 🔄 **Auto Sync** | Every 6 hours via GitHub Actions |
| 🐍 **Python 3.11** | RSS → HTML generator |
| 📡 **Blogspot RSS** | Multi-source feed parsing |
| 🚀 **GitHub Pages** | Zero-cost global hosting |
| 📋 **JSON Metadata** | Structured post data |

</td>
</tr>
</table>

<br/>

---

<div align="center">

## 📂 Repository Structure

</div>

```
┌─────────────────────────────────────────────────────────────────┐
│  Review/                                                        │
│  ├── 🏠 index.html              ← Main page (dark theme)        │
│  ├── 📄 post-template.html      ← Post template (Pyidaungsu)    │
│  ├── 🔄 sync-posts.py          ← Blogspot RSS → HTML sync      │
│  ├── 📋 assets/                                             │
│  │   ├── posts.json             ← Posts metadata (JSON)         │
│  │   └── subset-*.woff2         ← Pyidaungsu font files        │
│  ├── ⚙️ .github/workflows/                                   │
│  │   └── sync-posts.yml         ← GitHub Actions workflow       │
│  └── 📖 {slug}/                                              │
│      └── index.html             ← Individual book reviews       │
└─────────────────────────────────────────────────────────────────┘
```

<br/>

---

<div align="center">

## ⚙️ How It Works

</div>

<div align="center">

```
  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
  │  ⏰ Cron │───▶│ 📡 RSS   │───▶│ 🐍 Python│───▶│ 📄 HTML  │───▶│ 🚀 Push  │
  │  Every   │    │  Fetch   │    │  Parse   │    │  Generate│    │  to Git  │
  │  6 hours │    │  Feeds   │    │  Posts   │    │  Pages   │    │  Pages   │
  └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
```

</div>

| Step | Action | Detail |
|:----:|:-------|:-------|
| **①** | **⏰ Schedule** | GitHub Actions cron — `0 */6 * * *` |
| **②** | **📡 RSS Fetch** | Pulls from [Whisper1OF](https://whisper1of.blogspot.com) + [Youths Book](https://youthsbookreflections.blogspot.com) |
| **③** | **🐍 Parse** | Python 3.11 — XML → JSON metadata + HTML pages |
| **④** | **📄 Generate** | Pyidaungsu font, justify layout, responsive design |
| **⑤** | **🚀 Deploy** | Auto-commit to `main` → GitHub Pages live |

<br/>

---

<div align="center">

## 🌐 Live Projects

</div>

<div align="center">

[![Review](https://img.shields.io/badge/%F0%9F%93%96_REVIEW-Book_Reviews_48+-9b59b6?style=for-the-badge&logo=readthedocs&logoColor=white)](https://whispermmepub.github.io/Review/)
[![Blog](https://img.shields.io/badge/%F0%9F%93%9D_BLOG-Myanmar_Books-3b82f6?style=for-the-badge&logo=blogger&logoColor=white)](https://whispermmepub.github.io/blog/)
[![Wow Books](https://img.shields.io/badge/%F0%9F%93%9A_WOW_BOOKS-Library-10b981?style=for-the-badge&logo=bookstack&logoColor=white)](https://whispermmepub.github.io/wow-books/)
[![Book Site](https://img.shields.io/badge/%F0%9F%93%84_BOOK_SITE-Collection-f59e0b?style=for-the-badge&logo=openbookinitiative&logoColor=white)](https://whispermmepub.github.io/book-site/)

</div>

<br/>

---

<div align="center">

## 🛠 Tech Stack

</div>

<div align="center">

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white&labelColor=2d3748)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white&labelColor=2d3748)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white&labelColor=2d3748)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white&labelColor=2d3748)
![GitHub Pages](https://img.shields.io/badge/GitHub_Pages-222222?style=for-the-badge&logo=githubpages&logoColor=white&labelColor=2d3748)
![JSON](https://img.shields.io/badge/JSON-000000?style=for-the-badge&logo=json&logoColor=white&labelColor=2d3748)

</div>

<br/>

---

<div align="center">

## 📊 GitHub Stats

</div>

<div align="center">

<a href="https://github.com/whispermmepub">
  <img height="180em" src="https://github-readme-stats.vercel.app/api/top-langs/?username=whispermmepub&layout=compact&theme=tokyonight&bg_color=0d1117&title_color=58a6ff&text_color=c9d1d9&hide_border=true&langs_count=8" alt="Top Languages" />
</a>

<a href="https://github.com/whispermmepub">
  <img height="180em" src="https://github-readme-stats.vercel.app/api?username=whispermmepub&show_icons=true&theme=tokyonight&hide_border=true&bg_color=0d1117&title_color=58a6ff&icon_color=79c0ff&text_color=c9d1d9&include_all_commits=true&count_private=true" alt="GitHub Stats" />
</a>

</div>

<br/>

---

<div align="center">

## 🏆 Trophies

</div>

<div align="center">

![trophy](https://github-profile-trophy.vercel.app/?username=whispermmepub&theme=tokyonight&no-frame=true&no-bg=true&column=7&margin-w=10)

</div>

<br/>

---

<div align="center">

## 📝 How to Contribute

</div>

### Step 1 — Add Metadata

`assets/posts.json` ထဲမှာ ထည့်ပါ:

```json
{
  "id": "post-XXX",
  "title": "စာအုပ်ခေါင်းစဉ်",
  "date": "2026-07-10",
  "category": "စာအုပ်",
  "author": "ရေးသားသူ",
  "image": "https://image-url.com/image.jpg",
  "excerpt": "အကျဉ်းချုပ်",
  "link": "{slug}/index.html",
  "tags": ["tag1", "tag2"]
}
```

### Step 2 — Create Post

`post-template.html` ကို အခြေခံပြီး `{slug}/index.html` ဖန်တီးပါ:

| Requirement | Detail |
|:------------|:-------|
| `text-align` | `justify` |
| `font` | Pyidaungsu (subset `.woff2`) |
| `images` | `assets/` folder ထဲမှာ |
| `lang` | `<html lang="my">` |

### Step 3 — Push

```bash
git add .
git commit -m "✨ Add new post: {slug}"
git push origin main
```

<br/>

---

<div align="center">

## 🌐 Deploy

</div>

1. **Settings** → **Pages**
2. **Source:** `main` branch → `/ (root)`
3. **Live:** [whispermmepub.github.io/Review](https://whispermmepub.github.io/Review/)

<br/>

---

<div align="center">

## 🌍 Find Me

[![Twitter](https://img.shields.io/badge/X_Twitter-000000?style=for-the-badge&logo=x&logoColor=white)](https://twitter.com/WhisperW69842)
[![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/whispermmepub)
[![Blog](https://img.shields.io/badge/Blogspot-FF5722?style=for-the-badge&logo=blogger&logoColor=white)](https://whisper1of.blogspot.com)
[![Live](https://img.shields.io/badge/Live_Site-0ea5e9?style=for-the-badge&logo=githubpages&logoColor=white)](https://whispermmepub.github.io/Review/)

</div>

<br/>

---

<div align="center">

![Divider](https://img.shields.io/badge/_-0d1117?style=for-the-badge&labelColor=0d1117&label=═══════════════════════════════════════)

<br/>

**Made with ❤️ for Myanmar Readers**

[![Whisper Of Words](https://img.shields.io/badge/%F0%9F%93%96_Whisper_Of_Words-0d1117?style=for-the-badge&labelColor=1e293b&label=WHISPER+OF+WORDS&logo=blogger&logoColor=white)](https://github.com/whispermmepub)

</div>
