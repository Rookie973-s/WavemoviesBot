# Wavemovies Bot — Setup Guide

## Project Structure

```
wavemovies/
├── bot.py                  ← Entry point, starts the bot
├── config.py               ← All settings (token, channels, admins)
├── requirements.txt        ← Python dependencies
├── .env.example            ← Template for your secrets
├── Procfile                ← For Railway/Render deployment
├── handlers/
│   ├── start.py            ← /start command + file delivery
│   ├── verify.py           ← "I've Joined" button callback
│   └── admin.py            ← Admin: store files, view stats
└── utils/
    ├── database.py         ← MongoDB operations
    └── membership.py       ← Channel membership checker
```

---

## Step 1 — Create your bot on Telegram

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. When asked for a name, type: `Wavemovies`
4. When asked for a username, type something like: `wavemovies_bot`
5. BotFather will give you a **token** like:
   ```
   7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
   Copy and save this — it's your `BOT_TOKEN`.

---

## Step 2 — Get your Telegram user ID

1. Open Telegram and search for **@userinfobot**
2. Send `/start`
3. It will reply with your user ID, e.g. `Id: 987654321`
4. Save this — it's your `ADMIN_IDS` value.

---

## Step 3 — Create your Telegram channel (if you don't have one)

1. In Telegram, tap the pencil/compose icon → **New Channel**
2. Name it `Wavemovies` and make it **public**
3. Set a username like `@wavemovies`
4. **Add your bot as an admin** of this channel:
   - Go to channel settings → Administrators → Add Admin
   - Search for your bot username and add it
   - The bot needs at least **"Add Members"** permission to check membership

---

## Step 4 — Set up MongoDB

### Option A: Free cloud database (recommended)
1. Go to [mongodb.com/atlas](https://www.mongodb.com/atlas) and create a free account
2. Create a free **M0** cluster
3. Under **Database Access**, create a user with password
4. Under **Network Access**, add `0.0.0.0/0` (allow all IPs)
5. Click **Connect → Drivers** and copy the connection string, e.g.:
   ```
   mongodb+srv://myuser:mypassword@cluster0.xxxxx.mongodb.net/
   ```

### Option B: Local MongoDB (for testing only)
```bash
# Install MongoDB on Ubuntu/Debian
sudo apt install mongodb
sudo systemctl start mongodb
# Connection string: mongodb://localhost:27017
```

---

## Step 5 — Configure the bot

1. Copy the environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and fill in your values:
   ```env
   BOT_TOKEN=7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ADMIN_IDS=987654321
   MONGO_URI=mongodb+srv://myuser:mypassword@cluster0.xxxxx.mongodb.net/
   ```

3. Edit `config.py` — update the `REQUIRED_CHANNELS` list:
   ```python
   REQUIRED_CHANNELS = [
       {
           "name": "Wavemovies",
           "username": "@wavemovies",       # your actual channel username
           "url": "https://t.me/wavemovies", # your actual channel link
       },
   ]
   ```

---

## Step 6 — Install and run locally

```bash
# Make sure you have Python 3.11+
python --version

# Install dependencies
pip install -r requirements.txt

# Run the bot
python bot.py
```

You should see:
```
INFO - Wavemovies bot is running...
```

---

## Step 7 — Test it

1. Open your bot on Telegram (e.g. `t.me/wavemovies_bot`)
2. Send `/start` — you should see the join prompt if you haven't joined the channel
3. Join the channel, tap **"I've Joined — Check Again"**
4. You should see the welcome message

### Storing your first file (admin):
1. Open a private chat with your bot
2. Send any video, document, or photo
3. The bot replies with a shareable link like:
   ```
   https://t.me/wavemovies_bot?start=a3f9c12d45
   ```
4. Post that link in your channel
5. When users click it, they go through the join gate and receive the file

---

## Step 8 — Deploy to Railway (free hosting)

Railway lets you host the bot 24/7 for free (500 hours/month on free plan).

1. Go to [railway.app](https://railway.app) and sign up with GitHub
2. Click **New Project → Deploy from GitHub repo**
3. Push your code to a GitHub repo first:
   ```bash
   git init
   git add .
   git commit -m "Wavemovies bot"
   git remote add origin https://github.com/yourusername/wavemovies-bot.git
   git push -u origin main
   ```
4. In Railway, select your repo
5. Go to **Variables** tab and add:
   ```
   BOT_TOKEN    = your token
   ADMIN_IDS    = your user id
   MONGO_URI    = your mongodb atlas uri
   ```
6. Railway detects the `Procfile` and starts the bot automatically

### Alternative: Render.com
Same process — create a Background Worker service, set the build command to
`pip install -r requirements.txt` and start command to `python bot.py`.

---

## Admin Commands

| Action | How to do it |
|--------|-------------|
| Store a file | Send any file (video/doc/photo) to the bot in private chat |
| View stats | Send `/stats` to the bot |
| Get a shareable link | Automatically shown after sending a file |

---

## How the force-join works

1. User clicks a movie link or sends `/start`
2. Bot calls Telegram's `getChatMember` API for each required channel
3. If the user hasn't joined all channels → they see join buttons
4. When they tap "I've Joined" → bot re-checks membership
5. If verified → file is delivered instantly
6. If still not joined → prompt shown again

**Important:** Your bot must be an admin of every channel in `REQUIRED_CHANNELS` for the membership check to work. If the bot is not an admin, the check will fail and users will always see the join prompt.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Bot doesn't respond | Check `BOT_TOKEN` in `.env` is correct |
| "Can't check membership" error | Make bot an admin of your channel |
| Files not stored | Make sure your `ADMIN_IDS` matches your actual Telegram ID |
| MongoDB connection error | Check your `MONGO_URI` and that Atlas allows your IP |
| Bot stops after closing terminal | Deploy to Railway/Render for 24/7 uptime |
