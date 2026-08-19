import asyncio
import sqlite3
import random
import time
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# --- 1. GAME ENGINE CONFIGURATION ---
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
    if now - last < 0.8:
        return True
    user_last_click[user_id] = now
    return False

# --- 2. GAME DATABASE & RANKS ---
RANKS = {
    1: "🗡️ Novice Hunter",
    2: "🏹 Shadow Archer",
    3: "🛡️ Iron Knight",
    4: "⚡ Thunder Mage",
    5: "🐉 Dragon Slayer",
    6: "👑 Mythic Lord"
}

def init_db():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 0,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            energy INTEGER DEFAULT 100,
            last_energy_refill INTEGER DEFAULT 0,
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
            xp_reward INTEGER
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
    
    # ⚔️ BOSS QUESTS (CPA OFFERS)
    boss_quests = [
        ('navi_app', '🐉 [BOSS] Navi UPI Gold Quest', 'https://r.navi.com/tQWBgB?sub1=', 70, 150),
        ('phonepe_app', '⚡ [QUEST] PhonePe Cyber Transfer', 'https://phon.pe/ozu7alu7?sub1=', 50, 100),
        ('kotak_811', '🏰 [EPIC] Kotak 811 Treasury Vault', 'https://extp.in/YOxbJV?sub1=', 250, 400),
        ('angel_one', '👑 [LEGENDARY] Angel Demat Arena', 'https://extp.in/4SwYOi?sub1=', 450, 800),
        ('groww_app', '💎 [QUEST] Groww Stock Raider', 'https://extp.in/YOxbJV?sub1=', 300, 500),
        ('airtel_bank', '🛡️ [EPIC] Airtel Bank Fort', 'https://extp.in/4SwYOi?sub1=', 120, 250),
        ('mstock_app', '🔥 [LEGENDARY] m.Stock Zero Broker Guild', 'https://extp.in/YOxbJV?sub1=', 500, 1000)
    ]
    for tid, title, url, rew, xp in boss_quests:
        cur.execute("INSERT OR REPLACE INTO tasks (task_id, title, url, coins_reward, xp_reward) VALUES (?, ?, ?, ?, ?)", (tid, title, url, rew, xp))
    
    cur.execute("INSERT OR REPLACE INTO lifafa (code, reward, max_claims) VALUES ('LOOTBOX100', 20, 100)")
    conn.commit()
    conn.close()

init_db()

def get_player(user_id: int):
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT balance, xp, level, energy, scratch_cards FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row if row else (0, 0, 1, 100, 0)

# --- 3. GAMIFIED BOT UI & HANDLERS ---
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

    balance, xp, level, energy, loot_boxes = get_player(user_id)
    rank_title = RANKS.get(level, "👑 Mythic Lord")
    inr_cash = balance / COINS_PER_RUPEE

    # Game HUD Screen
    hud_text = (
        f"🎮 <b>═══ ZYVARO CYBER ARENA ═══</b> 🎮\n\n"
        f"👤 <b>Player:</b> <code>{message.from_user.first_name}</code>\n"
        f"🎖️ <b>Rank:</b> <b>{rank_title}</b> (Lv.{level})\n"
        f"⚡ <b>Energy:</b> <code>[{'█'*(energy//10)}{'░'*(10-(energy//10))}] {energy}/100</code>\n"
        f"🌟 <b>XP Points:</b> <code>{xp} XP</code>\n"
        f"🪙 <b>Gold Vault:</b> <code>{balance} Coins</code> (<b>₹{inr_cash:.2f} INR</b>)\n"
        f"🎁 <b>Loot Boxes:</b> <code>{loot_boxes} Ready to Open</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>MISSION:</b> Quests पूरे करो, Bosses हराओ और रियल कैश निकालो!"
    )
    
    ad_url = f"{RENDER_URL}/watch-ad-page"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️ BOSS QUESTS (Earn ₹70+)", callback_data="quests")],
        [InlineKeyboardButton(text="⚡ ENERGY STATION (Watch Ad +2🪙)", web_app=WebAppInfo(url=ad_url))],
        [InlineKeyboardButton(text="🎁 OPEN LOOT BOX", callback_data="loot_box"), InlineKeyboardButton(text="🎰 CYBER SPIN WHEEL", callback_data="spin_wheel")],
        [InlineKeyboardButton(text="💣 DUNGEON MINES (2X)", callback_data="game_mines"), InlineKeyboardButton(text="🎲 MONSTER DICE BATTLE", callback_data="game_dice")],
        [InlineKeyboardButton(text="🔥 7-DAY LOGIN STREAK", callback_data="streak"), InlineKeyboardButton(text="👑 GUILD RECRUIT (₹10)", callback_data="refer")],
        [InlineKeyboardButton(text="💎 🏦 CASHOUT TO BANK UPI 🏦 💎", callback_data="withdraw")]
    ])
    await message.answer(hud_text, parse_mode="HTML", reply_markup=kb)

@dp.callback_query(F.data == "quests")
async def show_quests(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if is_spamming(user_id):
        await callback.answer()
        return

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT task_id, title, url, coins_reward, xp_reward FROM tasks")
    tasks = cur.fetchall()
    conn.close()

    text = (
        f"⚔️ <b>AVAILABLE BOSS RAIDS & QUESTS</b> ⚔️\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <i>Boss Quests पूरा करो, Gold Coins जीतो और Level Up करो!</i>\n\n"
    )
    buttons = []
    for tid, title, url, rew, xp in tasks:
        track_url = f"{url}{user_id}"
        buttons.append([InlineKeyboardButton(text=f"{title} ➔ [+{rew}🪙 | +{xp}XP]", url=track_url)])
    
    buttons.append([InlineKeyboardButton(text="🔙 Back to Arena", callback_data="main_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()

@dp.callback_query(F.data == "main_menu")
async def back_to_menu(callback: types.CallbackQuery):
    await cmd_start(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "loot_box")
async def open_loot_box(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT scratch_cards FROM users WHERE user_id = ?", (user_id,))
    boxes = cur.fetchone()[0]

    if boxes <= 0:
        await callback.message.answer(
            "🔒 <b>NO LOOT BOXES AVAILABLE!</b>\n\n"
            "⚔️ <i>Boss Quests पूरे करें! हर ऐप डाउनलोड पर 1 Mythic Loot Box फ्री मिलता है।</i>",
            parse_mode="HTML"
        )
        conn.close()
        await callback.answer()
        return

    won_gold = random.randint(15, 60)
    won_xp = random.randint(50, 150)
    cur.execute("UPDATE users SET balance = balance + ?, xp = xp + ?, scratch_cards = scratch_cards - 1 WHERE user_id = ?", 
                (won_gold, won_xp, user_id))
    conn.commit()
    conn.close()

    await callback.message.answer(
        f"✨ <b>MYTHIC LOOT BOX OPENED!</b> ✨\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎉 <b>Loot Dropped:</b>\n"
        f"🪙 <b>+{won_gold} Gold Coins (₹{won_gold/10:.2f})</b>\n"
        f"🌟 <b>+{won_xp} Player XP</b>\n\n"
        f"🚀 <i>Vault में बैलेंस अपडेट हो गया!</i>",
        parse_mode="HTML"
    )
    await callback.answer()

@dp.callback_query(F.data == "game_mines")
async def play_mines(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    balance, xp, level, energy, _ = get_player(user_id)

    if balance < 10:
        await callback.message.answer("❌ Dungeon में उतरने के लिए कम से कम <b>10 Gold Coins</b> चाहिए!", parse_mode="HTML")
        await callback.answer()
        return

    outcome = random.choice(["SAFE", "SAFE", "SAFE", "BOMB"])
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    if outcome == "SAFE":
        cur.execute("UPDATE users SET balance = balance + 10, xp = xp + 30 WHERE user_id = ?", (user_id,))
        msg = (
            f"💣 <b>DUNGEON MINES RESULT</b> 💣\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🟩 <b>SAFE TILE CLEARED!</b> 💎\n"
            f"🏆 <b>Victory Loot:</b> +10 Gold (20 Total) & +30 XP!"
        )
    else:
        cur.execute("UPDATE users SET balance = balance - 10 WHERE user_id = ?", (user_id,))
        msg = (
            f"💣 <b>DUNGEON MINES RESULT</b> 💣\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💥 <b>BOMB EXPLODED!</b> 💀\n"
            f"🩸 <b>Damage:</b> -10 Gold lost in dungeon!"
        )
    
    conn.commit()
    conn.close()
    await callback.message.answer(msg, parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "game_dice")
async def play_dice(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    balance, _, _, _, _ = get_player(user_id)

    if balance < 10:
        await callback.message.answer("❌ Battle शुरू करने के लिए <b>10 Coins</b> चाहिए!", parse_mode="HTML")
        await callback.answer()
        return

    player_roll = random.randint(1, 6)
    monster_roll = random.randint(1, 6)

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    if player_roll > monster_roll:
        cur.execute("UPDATE users SET balance = balance + 8, xp = xp + 25 WHERE user_id = ?", (user_id,))
        msg = (
            f"🎲 <b>MONSTER BATTLE ARENA</b> ⚔️\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🤺 Your Hero Roll: <b>[{player_roll}]</b>\n"
            f"👹 Monster Roll: <b>[{monster_roll}]</b>\n\n"
            f"🎉 <b>VICTORY! Monster Defeated!</b>\n"
            f"💰 <b>Reward:</b> +8 Gold Coins & +25 XP!"
        )
    elif player_roll < monster_roll:
        cur.execute("UPDATE users SET balance = balance - 10 WHERE user_id = ?", (user_id,))
        msg = (
            f"🎲 <b>MONSTER BATTLE ARENA</b> ⚔️\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🤺 Your Hero Roll: <b>[{player_roll}]</b>\n"
            f"👹 Monster Roll: <b>[{monster_roll}]</b>\n\n"
            f"💀 <b>DEFEAT! Monster Overpowered You!</b>\n"
            f"🩸 -10 Gold Coins lost!"
        )
    else:
        msg = f"🎲 <b>DRAW!</b> दोनों का रोल <b>[{player_roll}]</b> था। सिक्के सुरक्षित हैं!"

    conn.commit()
    conn.close()
    await callback.message.answer(msg, parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "spin_wheel")
async def spin_wheel(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    balance, _, _, _, _ = get_player(user_id)

    if balance < 5:
        await callback.message.answer("❌ Arcade Spin के लिए कम से कम <b>5 Coins</b> चाहिए!", parse_mode="HTML")
        await callback.answer()
        return

    prizes = [0, 2, 5, 10, 20, 50]
    won = random.choice(prizes)
    net = won - 5

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + ?, xp = xp + 15 WHERE user_id = ?", (net, user_id))
    conn.commit()
    conn.close()

    await callback.message.answer(
        f"🎰 <b>CYBER ARCADE SPINNER</b> 🎰\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌀 Wheel रुक गया: <b>+{won} Gold Coins</b> पर!\n"
        f"💰 <b>Net Change:</b> {f'+{net}' if net >= 0 else str(net)} Gold Vault में गया!",
        parse_mode="HTML"
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
        await callback.message.answer(f"⏳ <b>Daily Bonus पहले से क्लेम है!</b>\nअगला ड्रॉप <b>{rem_hrs} घंटे</b> बाद आएगा।", parse_mode="HTML")
        conn.close()
        await callback.answer()
        return

    streak = min(streak + 1, 7) if now - last_checkin < (day_sec * 2) else 1
    reward = streak * 3 
    cur.execute("UPDATE users SET balance = balance + ?, last_checkin = ?, streak_days = ?, xp = xp + 50 WHERE user_id = ?",
                (reward, now, streak, user_id))
    conn.commit()
    conn.close()

    await callback.message.answer(
        f"🔥 <b>DAY {streak} QUEST STREAK CLAIMED!</b> 🔥\n\n"
        f"🪙 +{reward} Gold Coins\n"
        f"🌟 +50 XP Points\n"
        f"7 दिन लगातार लॉगिन करें और Grand Mystery Box पाएं!",
        parse_mode="HTML"
    )
    await callback.answer()

@dp.callback_query(F.data == "refer")
async def show_refer(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    
    await callback.message.answer(
        f"👑 <b>RECRUIT GUILD MEMBERS</b> 👑\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"अपने इनवाइट लिंक से दोस्तों को Guild में जोड़ें:\n<code>{ref_link}</code>\n\n"
        f"💰 <b>Bounty:</b> जब आपका रिक्रूट पहला Boss Quest पूरा करेगा, आपको मिलेंगे:\n"
        f"🪙 <b>100 Gold Coins (₹10.00)</b> + 🌟 <b>200 XP</b>!",
        parse_mode="HTML"
    )
    await callback.answer()

@dp.callback_query(F.data == "withdraw")
async def req_withdraw(callback: types.CallbackQuery):
    await callback.message.answer(
        "💎 <b>CASHOUT GOLD TO BANK UPI</b> 💎\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "कमांड भेजें:\n<code>/payout &lt;Coins&gt; &lt;UPI_ID&gt;</code>\n\n"
        "📌 <b>उदाहरण:</b>\n<code>/payout 100 myname@okaxis</code>\n*(100 Coins = ₹10.00)*",
        parse_mode="HTML"
    )
    await callback.answer()

@dp.message(Command("payout"))
async def process_payout(message: types.Message):
    user_id = message.from_user.id
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("❌ फॉर्मेट: <code>/payout &lt;Coins&gt; &lt;UPI_ID&gt;</code>", parse_mode="HTML")
        return

    try:
        coins = int(parts[1])
        upi_id = parts[2]
    except ValueError:
        await message.answer("❌ अमान्य संख्या!", parse_mode="HTML")
        return

    if coins < 100:
        await message.answer("❌ न्यूनतम विड्रॉल 100 Coins (₹10.00) है!", parse_mode="HTML")
        return

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    res = cur.fetchone()
    balance = res[0] if res else 0

    if balance < coins:
        await message.answer("❌ Vault में पर्याप्त सिक्के नहीं हैं!", parse_mode="HTML")
        conn.close()
        return

    cur.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (coins, user_id))
    conn.commit()
    conn.close()

    inr_amount = coins / COINS_PER_RUPEE
    await message.answer(f"✅ <b>₹{inr_amount:.2f} विड्रॉल रिक्वेस्ट प्रोसेस हो रही है!</b>", parse_mode="HTML")

    await bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🚨 <b>CASHOUT REQUEST ALERT!</b> 🚨\n"
             f"━━━━━━━━━━━━━━━━━━━━\n"
             f"👤 <b>Player ID:</b> <code>{user_id}</code>\n"
             f"🪙 <b>Coins:</b> <code>{coins}</code> (<b>₹{inr_amount:.2f} INR</b>)\n"
             f"📍 <b>UPI:</b> <code>{upi_id}</code>\n"
             f"━━━━━━━━━━━━━━━━━━━━",
        parse_mode="HTML"
    )

# --- 4. CYBERPUNK ARCADE WEBAPP (ADSGRAM REWARDED VIDEO) ---
@app.get("/watch-ad-page", response_class=HTMLResponse)
async def watch_ad_page():
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Cyber Arcade Video Vault</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <script src="https://sad.adsgram.ai/js/sad.min.js"></script>
        <style>
            * {{ box-sizing: border-box; }}
            body {{
                background: radial-gradient(circle at center, #1e1b4b 0%, #030712 100%);
                color: #ffffff;
                font-family: 'Courier New', Courier, monospace;
                text-align: center;
                padding: 24px 16px;
                margin: 0;
            }}
            .arcade-card {{
                background: rgba(17, 24, 39, 0.95);
                border: 2px solid #818cf8;
                border-radius: 16px;
                padding: 24px 18px;
                box-shadow: 0 0 25px rgba(99, 102, 241, 0.4);
                margin-top: 10px;
            }}
            .arcade-title {{
                font-size: 20px;
                font-weight: 900;
                color: #38bdf8;
                text-shadow: 0 0 10px #38bdf8;
                margin-bottom: 8px;
            }}
            .neon-btn {{
                background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%);
                color: #ffffff;
                border: none;
                padding: 16px 24px;
                font-size: 16px;
                font-weight: 900;
                border-radius: 10px;
                cursor: pointer;
                box-shadow: 0 0 20px rgba(236, 72, 153, 0.6);
                width: 100%;
                margin-top: 15px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            .energy-box {{
                display: inline-block;
                background: #064e3b;
                color: #34d399;
                border: 1px solid #10b981;
                padding: 6px 14px;
                border-radius: 8px;
                font-size: 12px;
                font-weight: bold;
                margin-bottom: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="arcade-card">
            <span class="energy-box">⚡ ENERGY CHARGER STATION</span>
            <div class="arcade-title">▶ ARCADE AD VAULT ◀</div>
            <p style="color: #94a3b8; font-size: 13px;">Watch 15s HD Holo-Ad to recharge:</p>
            <p style="color: #fbbf24; font-size: 16px; font-weight: bold;">+2 Gold Coins 🪙 & +20 XP 🌟</p>
            
            <button class="neon-btn" id="playBtn" onclick="playAd()">▶ START ARCADE AD</button>
        </div>
        <p id="msg" style="color: #34d399; font-weight: bold; margin-top: 20px; font-size: 14px;"></p>

        <script>
            const tg = window.Telegram.WebApp;
            tg.ready();
            tg.expand();

            const AdController = window.Adsgram.init({{ blockId: "{ADSGRAM_BLOCK_ID}" }});

            function playAd() {{
                const btn = document.getElementById('playBtn');
                btn.disabled = true;
                btn.innerText = "⏳ CHARGING BEAM...";

                AdController.show().then((result) => {{
                    document.getElementById('msg').innerText = "✅ AD COMPLETE! +2 Gold & +20 XP Injected!";
                    
                    const userId = tg.initDataUnsafe && tg.initDataUnsafe.user ? tg.initDataUnsafe.user.id : null;
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
                    btn.innerText = "▶ START ARCADE AD";
                    document.getElementById('msg').innerText = "❌ Holo-Shield Blocked! (Turn off AdBlock/DNS)";
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

    cur.execute("UPDATE users SET balance = balance + 2, xp = xp + 20, ads_watched_today = ads_watched_today + 1, last_ad_time = ? WHERE user_id = ?", (now, user_id))
    conn.commit()
    conn.close()

    try:
        await bot.send_message(chat_id=user_id, text="⚡ <b>ARCADE POWER RECHARGE!</b> +2 Gold Coins 🪙 & +20 XP 🌟", parse_mode="HTML")
    except Exception:
        pass

    return {"status": "success"}

# --- 5. BOSS QUEST COMPLETION WEBHOOK (POSTBACK) ---
@app.get("/postback")
async def secure_postback(sub1: int, task_id: str, secret: str = ""):
    if secret != POSTBACK_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")

    user_id = sub1
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("SELECT coins_reward, xp_reward FROM tasks WHERE task_id = ?", (task_id,))
    task = cur.fetchone()
    if not task:
        conn.close()
        return {"status": "error"}

    reward_coins, reward_xp = task[0], task[1]

    cur.execute("SELECT 1 FROM completed_tasks WHERE user_id = ? AND task_id = ?", (user_id, task_id))
    if cur.fetchone():
        conn.close()
        return {"status": "already_completed"}

    now = int(time.time())
    cur.execute("INSERT INTO completed_tasks (user_id, task_id, timestamp) VALUES (?, ?, ?)", (user_id, task_id, now))
    cur.execute("UPDATE users SET balance = balance + ?, xp = xp + ?, scratch_cards = scratch_cards + 1 WHERE user_id = ?", (reward_coins, reward_xp, user_id))

    cur.execute("SELECT referred_by, referral_rewarded FROM users WHERE user_id = ?", (user_id,))
    user_data = cur.fetchone()
    if user_data and user_data[0] != 0 and user_data[1] == 0:
        referrer_id = user_data[0]
        cur.execute("UPDATE users SET balance = balance + 100, xp = xp + 200 WHERE user_id = ?", (referrer_id,))
        cur.execute("UPDATE users SET referral_rewarded = 1 WHERE user_id = ?", (user_id,))
        try:
            await bot.send_message(
                chat_id=referrer_id,
                text="👑 <b>GUILD RECRUIT SUCCESS!</b> आपके रिक्रूट ने Boss Quest हराया! आपको <b>+100 Gold (₹10) & +200 XP</b> मिले!",
                parse_mode="HTML"
            )
        except Exception:
            pass

    conn.commit()
    conn.close()

    try:
        await bot.send_message(
            chat_id=user_id,
            text=f"🏆 <b>BOSS QUEST DEFEATED!</b> 🏆\n\n"
                 f"🪙 <b>+{reward_coins} Gold Coins</b>\n"
                 f"🌟 <b>+{reward_xp} XP Points</b>\n"
                 f"🎁 <b>+1 Mythic Loot Box Unlocked!</b>",
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
