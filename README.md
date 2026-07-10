# 📚 Review - စာအုပ်နှင့် အဆောင်းပုံများ ပြန်လည်သုံးသပ်ခြင်း

ကြိုဆိုပါသည်။ ဤ Repository သည် စာအုပ်များ၊ အဆောင်းပုံများ နှင့် အခြားသော အကြောင်းအရာများကို ပြန်လည်သုံးသပ်ရန် ဘလော့ဂ်ပုံစံ ဖြစ်ပါသည်။

## 🎯 အစီအစဉ်

### Repository Structure

```
Review/
├── index.html              # ပင်မစာမျက်နှာ (Posts အညွှန်း)
├── posts.json              # Posts metadata
├── post-template.html      # Post template (Justify alignment & Pyidaungsu Font)
├── posts/                  # Individual post files
│   ├── post-001.html
│   ├── post-002.html
│   └── ...
├── assets/                 # ပုံများ နှင့် အခြားသော ဖိုင်များ
└── README.md               # ဤ ဖိုင်
```

## 📝 Post အသစ်ထည့်သွင်းခြင်း

### Step 1: Post Metadata ထည့်သွင်းခြင်း

`posts.json` ဖိုင်တွင် အောက်ပါအတိုင်း ထည့်သွင်းပါ:

```json
{
  "id": "post-XXX",
  "title": "အဆောင်းပုံ ခေါင်းစဉ်",
  "date": "2026-07-10",
  "category": "စာအုပ်/အဆောင်းပုံ/အခြား",
  "author": "ရေးသားသူ အမည်",
  "image": "https://image-url.com/image.jpg",
  "excerpt": "အဆောင်းပုံ အကျဉ်းချုပ်",
  "link": "posts/post-XXX.html",
  "tags": ["tag1", "tag2"]
}
```

### Step 2: Post HTML ဖိုင်ကို ဖန်တီးခြင်း

`posts/post-XXX.html` ဖိုင်ကို `post-template.html` အခြေခံပြီး ဖန်တီးပါ။

**အရေးကြီးသော အချက်များ:**
- စာသားများကို **Justify** alignment ဖြင့် ရေးသားပါ
- **Pyidaungsu Font** ကို အသုံးပြုပါ
- ပုံများကို `assets/` folder တွင် သိမ်းဆည်းပါ

### Step 3: GitHub သို့ Push ပြုလုပ်ခြင်း

```bash
git add .
git commit -m "Add new post: post-XXX"
git push origin main
```

## 🎨 Design Features

- ✅ Responsive Design (Mobile, Tablet, Desktop)
- ✅ Pyidaungsu Font အသုံးပြုခြင်း
- ✅ Justify Text Alignment
- ✅ Post အတစ်ခုချင်းစီအတွက် Unique URL
- ✅ Clean နှင့် Modern Design
- ✅ Easy Navigation

## 🌐 GitHub Pages တွင် Publish ပြုလုပ်ခြင်း

1. Repository Settings သို့ သွားပါ
2. GitHub Pages section တွင် `main` branch ကို ရွေးချယ်ပါ
3. Site သည် `https://whispermmepub.github.io/Review/` တွင် Live ဖြစ်သွားပါသည်

## 📋 Post Template အသုံးပြုခြင်း

```html
<!DOCTYPE html>
<html lang="my">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{POST_TITLE}} - Review</title>
    <!-- CSS သည် post-template.html တွင် ပါရှိပါသည် -->
</head>
<body>
    <div class="container">
        <header>
            <h1>{{POST_TITLE}}</h1>
            <div class="post-meta">
                <span>📅 {{POST_DATE}}</span>
                <span>📂 {{POST_CATEGORY}}</span>
                <span>✍️ {{POST_AUTHOR}}</span>
            </div>
        </header>

        <img src="{{POST_IMAGE}}" alt="{{POST_TITLE}}" class="post-image">

        <div class="post-body">
            <!-- စာသားများကို Justify alignment ဖြင့် ရေးသားပါ -->
            <p>ဤနေရာတွင် ပုံ နှင့် စာသားများကို ထည့်သွင်းပါ။</p>
        </div>
    </div>
</body>
</html>
```

## 📧 ဆက်သွယ်ရန်

Post အသစ်များ ထည့်သွင်းရန် သို့မဟုတ် အကူအညီ လိုအပ်ပါက ကျွန်တော့်ထံ ဆက်သွယ်ပါ။

---

**Repository URL:** https://github.com/whispermmepub/Review  
**Live Site:** https://whispermmepub.github.io/Review/
