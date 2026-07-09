# Deploying to GitHub + Railway

## Part 1: Push to GitHub

### 1. Make sure your folder structure looks like this
```
music-bot/
├── main.py
├── config.py
├── requirements.txt
├── nixpacks.toml
├── Procfile
├── .gitignore
├── .env.example
├── generate_session.py
├── README.md
└── helpers/
    ├── auth.py
    ├── downloader.py
    ├── queue.py
    └── session.py
```
**Important:** `.env` should NOT be in this list — `.gitignore` will keep it out of GitHub automatically. Never commit real secrets.

### 2. Create a new repository on GitHub
- Go to https://github.com/new
- Give it a name (e.g. `telegram-music-bot`)
- Keep it **Private** (recommended, since it's tied to your bot/account)
- Don't initialize with a README (you already have one)
- Click "Create repository"

### 3. Push your code (run these in your bot folder)
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/telegram-music-bot.git
git push -u origin main
```
Replace `YOUR_USERNAME` with your actual GitHub username.

If asked for login, use a GitHub Personal Access Token (not your password) — GitHub will prompt you to generate one if needed.

---

## Part 2: Deploy on Railway

### 1. Create a new project
- Go to https://railway.app
- Click "New Project" → "Deploy from GitHub repo"
- Select your `telegram-music-bot` repository
- Railway will auto-detect Python and start building

### 2. Add environment variables
Railway does **not** use your `.env` file (it's excluded from git). Instead:
- Go to your Railway project → **Variables** tab
- Add each variable one by one:
  ```
  API_ID=20329123
  API_HASH=your_api_hash
  BOT_TOKEN=your_bot_token
  SESSION_STRING=your_session_string
  OWNER_ID=your_telegram_id
  ```

### 3. Set the start command (if not auto-detected)
- Go to **Settings** → **Deploy**
- Under "Start Command", make sure it's:
  ```
  python3 main.py
  ```
  (This should already be picked up from `Procfile` / `nixpacks.toml`, but double-check.)

### 4. Deploy
- Railway will automatically build and start the bot
- Check the **Deployments → Logs** tab — you should see:
  ```
  Bot and assistant are both up. Music bot is ready!
  ```

### 5. Test it
Go to your Telegram group, start the Voice Chat, and send:
```
/play tera ban jaunga
```

---

## Notes for Railway hosting
- **In-memory queue**: the current queue/auth/session data resets on every redeploy or restart. This is fine for casual use, but if you want it to persist, move `helpers/queue.py` etc. to a database (Railway offers free PostgreSQL/Redis add-ons).
- **Downloads folder**: songs are downloaded temporarily to `downloads/`. On Railway's ephemeral filesystem, these get cleared on redeploy — that's expected and fine.
- **Costs**: Railway's free tier has limited hours/month. A music bot running 24/7 will likely need a paid plan eventually — check Railway's current pricing at https://railway.app/pricing.
- Whenever you push new changes to GitHub, Railway will auto-redeploy (if auto-deploy is enabled in Settings).
