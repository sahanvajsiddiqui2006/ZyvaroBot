import asyncio
import sqlite3
import random
import time
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# --- 1. CREDENTIALS & SECURITY ---
BOT_TOKEN = "8963537516:AAHai5H9r3R8sOc8Y1LzYRtPfkAKpUGvTHI"
ADMIN_ID = 8721064016
POSTBACK_SECRET = "ZyvaroSecureKey2026"
ADSGRAM_BLOCK_ID = "1njoD0"  # आपकी Adsgram Block ID

COINS_PER_RUPEE = 10 

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()

user_last_click = {}
def is_spamming(user_id: int) -> bool:
    now = time.time()
    last = user_last_click.get(user_id, 0)
    if now - last < 1.2:
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
    
    # आपके असली लिंक्स यहाँ सेट किए गए हैं
    cur.execute("""
        INSERT OR REPLACE INTO tasks (task_id, title, url, coins_reward) 
        VALUES ('navi_app', '🟢 Navi UPI / Cash (Download & Setup)', 'https://r.navi.com/tQWBgB?sub1=', 70)
    """)
    cur.execute("""
        INSERT OR REPLACE INTO tasks (task_id, title, url, coins_reward) 
        VALUES ('phonepe_app', '🟣 PhonePe UPI (Send ₹1)', 'https://phon.pe/ozu7alu7?sub1=', 50)
    """)
    cur.execute("""
        INSERT OR REPLACE INTO tasks (task_id, title, url, coins_reward) 
        VALUES ('extp_task1', '🔵 Special Cash Offer 1', 'https://extp.in/YOxbJV?sub1=', 60)
    """)
    cur.execute("""
        INSERT OR REPLACE INTO tasks (task_id, title, url, coins_reward) 
        VALUES ('extp_task2', '🟡 Special Cash Offer 2', 'https://extp.in/4SwYOi?sub1=', 80)
    """)
    cur.execute("""
        INSERT OR REPLACE INTO lifafa (code, reward, max_claims) 
        VALUES ('ZYVARO50', 10, 50)
    """)
    conn.commit()
    conn.close()

init_db()

# --- 3. BOT HANDLERS ---
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

    text = (
        f"👋 **नमस्ते {message.from_user.first_name}!** 🌟\n\n"
        f"💎 **Zyvaro Earn Club — Daily Cash & Rewards** 💎\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🪙 **10 Coins = ₹1.00**  |  ⚡ **Fast UPI Cashouts**\n"
        f"🎁 **Daily Loot:** हर ऐप इंस्टॉल पर पाएँ **Flat Cash + 1 Lucky Scratch Card** 🎟️\n"
        f"👑 दोस्त को जोड़ें और पाएँ **100 Coins (₹10)** जब वह पहला टास्क पूरा करे!\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👇 **नीचे दिए गए बटन दबाकर तुरंत कमाना शुरू करें:**"
    )
    
    # Mini App Video Ad URL
    ad_url = "https://zyvaro-earn-bot.onrender.com/watch-ad-page"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 📋 Hot CPA Loot Tasks", callback_data="tasks"), InlineKeyboardButton(text="🎬 🍿 Watch Video Ad (+2 🪙)", web_app=WebAppInfo(url=ad_url))],
        [InlineKeyboardButton(text="🎟️ 🎁 Scratch & Win", callback_data="scratch"), InlineKeyboardButton(text="👛 💰 My Wallet", callback_data="wallet")],
        [InlineKeyboardButton(text="👑 👥 Invite Agent (₹10)", callback_data="refer"), InlineKeyboardButton(text="🔥 📅 7-Day Streak", callback_data="streak")],
        [InlineKeyboardButton(text="🏏 🎯 Predict & Win", callback_data="predict"), InlineKeyboardButton(text="🎲 ⚡ Lucky Dice", callback_data="game_dice")],
        [InlineKeyboardButton(text="⚡ 💳 Instant UPI Bank Cashout ⚡", callback_data="withdraw")]
    ])
    await message.answer(text, parse_mode="Markdown", reply_markup=kb)

@dp.callback_query(F.data == "wallet")
async def show_wallet(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if is_spamming(user_id):
        await callback.answer("⏳ Please wait...")
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
        f"💳 **ZYVARO WALLET DASHBOARD** 💳\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🪙 **Total Balance:** `{balance}` Coins\n"
        f"💵 **Cash Value:** `₹{inr_val:.2f}` INR\n"
        f"🎟️ **Available Scratch Cards:** `{cards}` Cards\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 *न्यूनतम विड्रॉल सीमा: 100 Coins (₹10)*",
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "tasks")
async def show_tasks(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if is_spamming(user_id):
        await callback.answer()
        return

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT task_id, title, url, coins_reward FROM tasks")
    tasks = cur.fetchall()
    conn.close()

    text = "🔥 **HOT CPA EARNING OFFERS (New Users Only)** 🔥\n━━━━━━━━━━━━━━━━━━━━\n"
    buttons = []
    for task_id, title, url, reward in tasks:
        track_url = f"{url}{user_id}"
        buttons.append([InlineKeyboardButton(text=f"{title} ➔ (+{reward} 🪙)", url=track_url)])
    
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer(
        text + "⚠️ *नियम: ऐप डाउनलोड करें और पहला ट्रांज़ैक्शन / साइनअप पूरा करें। कॉइन्स ऑटोमैटिक वॉलेट में जुड़ जाएंगे।*",
        parse_mode="Markdown",
        reply_markup=kb
    )
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
        rem_hrs = int((day_sec - (now - last_checkin)) / 3600)
        await callback.message.answer(f"⏳ **आप आज का बोनस ले चुके हैं!**\nअगला चेक-इन **{rem_hrs} घंटे** बाद खुलेगा।")
        conn.close()
        await callback.answer()
        return

    if now - last_checkin < (day_sec * 2):
        streak = min(streak + 1, 7)
    else:
        streak = 1

    reward = streak * 2 
    cur.execute("UPDATE users SET balance = balance + ?, last_checkin = ?, streak_days = ? WHERE user_id = ?",
                (reward, now, streak, user_id))
    conn.commit()
    conn.close()

    await callback.message.answer(
        f"🔥 **DAY {streak} STREAK CLAIMED!** 🔥\n\n"
        f"🎉 आपको मिले: **+{reward} Coins** 🪙\n"
        f"लगातार 7 दिन बोट खोलें और जैकपॉट पाएं!",
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "scratch")
async def open_scratch(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT scratch_cards FROM users WHERE user_id = ?", (user_id,))
    cards = cur.fetchone()[0]

    if cards <= 0:
        await callback.message.answer("❌ **कोई स्क्रैच कार्ड नहीं बचा है!**\nनए ऐप्स डाउनलोड करके टास्क पूरे करें और हर टास्क पर 1 फ्री स्क्रैच कार्ड पाएं।")
        conn.close()
        await callback.answer()
        return

    win_amount = random.randint(10, 50)
    cur.execute("UPDATE users SET balance = balance + ?, scratch_cards = scratch_cards - 1 WHERE user_id = ?", (win_amount, user_id))
    conn.commit()
    conn.close()

    await callback.message.answer(
        f"✨ **SCRATCH & WIN JACKPOT!** ✨\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎉 बधाई! आपके स्क्रैच कार्ड में निकला:\n"
        f"💰 **+{win_amount} Bonus Coins (₹{win_amount/10:.2f})**\n"
        f"बैलेंस सीधे वॉलेट में जोड़ दिया गया है!",
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "predict")
async def predict_win(callback: types.CallbackQuery):
    await callback.message.answer(
        "🏏 **IPL / Match Predict & Win Pool** 🎯\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "आज का मुकाबला कौन जीतेगा?\n"
        "🔹 एंट्री फीस: **5 Coins**\n"
        "🔹 सही जवाब पर **Mega Prize Pool** से कॉइन्स मिलेंगे!\n\n"
        "वोट करने के लिए लिखें:\n`/vote TeamA` या `/vote TeamB`",
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "refer")
async def show_refer(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    
    await callback.message.answer(
        f"👑 **BECOME A ZYVARO VIP AGENT** 👑\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"अपने दोस्तों को अपने लिंक से जोड़ें:\n`{ref_link}`\n\n"
        f"💰 **रिवॉर्ड नियम:**\n"
        f"जब आपका दोस्त पहला ऐप इंस्टॉल करके पहला टास्क पूरा करेगा, तो आपको **100 Coins (₹10)** सीधे वॉलेट में मिलेंगे!",
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "game_dice")
async def play_dice(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    balance = cur.fetchone()[0]

    if balance < 10:
        await callback.message.answer("❌ डाइस गेम के लिए कम से कम 10 Coins होने चाहिए!")
        conn.close()
        await callback.answer()
        return

    dice_roll = random.randint(1, 6)
    if dice_roll >= 4:
        cur.execute("UPDATE users SET balance = balance + 5 WHERE user_id = ?", (user_id,))
        msg = f"🎲 डाइस नंबर: **{dice_roll}**\n🎉 **JACKPOT! आप जीत गए!** (+5 Coins)"
    else:
        cur.execute("UPDATE users SET balance = balance - 10 WHERE user_id = ?", (user_id,))
        msg = f"🎲 डाइस नंबर: **{dice_roll}**\n😢 **Bad Luck! आप हार गए!** (-10 Coins)"
    
    conn.commit()
    conn.close()
    await callback.message.answer(msg, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "withdraw")
async def req_withdraw(callback: types.CallbackQuery):
    await callback.message.answer(
        "⚡ **INSTANT UPI CASHOUT** ⚡\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        "चैट में यह कमांड लिखकर भेजें:\n`/payout <Coins> <UPI_ID>`\n\n"
        "📌 **उदाहरण:**\n`/payout 100 myname@okaxis`\n*(न्यूनतम 100 Coins = ₹10.00)*",
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.message(Command("payout"))
async def process_payout(message: types.Message):
    user_id = message.from_user.id
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("❌ सही फॉर्मेट: `/payout <Coins> <UPI_ID>`")
        return

    try:
        coins = int(parts[1])
        upi_id = parts[2]
    except ValueError:
        await message.answer("❌ Coins की संख्या सही डालें।")
        return

    if coins < 100:
        await message.answer("❌ न्यूनतम विड्रॉल 100 Coins (₹10) है।")
        return

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    res = cur.fetchone()
    balance = res[0] if res else 0

    if balance < coins:
        await message.answer("❌ आपके पास पर्याप्त बैलेंस नहीं है!")
        conn.close()
        return

    cur.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (coins, user_id))
    conn.commit()
    conn.close()

    inr_amount = coins / COINS_PER_RUPEE
    await message.answer(f"✅ **आपकी ₹{inr_amount:.2f} की रिक्वेस्ट दर्ज हो गई है!**\nएडमिन जल्द ही UPI में पैसे भेज देगा।")

    # एडमिन को सीधा अलर्ट
    await bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🚨 **NEW WITHDRAWAL REQUEST!** 🚨\n"
             f"━━━━━━━━━━━━━━━━━━━━\n"
             f"👤 **User ID:** `{user_id}`\n"
             f"💰 **Amount:** `{coins}` Coins (₹{inr_amount:.2f} INR)\n"
             f"📍 **UPI Address:** `{upi_id}`\n"
             f"━━━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown"
    )

@dp.message(Command("claim"))
async def claim_lifafa(message: types.Message):
    user_id = message.from_user.id
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("❌ कोड डालें! उदाहरण: `/claim ZYVARO50`")
        return
    
    code = parts[1].upper()
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    
    cur.execute("SELECT reward, max_claims, claimed_count FROM lifafa WHERE code = ?", (code,))
    row = cur.fetchone()
    if not row:
        await message.answer("❌ अमान्य प्रोमो कोड!")
        conn.close()
        return

    reward, max_claims, claimed_count = row[0], row[1], row[2]
    if claimed_count >= max_claims:
        await message.answer("❌ यह लिफ़ाफ़ा पूरा क्लेम हो चुका है!")
        conn.close()
        return

    cur.execute("SELECT 1 FROM claimed_lifafa WHERE code = ? AND user_id = ?", (code, user_id))
    if cur.fetchone():
        await message.answer("❌ आप यह कोड पहले ही क्लेम कर चुके हैं!")
        conn.close()
        return

    cur.execute("INSERT INTO claimed_lifafa (code, user_id) VALUES (?, ?)", (code, user_id))
    cur.execute("UPDATE lifafa SET claimed_count = claimed_count + 1 WHERE code = ?", (code,))
    cur.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (reward, user_id))
    conn.commit()
    conn.close()

    await message.answer(f"🎉 **बधाई! आपको +{reward} Coins का लिफ़ाफ़ा बोनस मिला!** 🎁")

# --- 4. VIDEO AD WEBPAGE (ADSGRAM INTEGRATION) ---
@app.get("/watch-ad-page", response_class=HTMLResponse)
async def watch_ad_page():
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Watch & Earn</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <script src="https://sad.adsgram.ai/js/sad.min.js"></script>
        <style>
            body {{
                background: #090d16;
                color: #ffffff;
                font-family: sans-serif;
                text-align: center;
                padding: 30px 15px;
            }}
            .btn {{
                background: linear-gradient(135deg, #2563eb, #7c3aed);
                color: #fff;
                border: none;
                padding: 14px 28px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 10px;
                cursor: pointer;
                box-shadow: 0 4px 15px rgba(37,99,235,0.4);
            }}
            .card {{
                background: #111827;
                border: 1px solid #1f2937;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>🎬 Watch Video Ad & Earn</h2>
            <p>15 सेकंड का वीडियो ऐड पूरा देखें और <b>+2 Coins</b> कमाएं!</p>
            <p style="color: #9ca3af; font-size: 13px;">(Daily Limit: 10 Ads)</p>
            <br>
            <button class="btn" onclick="playAd()">▶️ Watch Video Ad</button>
        </div>
        <p id="msg" style="color: #34d399; font-weight: bold;"></p>

        <script>
            const tg = window.Telegram.WebApp;
            tg.expand();

            const AdController = window.Adsgram.init({{ blockId: "{ADSGRAM_BLOCK_ID}" }});

            function playAd() {{
                AdController.show().then((result) => {{
                    document.getElementById('msg').innerText = "✅ ऐड पूरा देखा गया! कॉइन्स ऐड हो रहे हैं...";
                    
                    fetch('/claim-ad-reward', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ 
                            user_id: tg.initDataUnsafe.user.id,
                            secret: "{POSTBACK_SECRET}"
                        }})
                    }}).then(() => {{
                        setTimeout(() => {{ tg.close(); }}, 1500);
                    }});
                }}).catch((error) => {{
                    document.getElementById('msg').innerText = "❌ ऐड लोड नहीं हुआ या बीच में बंद किया गया!";
                }});
            }}
        </script>
    </body>
    </html>
    """

@app.post("/claim-ad-reward")
async def claim_ad_reward(req: Request):
    data = await req.json()
    if data.get("secret") != POSTBACK_SECRET:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    user_id = data.get("user_id")
    if not user_id:
        return {"status": "error"}

    now = int(time.time())
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT ads_watched_today, last_ad_time FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    
    ads_count = row[0] if row else 0
    last_ad = row[1] if row else 0

    if now - last_ad < 20:  # 20s cooldown
        conn.close()
        return {"status": "cooldown"}

    if ads_count >= 10:  # Daily limit
        conn.close()
        return {"status": "limit_reached"}

    cur.execute("UPDATE users SET balance = balance + 2, ads_watched_today = ads_watched_today + 1, last_ad_time = ? WHERE user_id = ?", (now, user_id))
    conn.commit()
    conn.close()

    try:
        await bot.send_message(chat_id=user_id, text="🎬 **वीडियो रिवॉर्ड:** आपके वॉलेट में **+2 Coins** जोड़ दिए गए हैं!")
    except Exception:
        pass

    return {"status": "success"}

# --- 5. SECURE POSTBACK WEBHOOK ---
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
    cur.execute("INSERT INTO completed_tasks (user_id, task_id, timestamp) VALUES (?, ?, ?)", (user_id, task_id, now))
    cur.execute("UPDATE users SET balance = balance + ?, scratch_cards = scratch_cards + 1 WHERE user_id = ?", (reward_coins, user_id))

    cur.execute("SELECT referred_by, referral_rewarded FROM users WHERE user_id = ?", (user_id,))
    user_data = cur.fetchone()
    if user_data and user_data[0] != 0 and user_data[1] == 0:
        referrer_id = user_data[0]
        cur.execute("UPDATE users SET balance = balance + 100 WHERE user_id = ?", (referrer_id,))
        cur.execute("UPDATE users SET referral_rewarded = 1 WHERE user_id = ?", (user_id,))
        try:
            await bot.send_message(
                chat_id=referrer_id,
                text="🎉 **रेफरल अनलॉक!** आपके दोस्त ने पहला ऐप इंस्टॉल किया। आपको **+100 Coins (₹10)** मिले! 👑"
            )
        except Exception:
            pass

    conn.commit()
    conn.close()

    try:
        await bot.send_message(
            chat_id=user_id,
            text=f"🎉 **टास्क स्वीकृत!** आपके वॉलेट में **+{reward_coins} Coins** और **1 Lucky Scratch Card** 🎟️ जोड़ दिया गया है!"
        )
    except Exception:
        pass

    return {"status": "success"}

# --- 6. START SERVER ---
async def start_bot():
    await dp.start_polling(bot)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(start_bot())
