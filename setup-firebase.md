# Firebase Setup (2 minutes, free)

## Steps:
1. Go to https://console.firebase.google.com
2. Click "Create a project" → Name it anything (e.g., "book-comments")
3. Click "Continue" → Disable Google Analytics → "Create project"
4. Click "Realtime Database" → "Create Database" → "Start in test mode" → "Enable"
5. Go to "Project Settings" (gear icon) → "General" → "Your apps" → Click "</>" web icon
6. Register app with any nickname → Copy the config object

## Then paste the config values:
Replace the PLACEHOLDER values in `sync-posts.py` line with your config:

```
apiKey: "YOUR_apiKey",
authDomain: "YOUR_authDomain", 
databaseURL: "YOUR_databaseURL",
projectId: "YOUR_projectId",
storageBucket: "YOUR_storageBucket",
messagingSenderId: "YOUR_messagingSenderId",
appId: "YOUR_appId"
```

## After updating config:
Run `python3 sync-posts.py` and push to GitHub.

That's it! Views, comments will be shared across all visitors.
