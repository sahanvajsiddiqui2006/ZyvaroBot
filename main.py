import asyncio
import sqlite3
import random
import time
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# --- 1. CREDENTIALS ---
BOT_TOKEN = "8963537516:AAHai5H9r3R8sOc8Y1LzYRtPfkAKpUGvTHI"
ADMIN_ID = 8721064016
POSTBACK_SECRET = "ZyvaroSecureKey2026"
ADSGRAM_BLOCK_ID = "1njoD0"
RENDER_URL = "https://zyvaro-earn-bot.onrender.com"

COINS_PER_RUPEE = 10 

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()

user_last_click = {}
def is_spamming(user_id: int) -> bool:
    now = time.time()
    last = user_last_click.get(user_id, 0)
    if now - last < 1.0:
        return True
    user_last_click[user_id] = now
    return False

# --- 2. DATABASE ---
def init_db():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 0,
            referred_by INTEGER DEFAULT 0,
            referral_rewarded INTEGER DEFAULT 0,
            last_checkin INTEGER DEFAULT 0,
            streak_days INTEGER DEFAULT 0,
            scratch_cards INTEGER DEFAULT 0,
            ads_watched_today INTEGER DEFAULT 0,
            last_ad_time INTEGER DEFAULT 0
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY,
            title TEXT,
            url TEXT,
            coins_reward INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS completed_tasks (
            user_id INTEGER,
            task_id TEXT,
            timestamp INTEGER,
            PRIMARY KEY (user_id, task_id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS lifafa (
            code TEXT PRIMARY KEY,
            reward INTEGER,
            max_claims INTEGER,
            claimed_count INTEGER DEFAULT 0
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS claimed_lifafa (
            code TEXT,
            user_id INTEGER,
            PRIMARY KEY (code, user_id)
        )
    """)
    
    # 4 मुख्य CPA टास्क
    cur.execute("INSERT OR REPLACE INTO tasks VALUES ('navi_app', '🟢 Navi UPI / Cash (Download & Pay ₹1)', 'https://r.navi.com/tQWBgB?sub1=', 70)")
    cur.execute("INSERT OR REPLACE INTO tasks VALUES ('phonepe_app', '🟣 PhonePe UPI (Send ₹1)', 'https://phon.pe/ozu7alu7?sub1=', 50)")
    cur.execute("INSERT OR REPLACE INTO tasks VALUES ('extp_task1', '🔵 Kotak 811 Digital Account', 'https://extp.in/YOxbJV?sub1=', 250)")
    cur.execute("INSERT OR REPLACE INTO tasks VALUES ('extp_task2', '🟡 Angel One Demat Account', 'https://extp.in/4SwYOi?sub1=', 450)")
    cur.execute("INSERT OR REPLACE INTO lifafa VALUES ('ZYVARO100', 20, 100, 0)")
    
    conn.commit()
    conn.close()

init_db()

# --- 3. TELEGRAM BOT HANDLERS ---
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    if is_spamming(user_id):
        return

    args = message.text.split()
    referred_by = 0
    if len(args) > 1 and args[1].isdigit():
        referred_by = int(args[1])
        if referred_by == user_id:
            referred_by = 0

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users (user_id, referred_by) VALUES (?, ?)", (user_id, referred_by))
        conn.commit()
    conn.close()

    games_url = f"{RENDER_URL}/games-arcade"

    text = (
        f"🌟 <b>WELCOME TO ZYVARO VIP EARN HUB</b> 🌟\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👋 <b>नमस्ते {message.from_user.first_name}!</b>\n\n"
        f"🪙 <b>कॉइन रेट:</b> <code>10 Coins = ₹1.00 INR</code> 💵\n"
        f"⚡ <b>पेआउट:</b> <i>Instant UPI Bank Transfer (Min ₹10)</i>\n"
        f"🎁 <b>Loot:</b> हर ऐप पर <b>Cash + Lucky Scratch Card 🎟️</b>\n"
        f"👑 <b>Referral:</b> हर दोस्त पर <b>100 Coins (₹10)</b> कैश!\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 📋 ऑल टास्क लिस्ट (CPA Offers)", callback_data="tasks")],
        [InlineKeyboardButton(text="🎮 🕹️ OPEN 4-IN-1 GAMES ARCADE", web_app=WebAppInfo(url=games_url))],
        [InlineKeyboardButton(text="👛 💰 My Wallet & Balance", callback_data="wallet"), InlineKeyboardButton(text="🎟️ 🎁 Scratch Card", callback_data="scratch")],
        [InlineKeyboardButton(text="👑 👥 Invite Agent (₹10)", callback_data="refer"), InlineKeyboardButton(text="🔥 📅 Daily Streak", callback_data="streak")],
        [InlineKeyboardButton(text="⚡ 💳 INSTANT UPI CASHOUT 💳 ⚡", callback_data="withdraw")]
    ])
    await message.answer(text, parse_mode="HTML", reply_markup=kb)

@dp.callback_query(F.data == "wallet")
async def show_wallet(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if is_spamming(user_id):
        await callback.answer()
        return

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT balance, scratch_cards FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    balance = row[0] if row else 0
    cards = row[1] if row else 0
    conn.close()
    
    inr_val = balance / COINS_PER_RUPEE
    await callback.message.answer(
        f"💳 <b>ZYVARO WALLET DASHBOARD</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🪙 <b>टोटल बैलेंस:</b> <code>{balance} Coins</code>\n"
        f"💵 <b>रुपये में वैल्यू:</b> <code>₹{inr_val:.2f} INR</code>\n"
        f"🎟️ <b>स्क्रैच कार्ड्स:</b> <code>{cards}</code>\n\n"
        f"📌 *न्यूनतम विड्रॉल:* 100 Coins (₹10.00)",
        parse_mode="HTML"
    )
    await callback.answer()

@dp.callback_query(F.data == "tasks")
async def show_tasks(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT task_id, title, url, coins_reward FROM tasks")
    tasks = cur.fetchall()
    conn.close()

    text = "🔥 <b>HOT CPA EARNING OFFERS</b> 🔥\n━━━━━━━━━━━━━━━━━━━━\n"
    buttons = []
    for task_id, title, url, reward in tasks:
        track_url = f"{url}{user_id}"
        buttons.append([InlineKeyboardButton(text=f"{title} ➔ (+{reward} 🪙)", url=track_url)])
    
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()

@dp.callback_query(F.data == "scratch")
async def open_scratch(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT scratch_cards FROM users WHERE user_id = ?", (user_id,))
    cards = cur.fetchone()[0]

    if cards <= 0:
        await callback.message.answer("❌ <b>कोई स्क्रैच कार्ड नहीं है!</b>\nटास्क पूरा करें और फ्री कार्ड पाएं।", parse_mode="HTML")
        conn.close()
        await callback.answer()
        return

    win_amount = random.randint(10, 50)
    cur.execute("UPDATE users SET balance = balance + ?, scratch_cards = scratch_cards - 1 WHERE user_id = ?", (win_amount, user_id))
    conn.commit()
    conn.close()

    await callback.message.answer(f"🎉 <b>बधाई!</b> आपके कार्ड में <b>+{win_amount} Coins (₹{win_amount/10:.2f})</b> निकले!", parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "streak")
async def claim_streak(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    now = int(time.time())
    day_sec = 86400

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT last_checkin, streak_days FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    last_checkin, streak = row[0], row[1]

    if now - last_checkin < day_sec:
        await callback.message.answer("⏳ आप आज का बोनस ले चुके हैं!", parse_mode="HTML")
        conn.close()
        await callback.answer()
        return

    streak = min(streak + 1, 7) if now - last_checkin < (day_sec * 2) else 1
    reward = streak * 3 
    cur.execute("UPDATE users SET balance = balance + ?, last_checkin = ?, streak_days = ? WHERE user_id = ?",
                (reward, now, streak, user_id))
    conn.commit()
    conn.close()

    await callback.message.answer(f"🔥 <b>Day {streak} Streak Unlocked!</b> +{reward} Coins", parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "refer")
async def show_refer(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    await callback.message.answer(f"👑 <b>Referral Link:</b>\n<code>{ref_link}</code>\n\nदोस्त के पहले टास्क पर पाएँ <b>100 Coins (₹10)</b>!", parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "withdraw")
async def req_withdraw(callback: types.CallbackQuery):
    await callback.message.answer("⚡ <b>विड्रॉल कमांड:</b>\n<code>/payout <Coins> <UPI_ID></code>\n\nउदा: <code>/payout 100 name@okaxis</code>", parse_mode="HTML")
    await callback.answer()

@dp.message(Command("payout"))
async def process_payout(message: types.Message):
    user_id = message.from_user.id
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("❌ सही फॉर्मेट: <code>/payout <Coins> <UPI_ID></code>", parse_mode="HTML")
        return

    try:
        coins = int(parts[1])
        upi_id = parts[2]
    except ValueError:
        await message.answer("❌ अमान्य संख्या!", parse_mode="HTML")
        return

    if coins < 100:
        await message.answer("❌ न्यूनतम 100 Coins (₹10)!", parse_mode="HTML")
        return

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    res = cur.fetchone()
    balance = res[0] if res else 0

    if balance < coins:
        await message.answer("❌ बैलेंस कम है!", parse_mode="HTML")
        conn.close()
        return

    cur.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (coins, user_id))
    conn.commit()
    conn.close()

    inr_amount = coins / COINS_PER_RUPEE
    await message.answer(f"✅ ₹{inr_amount:.2f} की रिक्वेस्ट दर्ज हो गई!", parse_mode="HTML")
    await bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🚨 <b>NEW WITHDRAWAL!</b>\n👤 User: <code>{user_id}</code>\n💰 Coins: {coins} (₹{inr_amount:.2f})\n📍 UPI: <code>{upi_id}</code>",
        parse_mode="HTML"
    )

# --- 4. 4-IN-1 WEBAPP GAMES ARCADE ---
@app.get("/games-arcade", response_class=HTMLResponse)
async def games_arcade():
    return f"""
    <!DOCTYPE html>
    <html lang="hi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Zyvaro Arcade</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <script src="https://sad.adsgram.ai/js/sad.min.js"></script>
        <style>
            body {{ background: #0b0f19; color: #fff; font-family: sans-serif; text-align: center; padding: 15px; margin: 0; }}
            .card {{ background: #1e293b; border-radius: 12px; padding: 15px; margin-bottom: 12px; border: 1px solid #334155; }}
            .btn {{ background: linear-gradient(135deg, #2563eb, #7c3aed); color: #fff; border: none; padding: 12px 20px; font-weight: bold; border-radius: 8px; width: 100%; cursor: pointer; }}
            .tap-circle {{ width: 90px; height: 90px; border-radius: 50%; background: #ef4444; margin: 15px auto; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: bold; cursor: pointer; }}
        </style>
    </head>
    <body>
        <h2>🎮 Zyvaro WebApp Arcade</h2>

        <!-- Game 1: Watch Ad -->
        <div class="card">
            <h3>🎬 1. Watch HD Video Ad (+2 🪙)</h3>
            <button class="btn" onclick="playAd()">▶ Watch Ad</button>
        </div>

        <!-- Game 2: Lucky Number -->
        <div class="card">
            <h3>🔢 2. Lucky Number (1-5)</h3>
            <button class="btn" style="background:#059669;" onclick="playLucky()">Pick Number</button>
        </div>

        <!-- Game 3: Tap & Collect -->
        <div class="card">
            <h3>⚡ 3. Tap & Collect Fast</h3>
            <div class="tap-circle" id="tapBtn" onclick="tapCount()">TAP</div>
            <p id="tapScore">Score: 0</p>
        </div>

        <p id="status" style="color:#34d399; font-weight:bold;"></p>

        <script>
            const tg = window.Telegram.WebApp;
            tg.expand();
            const AdController = window.Adsgram.init({{ blockId: "{ADSGRAM_BLOCK_ID}" }});

            function playAd() {{
                AdController.show().then(() => {{
                    claimReward(2, "Ad Complete! +2 Coins");
                }}).catch(() => {{
                    document.getElementById('status').innerText = "❌ Ad not loaded!";
                }});
            }}

            function playLucky() {{
                let win = Math.random() > 0.5;
                if(win) claimReward(5, "🎉 You Picked Right! +5 Coins");
                else document.getElementById('status').innerText = "😢 Wrong Pick! Try again.";
            }}

            let score = 0;
            function tapCount() {{
                score++;
                document.getElementById('tapScore').innerText = "Score: " + score;
                if(score >= 10) {{
                    score = 0;
                    claimReward(3, "⚡ Speed Tap Master! +3 Coins");
                }}
            }}

            function claimReward(coins, msg) {{
                const uid = tg.initDataUnsafe && tg.initDataUnsafe.user ? tg.initDataUnsafe.user.id : null;
                fetch('/claim-game-reward', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ user_id: uid, reward: coins, secret: "{POSTBACK_SECRET}" }})
                }}).then(() => {{
                    document.getElementById('status').innerText = msg;
                }});
            }}
        </script>
    </body>
    </html>
    """

@app.post("/claim-game-reward")
async def claim_game_reward(req: Request):
    data = await req.json()
    if data.get("secret") != POSTBACK_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")
    user_id = data.get("user_id")
    reward = data.get("reward", 2)
    if not user_id:
        return {"status": "error"}

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (reward, user_id))
    conn.commit()
    conn.close()
    return {"status": "success"}

# --- 5. POSTBACK WEBHOOK ---
@app.get("/postback")
async def secure_postback(sub1: int, task_id: str, secret: str = ""):
    if secret != POSTBACK_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")

    user_id = sub1
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("SELECT coins_reward FROM tasks WHERE task_id = ?", (task_id,))
    task = cur.fetchone()
    if not task:
        conn.close()
        return {"status": "error"}

    reward_coins = task[0]

    cur.execute("SELECT 1 FROM completed_tasks WHERE user_id = ? AND task_id = ?", (user_id, task_id))
    if cur.fetchone():
        conn.close()
        return {"status": "already_completed"}

    now = int(time.time())
    cur.execute("INSERT INTO completed_tasks VALUES (?, ?, ?)", (user_id, task_id, now))
    cur.execute("UPDATE users SET balance = balance + ?, scratch_cards = scratch_cards + 1 WHERE user_id = ?", (reward_coins, user_id))

    cur.execute("SELECT referred_by, referral_rewarded FROM users WHERE user_id = ?", (user_id,))
    user_data = cur.fetchone()
    if user_data and user_data[0] != 0 and user_data[1] == 0:
        referrer_id = user_data[0]
        cur.execute("UPDATE users SET balance = balance + 100 WHERE user_id = ?", (referrer_id,))
        cur.execute("UPDATE users SET referral_rewarded = 1 WHERE user_id = ?", (user_id,))
        try:
            await bot.send_message(chat_id=referrer_id, text="🎉 <b>रेफरल अनलॉक!</b> +100 Coins (₹10)", parse_mode="HTML")
        except Exception:
            pass

    conn.commit()
    conn.close()
    return {"status": "success"}

# --- 6. START BOT ---
async def start_bot():
    await dp.start_polling(bot)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(start_bot())
