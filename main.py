import asyncio
import sqlite3
import random
import time
from fastapi import FastAPI, Request, HTTPException
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- 1. CONFIGURATION & SECURITY ---
BOT_TOKEN = "8963537516:AAHai5H9r3R8sOc8Y1LzYRtPfkAKpUGvTHI"
ADMIN_ID = 8721064016
POSTBACK_SECRET = "ZyvaroSecureKey2026"  # यह सीक्रेट की हैकर्स को ब्लॉक रखेगी

COINS_PER_RUPEE = 10  # 10 Coins = ₹1 (100 Coins = ₹10)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()

# Anti-Spam Rate Limiter (Memory Storage)
user_last_click = {}

def is_spamming(user_id: int) -> bool:
    now = time.time()
    last = user_last_click.get(user_id, 0)
    if now - last < 1.5:  # 1.5 सेकंड से पहले दोबारा क्लिक करने पर ब्लॉक
        return True
    user_last_click[user_id] = now
    return False

# --- 2. DATABASE INITIALIZATION ---
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
            scratch_cards INTEGER DEFAULT 0
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
    
    # डिफ़ॉल्ट टास्क इंसर्ट करें
    cur.execute("""
        INSERT OR IGNORE INTO tasks (task_id, title, url, coins_reward) 
        VALUES ('navi_01', 'Navi UPI / Gold (Download & ₹1 Pay)', 'https://affiliate.example.com/click?sub1=', 70)
    """)
    cur.execute("""
        INSERT OR IGNORE INTO tasks (task_id, title, url, coins_reward) 
        VALUES ('kotak_01', 'Kotak 811 Zero Balance Account', 'https://affiliate.example.com/click?sub1=', 250)
    """)
    cur.execute("""
        INSERT OR IGNORE INTO tasks (task_id, title, url, coins_reward) 
        VALUES ('angel_01', 'Angel One Demat Account', 'https://affiliate.example.com/click?sub1=', 500)
    """)
    # डेमो लिफाफा कोड
    cur.execute("""
        INSERT OR IGNORE INTO lifafa (code, reward, max_claims) 
        VALUES ('ZYVARO50', 10, 50)
    """)
    conn.commit()
    conn.close()

init_db()

# --- 3. BOT CORE HANDLERS ---
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
        f"👋 **नमस्ते {message.from_user.first_name}!**\n\n"
        f"💰 **Zyvaro Earn Bot में आपका स्वागत है!**\n\n"
        f"🔹 **10 Coins = ₹1**\n"
        f"🔹 नए ऐप्स इंस्टॉल करें और डायरेक्ट बैंक विड्रॉल लें।\n"
        f"🔹 दोस्त को जोड़ें और पाएँ **100 Coins (₹10)** जब वह पहला ऐप इंस्टॉल करे।"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Tasks (CPA ऑफर्स)", callback_data="tasks")],
        [InlineKeyboardButton(text="👛 Wallet / Balance", callback_data="wallet"), InlineKeyboardButton(text="👥 Refer & Earn", callback_data="refer")],
        [InlineKeyboardButton(text="🎁 Daily Streak Bonus", callback_data="streak"), InlineKeyboardButton(text="🎟️ Scratch Card", callback_data="scratch")],
        [InlineKeyboardButton(text="🏏 Predict & Win", callback_data="predict"), InlineKeyboardButton(text="🎲 Dice Game", callback_data="game_dice")],
        [InlineKeyboardButton(text="⚡ Instant UPI Withdraw", callback_data="withdraw")]
    ])
    await message.answer(text, parse_mode="Markdown", reply_markup=kb)

@dp.callback_query(F.data == "wallet")
async def show_wallet(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if is_spamming(user_id):
        await callback.answer("⏳ कृपया धीरे क्लिक करें!")
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
        f"👛 **आपका वॉलेट बैलेंस:**\n\n"
        f"🪙 Coins: **{balance} Coins**\n"
        f"💵 Value: **₹{inr_val:.2f}**\n"
        f"🎟️ Available Scratch Cards: **{cards}**\n\n"
        f"📌 *न्यूनतम विड्रॉल: 100 Coins (₹10)*",
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "tasks")
async def show_tasks(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if is_spamming(user_id):
        await callback.answer("⏳ Wait...")
        return

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT task_id, title, url, coins_reward FROM tasks")
    tasks = cur.fetchall()
    conn.close()

    text = "📋 **उपलब्ध टास्क (Only for New Users):**\n\n"
    buttons = []
    for task_id, title, url, reward in tasks:
        track_url = f"{url}{user_id}"
        buttons.append([InlineKeyboardButton(text=f"👉 {title} (+{reward} Coins)", url=track_url)])
    
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer(
        text + "⚠️ *नियम: अगर यह ऐप आपके फोन में पहले कभी डाउनलोड था, तो रिवॉर्ड नहीं मिलेगा।*",
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
        remaining_hours = int((day_sec - (now - last_checkin)) / 3600)
        await callback.message.answer(f"⏳ आप आज का बोनस ले चुके हैं! अगला बोनस **{remaining_hours} घंटे** बाद मिलेगा।")
        conn.close()
        await callback.answer()
        return

    if now - last_checkin < (day_sec * 2):
        streak = min(streak + 1, 7)
    else:
        streak = 1

    reward = streak * 2  # Day 1 = 2 Coins, Day 7 = 14 Coins
    cur.execute("UPDATE users SET balance = balance + ?, last_checkin = ?, streak_days = ? WHERE user_id = ?",
                (reward, now, streak, user_id))
    conn.commit()
    conn.close()

    await callback.message.answer(
        f"🔥 **Day {streak} Streak Completed!**\n\n"
        f"🎉 आपको मिले: **+{reward} Coins**\n"
        f"लगातार 7 दिन बोट खोलें और बड़ा बोनस पाएं!",
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
        await callback.message.answer("❌ आपके पास कोई स्क्रैच कार्ड नहीं है! नए ऐप्स डाउनलोड करके टास्क पूरा करें और स्क्रैच कार्ड पाएं।")
        conn.close()
        await callback.answer()
        return

    win_amount = random.randint(10, 50)  # ₹1 से ₹5 रैंडम
    cur.execute("UPDATE users SET balance = balance + ?, scratch_cards = scratch_cards - 1 WHERE user_id = ?", (win_amount, user_id))
    conn.commit()
    conn.close()

    await callback.message.answer(
        f"🎟️ **SCRATCH CARD RESULT**\n\n"
        f"✨ आपने स्क्रैच किया और पाया...\n"
        f"🎉 **+{win_amount} Bonus Coins!** आपके वॉलेट में जोड़ दिए गए हैं।",
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "predict")
async def predict_win(callback: types.CallbackQuery):
    await callback.message.answer(
        "🏏 **Predict & Win Game**\n\n"
        "आज के मैच में कौन सी टीम जीतेगी?\n"
        "🔹 एंट्री फीस: **5 Coins**\n"
        "🔹 सही जवाब पर पूल प्राइज़ मिलेगा!\n\n"
        "कमांड भेजें:\n`/vote TeamA` या `/vote TeamB`",
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "refer")
async def show_refer(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    
    await callback.message.answer(
        f"👥 **Refer & Earn Program**\n\n"
        f"अपने दोस्तों को अपने लिंक से जोड़ें:\n`{ref_link}`\n\n"
        f"📌 **शर्त:** जब आपका दोस्त ऐप इंस्टॉल करके पहला टास्क पूरा करेगा, तभी आपको **100 Coins (₹10)** मिलेंगे!",
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
        await callback.message.answer("❌ डाइस गेम खेलने के लिए कम से कम 10 Coins होने चाहिए!")
        conn.close()
        await callback.answer()
        return

    dice_roll = random.randint(1, 6)
    if dice_roll >= 4:
        cur.execute("UPDATE users SET balance = balance + 5 WHERE user_id = ?", (user_id,))
        msg = f"🎲 डाइस नंबर: **{dice_roll}**\n🎉 बधाई! आप जीत गए! (+5 Coins)"
    else:
        cur.execute("UPDATE users SET balance = balance - 10 WHERE user_id = ?", (user_id,))
        msg = f"🎲 डाइस नंबर: **{dice_roll}**\n😢 आप हार गए! -10 Coins कट गए।"
    
    conn.commit()
    conn.close()
    await callback.message.answer(msg, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "withdraw")
async def req_withdraw(callback: types.CallbackQuery):
    await callback.message.answer(
        "💳 **विड्रॉल करने का तरीका:**\n\n"
        "चैट में यह कमांड लिखकर भेजें:\n`/payout <Coins> <UPI_ID>`\n\n"
        "उदाहरण:\n`/payout 100 myname@okaxis`\n*(न्यूनतम 100 Coins = ₹10)*",
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
    await message.answer(f"✅ आपकी ₹{inr_amount:.2f} की विड्रॉल रिक्वेस्ट दर्ज हो गई है! जल्द ही ट्रांसफर कर दिया जाएगा।")

    # एडमिन को डायरेक्ट अलर्ट
    await bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🔔 **नई विड्रॉल रिक्वेस्ट!**\n\n"
             f"👤 User ID: `{user_id}`\n"
             f"💰 Coins: {coins} (₹{inr_amount:.2f})\n"
             f"📍 UPI ID: `{upi_id}`",
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
        await message.answer("❌ यह लिफ़ाफ़ा कोड पूरा क्लेम हो चुका है!")
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

    await message.answer(f"🎉 बधाई! आपको **+{reward} Coins** लिफ़ाफ़ा बोनस मिला।")

# --- 4. SECURE POSTBACK WEBHOOK ---
@app.get("/postback")
async def secure_postback(sub1: int, task_id: str, secret: str = ""):
    # सीक्रेट की चेक करें ताकि कोई हैकर फेक रिक्वेस्ट न भेज सके
    if secret != POSTBACK_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid Secret Key")

    user_id = sub1
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("SELECT coins_reward FROM tasks WHERE task_id = ?", (task_id,))
    task = cur.fetchone()
    if not task:
        conn.close()
        return {"status": "error", "message": "Invalid Task"}

    reward_coins = task[0]

    cur.execute("SELECT 1 FROM completed_tasks WHERE user_id = ? AND task_id = ?", (user_id, task_id))
    if cur.fetchone():
        conn.close()
        return {"status": "already_completed"}

    # टास्क पूरा करें और स्क्रैच कार्ड + कॉइन दें
    now = int(time.time())
    cur.execute("INSERT INTO completed_tasks (user_id, task_id, timestamp) VALUES (?, ?, ?)", (user_id, task_id, now))
    cur.execute("UPDATE users SET balance = balance + ?, scratch_cards = scratch_cards + 1 WHERE user_id = ?", (reward_coins, user_id))

    # रेफरल अनलॉक
    cur.execute("SELECT referred_by, referral_rewarded FROM users WHERE user_id = ?", (user_id,))
    user_data = cur.fetchone()
    if user_data and user_data[0] != 0 and user_data[1] == 0:
        referrer_id = user_data[0]
        cur.execute("UPDATE users SET balance = balance + 100 WHERE user_id = ?", (referrer_id,))
        cur.execute("UPDATE users SET referral_rewarded = 1 WHERE user_id = ?", (user_id,))
        try:
            await bot.send_message(
                chat_id=referrer_id,
                text="🎉 आपके दोस्त ने पहला ऐप इंस्टॉल किया! आपका लॉक्ड **100 Coins (₹10)** रेफरल बोनस अनलॉक हो गया।"
            )
        except Exception:
            pass

    conn.commit()
    conn.close()

    try:
        await bot.send_message(
            chat_id=user_id,
            text=f"🎉 **टास्क स्वीकृत!** आपके वॉलेट में **{reward_coins} Coins** और **1 Scratch Card** जोड़ दिया गया है।"
        )
    except Exception:
        pass

    return {"status": "success"}

# --- 5. START SERVER ---
async def start_bot():
    await dp.start_polling(bot)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(start_bot())
