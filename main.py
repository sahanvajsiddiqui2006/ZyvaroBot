import asyncio
import sqlite3
import random
import time
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# --- 1. CREDENTIALS & CONFIGURATION ---
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
            coins_reward INTEGER,
            category TEXT
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
    
    # 8+ नए और हाई-पेइंग CPA टास्क
    tasks_list = [
        ('navi_app', '🟢 ⚡ Navi UPI & Cash Loan (Setup & Pay ₹1)', 'https://r.navi.com/tQWBgB?sub1=', 70, 'UPI'),
        ('phonepe_app', '🟣 💸 PhonePe UPI (Register & ₹1 Transfer)', 'https://phon.pe/ozu7alu7?sub1=', 50, 'UPI'),
        ('kotak_811', '🔵 🏦 Kotak 811 Zero Balance Digital A/C', 'https://extp.in/YOxbJV?sub1=', 250, 'BANK'),
        ('angel_one', '🟡 📈 Angel One Free Demat A/C (+₹100 Cash)', 'https://extp.in/4SwYOi?sub1=', 450, 'DEMAT'),
        ('groww_app', '🟢 📊 Groww Mutual Fund & Stocks (Free Sign Up)', 'https://extp.in/YOxbJV?sub1=', 300, 'DEMAT'),
        ('airtel_bank', '🔴 📲 Airtel Payments Bank A/C', 'https://extp.in/4SwYOi?sub1=', 120, 'BANK'),
        ('mstock_app', '🟠 🚀 m.Stock Zero Brokerage Demat', 'https://extp.in/YOxbJV?sub1=', 500, 'DEMAT'),
        ('special_deal', '💎 🎁 Mega Bonus Cash Loot Task', 'https://extp.in/4SwYOi?sub1=', 150, 'SPECIAL')
    ]
    for tid, title, url, rew, cat in tasks_list:
        cur.execute("INSERT OR REPLACE INTO tasks (task_id, title, url, coins_reward, category) VALUES (?, ?, ?, ?, ?)", (tid, title, url, rew, cat))
    
    cur.execute("INSERT OR REPLACE INTO lifafa (code, reward, max_claims) VALUES ('ZYVARO100', 20, 100)")
    conn.commit()
    conn.close()

init_db()

# --- 3. COLORFUL TELEGRAM BOT HANDLERS ---
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
        f"🌟 <b>WELCOME TO ZYVARO VIP EARN CLUB</b> 🌟\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👋 <b>नमस्ते {message.from_user.first_name}!</b>\n\n"
        f"💰 <b>कॉइन रेट:</b> <code>10 Coins = ₹1.00 INR</code> 💵\n"
        f"⚡ <b>पेआउट:</b> <i>Instant UPI Bank Transfer (Min ₹10)</i>\n"
        f"🎁 <b>Loot:</b> हर ऐप पर <b>Cash + Lucky Scratch Card 🎟️</b>\n"
        f"👑 <b>Referral:</b> हर दोस्त पर <b>100 Coins (₹10)</b> कैश!\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👇 <b>नीचे दिए गए ऑप्शन्स से तुरंत अर्निंग शुरू करें:</b>"
    )
    
    video_ad_url = f"{RENDER_URL}/watch-ad-page"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 📋 ऑल टास्क लिस्ट (8+ ऑफर्स)", callback_data="tasks")],
        [InlineKeyboardButton(text="🎬 🍿 Watch HD Video Ad (+2 🪙)", web_app=WebAppInfo(url=video_ad_url))],
        [InlineKeyboardButton(text="🎟️ 🎁 Scratch & Win", callback_data="scratch"), InlineKeyboardButton(text="🎡 🎯 Spin Fortune Wheel", callback_data="spin_wheel")],
        [InlineKeyboardButton(text="💣 💥 Minesweeper Game", callback_data="game_mines"), InlineKeyboardButton(text="🎲 ⚡ Lucky 7 Dice", callback_data="game_dice")],
        [InlineKeyboardButton(text="👛 💰 My Wallet & Balance", callback_data="wallet"), InlineKeyboardButton(text="👑 👥 Invite Agent (₹10)", callback_data="refer")],
        [InlineKeyboardButton(text="🔥 📅 7-Day Streak Bonus", callback_data="streak"), InlineKeyboardButton(text="🏏 🎯 IPL Predict & Win", callback_data="predict")],
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
        f"╔═══════════════════════╗\n"
        f"  💎 <b>ZYVARO WALLET DASHBOARD</b> 💎\n"
        f"╚═══════════════════════╝\n\n"
        f"🪙 <b>टोटल बैलेंस:</b> <code>{balance} Coins</code>\n"
        f"💵 <b>रुपये में वैल्यू:</b> <code>₹{inr_val:.2f} INR</code>\n"
        f"🎟️ <b>अनलॉक्ड स्क्रैच कार्ड्स:</b> <code>{cards} Cards</code>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ <b>न्यूनतम विड्रॉल:</b> 100 Coins (₹10.00)\n"
        f"🚀 <b>पेमेंट स्पीड:</b> Instant UPI Direct Transfer",
        parse_mode="HTML"
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

    text = (
        f"🔥 <b>HOT CPA EARNING OFFERS (LIVE)</b> 🔥\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👉 <i>ऐप डाउनलोड करें, पहला ट्रांज़ैक्शन या फ्री अकाउंट बनाएं और बोट में ऑटोमैटिक कॉइन्स + स्क्रैच कार्ड पाएं!</i>\n\n"
    )
    buttons = []
    for task_id, title, url, reward in tasks:
        track_url = f"{url}{user_id}"
        buttons.append([InlineKeyboardButton(text=f"{title} ➔ (+{reward} 🪙)", url=track_url)])
    
    buttons.append([InlineKeyboardButton(text="🔙 बैक मेन मेन्यू", callback_data="main_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()

@dp.callback_query(F.data == "main_menu")
async def back_main(callback: types.CallbackQuery):
    await cmd_start(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "spin_wheel")
async def play_spin(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    balance = cur.fetchone()[0]

    if balance < 5:
        await callback.message.answer("❌ <b>Fortune Wheel</b> घुमाने के लिए कम से कम <b>5 Coins</b> होने चाहिए!", parse_mode="HTML")
        conn.close()
        await callback.answer()
        return

    prizes = [0, 2, 5, 10, 15, 25, 50]
    weights = [20, 30, 25, 15, 6, 3, 1]
    won = random.choices(prizes, weights=weights)[0]
    
    net_change = won - 5
    cur.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (net_change, user_id))
    conn.commit()
    conn.close()

    await callback.message.answer(
        f"🎡 <b>LUCKY WHEEL RESULT</b> 🎡\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌀 पहिया घूमा और रुका: <b>+{won} Coins</b> पर!\n"
        f"💰 <b>नेट परिणाम:</b> {f'+{net_change}' if net_change >= 0 else str(net_change)} Coins वॉलेट में अपडेट हो गए!",
        parse_mode="HTML"
    )
    await callback.answer()

@dp.callback_query(F.data == "game_mines")
async def play_mines(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    balance = cur.fetchone()[0]

    if balance < 10:
        await callback.message.answer("❌ <b>Minesweeper</b> खेलने के लिए कम से कम <b>10 Coins</b> होने चाहिए!", parse_mode="HTML")
        conn.close()
        await callback.answer()
        return

    # 70% Safe Chance, 30% Bomb
    outcome = random.choice(["SAFE", "SAFE", "SAFE", "BOMB"])
    if outcome == "SAFE":
        cur.execute("UPDATE users SET balance = balance + 10 WHERE user_id = ?", (user_id,))
        msg = "💣 <b>MINESWEEPER RESULT</b> 💣\n━━━━━━━━━━━━━━━━━━━━\n🟢 <b>SAFE TILE!</b> आपने बम बचा लिया!\n🎉 <b>बधाई: +10 Coins प्रॉफिट!</b> (कुल 20 Coins वापस)"
    else:
        cur.execute("UPDATE users SET balance = balance - 10 WHERE user_id = ?", (user_id,))
        msg = "💣 <b>MINESWEEPER RESULT</b> 💣\n━━━━━━━━━━━━━━━━━━━━\n💥 <b>BOOM!</b> बम फट गया!\n😢 <b>-10 Coins कट गए। अगली बार फिर कोशिश करें!</b>"

    conn.commit()
    conn.close()
    await callback.message.answer(msg, parse_mode="HTML")
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
        await callback.message.answer(f"⏳ <b>आज का बोनस क्लेम हो चुका है!</b>\nअगला चेक-इन <b>{rem_hrs} घंटे</b> बाद खुलेगा।", parse_mode="HTML")
        conn.close()
        await callback.answer()
        return

    if now - last_checkin < (day_sec * 2):
        streak = min(streak + 1, 7)
    else:
        streak = 1

    reward = streak * 3 
    cur.execute("UPDATE users SET balance = balance + ?, last_checkin = ?, streak_days = ? WHERE user_id = ?",
                (reward, now, streak, user_id))
    conn.commit()
    conn.close()

    await callback.message.answer(
        f"🔥 <b>DAY {streak} STREAK UNLOCKED!</b> 🔥\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎉 आपको मिले: <b>+{reward} Coins 🪙</b>\n"
        f"लगातार 7 दिन बोट खोलें और मेगा जैकपॉट पाएं!",
        parse_mode="HTML"
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
        await callback.message.answer("❌ <b>कोई स्क्रैच कार्ड नहीं बचा है!</b>\nटास्क पूरे करें और हर ऐप पर 1 फ्री स्क्रैच कार्ड पाएं।", parse_mode="HTML")
        conn.close()
        await callback.answer()
        return

    win_amount = random.randint(10, 50)
    cur.execute("UPDATE users SET balance = balance + ?, scratch_cards = scratch_cards - 1 WHERE user_id = ?", (win_amount, user_id))
    conn.commit()
    conn.close()

    await callback.message.answer(
        f"✨ <b>LUCKY SCRATCH CARD JACKPOT!</b> ✨\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎉 बधाई! आपके स्क्रैच कार्ड में निकला:\n"
        f"💰 <b>+{win_amount} Bonus Coins (₹{win_amount/10:.2f})</b>\n"
        f"बैलेंस तुरंत वॉलेट में क्रेडिट हो गया है!",
        parse_mode="HTML"
    )
    await callback.answer()

@dp.callback_query(F.data == "predict")
async def predict_win(callback: types.CallbackQuery):
    await callback.message.answer(
        "🏏 <b>IPL & MATCH PREDICTION POOL</b> 🎯\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "आज का मुकाबला कौन सी टीम जीतेगी?\n"
        "🔹 एंट्री फीस: <b>5 Coins</b>\n"
        "🔹 सही जवाब पर <b>Mega Prize Pool</b> शेयर मिलेगा!\n\n"
        "वोट करने के लिए लिखें:\n<code>/vote TeamA</code> या <code>/vote TeamB</code>",
        parse_mode="HTML"
    )
    await callback.answer()

@dp.callback_query(F.data == "refer")
async def show_refer(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    
    await callback.message.answer(
        f"👑 <b>ZYVARO VIP AGENT PROGRAM</b> 👑\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"अपने दोस्तों को अपने स्पेशल लिंक से जोड़ें:\n<code>{ref_link}</code>\n\n"
        f"💰 <b>कमाई का नियम:</b>\n"
        f"जब आपका दोस्त पहला टास्क पूरा करेगा, तो आपको <b>100 Coins (₹10.00)</b> सीधे वॉलेट में मिलेंगे!",
        parse_mode="HTML"
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
        await callback.message.answer("❌ डाइस गेम के लिए कम से कम 10 Coins होने चाहिए!", parse_mode="HTML")
        conn.close()
        await callback.answer()
        return

    dice_roll = random.randint(1, 6)
    if dice_roll >= 4:
        cur.execute("UPDATE users SET balance = balance + 5 WHERE user_id = ?", (user_id,))
        msg = f"🎲 डाइस नंबर: <b>{dice_roll}</b>\n🎉 <b>WINNER! आप जीत गए!</b> (+5 Coins)"
    else:
        cur.execute("UPDATE users SET balance = balance - 10 WHERE user_id = ?", (user_id,))
        msg = f"🎲 डाइस नंबर: <b>{dice_roll}</b>\n😢 <b>Better Luck Next Time!</b> (-10 Coins)"
    
    conn.commit()
    conn.close()
    await callback.message.answer(msg, parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "withdraw")
async def req_withdraw(callback: types.CallbackQuery):
    await callback.message.answer(
        "⚡ <b>INSTANT UPI CASHOUT REQUEST</b> ⚡\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "चैट में यह कमांड लिखकर भेजें:\n<code>/payout &lt;Coins&gt; &lt;UPI_ID&gt;</code>\n\n"
        "📌 <b>उदाहरण:</b>\n<code>/payout 100 myname@okaxis</code>\n*(न्यूनतम 100 Coins = ₹10.00 INR)*",
        parse_mode="HTML"
    )
    await callback.answer()

@dp.message(Command("payout"))
async def process_payout(message: types.Message):
    user_id = message.from_user.id
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("❌ सही फॉर्मेट: <code>/payout &lt;Coins&gt; &lt;UPI_ID&gt;</code>", parse_mode="HTML")
        return

    try:
        coins = int(parts[1])
        upi_id = parts[2]
    except ValueError:
        await message.answer("❌ Coins की संख्या सही डालें।")
        return

    if coins < 100:
        await message.answer("❌ न्यूनतम विड्रॉल 100 Coins (₹10.00) है।")
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
    await message.answer(f"✅ <b>आपकी ₹{inr_amount:.2f} की रिक्वेस्ट दर्ज हो गई है!</b>\nएडमिन 1 घंटे में UPI में पैसे ट्रांसफर कर देगा।", parse_mode="HTML")

    # एडमिन को कलरफुल अलर्ट
    await bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🚨 <b>NEW WITHDRAWAL ALERT!</b> 🚨\n"
             f"━━━━━━━━━━━━━━━━━━━━\n"
             f"👤 <b>User ID:</b> <code>{user_id}</code>\n"
             f"💰 <b>Amount:</b> <code>{coins} Coins</code> (<b>₹{inr_amount:.2f} INR</b>)\n"
             f"📍 <b>UPI Address:</b> <code>{upi_id}</code>\n"
             f"━━━━━━━━━━━━━━━━━━━━",
        parse_mode="HTML"
    )

@dp.message(Command("claim"))
async def claim_lifafa(message: types.Message):
    user_id = message.from_user.id
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("❌ कोड डालें! उदाहरण: <code>/claim ZYVARO100</code>", parse_mode="HTML")
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

    await message.answer(f"🎉 <b>बधाई! आपको +{reward} Coins का लिफ़ाफ़ा बोनस मिला!</b> 🎁", parse_mode="HTML")

# --- 4. FIXED VIDEO AD WEBPAGE (ADSGRAM FULL INTEGRATION) ---
@app.get("/watch-ad-page", response_class=HTMLResponse)
async def watch_ad_page():
    return f"""
    <!DOCTYPE html>
    <html lang="hi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Zyvaro Video Ads</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <script src="https://sad.adsgram.ai/js/sad.min.js"></script>
        <style>
            * {{ box-sizing: border-box; }}
            body {{
                background: linear-gradient(135deg, #090d16 0%, #111827 100%);
                color: #ffffff;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                text-align: center;
                padding: 24px 16px;
                margin: 0;
            }}
            .card {{
                background: #1f2937;
                border: 1.5px solid #374151;
                border-radius: 16px;
                padding: 24px 18px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.5);
                margin-top: 15px;
            }}
            .glow-btn {{
                background: linear-gradient(135deg, #2563eb, #7c3aed);
                color: #ffffff;
                border: none;
                padding: 16px 28px;
                font-size: 17px;
                font-weight: 800;
                border-radius: 12px;
                cursor: pointer;
                box-shadow: 0 4px 20px rgba(37,99,235,0.5);
                width: 100%;
                margin-top: 15px;
            }}
            .badge {{
                display: inline-block;
                background: #065f46;
                color: #34d399;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 13px;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <span class="badge">🎬 REWARDED VIDEO</span>
            <h2 style="margin: 12px 0 6px 0; color: #60a5fa;">Watch HD Video & Earn</h2>
            <p style="color: #cbd5e1; font-size: 14px; margin: 0 0 10px 0;">15 सेकंड का वीडियो ऐड पूरा देखें और <b>+2 Coins</b> तुरंत कमाएं!</p>
            <p style="color: #9ca3af; font-size: 12px;">(डेली लिमिट: 10 वीडियो ऐड्स)</p>
            <button class="glow-btn" id="playBtn" onclick="playAd()">▶️ Watch Video Ad Now</button>
        </div>
        <p id="msg" style="color: #34d399; font-weight: bold; margin-top: 20px; font-size: 15px;"></p>

        <script>
            const tg = window.Telegram.WebApp;
            tg.ready();
            tg.expand();

            const AdController = window.Adsgram.init({{ blockId: "{ADSGRAM_BLOCK_ID}" }});

            function playAd() {{
                const btn = document.getElementById('playBtn');
                btn.disabled = true;
                btn.innerText = "⏳ Loading Video...";

                AdController.show().then((result) => {{
                    document.getElementById('msg').innerText = "✅ ऐड पूरा देखा गया! +2 Coins जुड़ रहे हैं...";
                    
                    const userId = tg.initDataUnsafe && tg.initDataUnsafe.user ? tg.initDataUnsafe.user.id : null;
                    if(!userId) {{
                        document.getElementById('msg').innerText = "⚠️ Telegram context missing!";
                        return;
                    }}

                    fetch('/claim-ad-reward', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ 
                            user_id: userId,
                            secret: "{POSTBACK_SECRET}"
                        }})
                    }}).then(() => {{
                        setTimeout(() => {{ tg.close(); }}, 1200);
                    }});
                }}).catch((error) => {{
                    btn.disabled = false;
                    btn.innerText = "▶️ Watch Video Ad Now";
                    document.getElementById('msg').innerText = "❌ ऐड लोड नहीं हुआ! (AdBlocker/Private DNS बंद करें)";
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

    if now - last_ad < 15:
        conn.close()
        return {"status": "cooldown"}

    if ads_count >= 10:
        conn.close()
        return {"status": "limit_reached"}

    cur.execute("UPDATE users SET balance = balance + 2, ads_watched_today = ads_watched_today + 1, last_ad_time = ? WHERE user_id = ?", (now, user_id))
    conn.commit()
    conn.close()

    try:
        await bot.send_message(chat_id=user_id, text="🎬 <b>वीडियो रिवॉर्ड:</b> आपके वॉलेट में <b>+2 Coins</b> जोड़ दिए गए हैं! 🪙", parse_mode="HTML")
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
                text="🎉 <b>रेफरल अनलॉक!</b> आपके दोस्त ने पहला ऐप इंस्टॉल किया। आपको <b>+100 Coins (₹10.00)</b> मिले! 👑",
                parse_mode="HTML"
            )
        except Exception:
            pass

    conn.commit()
    conn.close()

    try:
        await bot.send_message(
            chat_id=user_id,
            text=f"🎉 <b>टास्क स्वीकृत!</b> आपके वॉलेट में <b>+{reward_coins} Coins</b> और <b>1 Lucky Scratch Card 🎟️</b> जोड़ दिया गया है!",
            parse_mode="HTML"
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
