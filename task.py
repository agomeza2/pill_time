import asyncio
import sqlite3
import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

import discord
from discord.ext import commands
from config import DISCORD_TOKEN, DISCORD_USER_ID

# --- bot configuration---
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

DB_PATH = "data.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS medi_data (
            date TEXT,
            pill_taken INTEGER,
            blood_pressure REAL
        )
    ''')
    conn.commit()
    conn.close()

def save_db(date, pill_taken=None, blood_pressure=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO medi_data (date,pill_taken,blood_pressure) VALUES (?, ?, ?)", (date, pill_taken, blood_pressure))
    conn.commit()
    conn.close()

# --- DMs ---
async def send_message_pill():
    user = await bot.fetch_user(DISCORD_USER_ID)
    await user.send("Did you take your pills?")
    
    def check(msg):
        return msg.author.id == DISCORD_USER_ID and isinstance(msg.channel, discord.DMChannel)
    
    try:
        await bot.wait_for('message', check=check, timeout=5*60*60)
        save_db(datetime.date.today().isoformat(), pill_taken=1)
        await user.send("record registered")
    except asyncio.TimeoutError:
        await user.send("didn't register your if you take your pill, will tell tomorrow")
        save_db(datetime.date.today().isoformat(), pill_taken=0)

async def send_message_bp():
    user = await bot.fetch_user(DISCORD_USER_ID)
    await user.send("what is your blood pressure?")

    def check(msg):
        return msg.author.id == DISCORD_USER_ID and isinstance(msg.channel, discord.DMChannel)

    try:
        while True:
            msg = await bot.wait_for('message', check=check, timeout=5*60*60)
            try:
                pressure = float(msg.content)
                save_db(datetime.date.today().isoformat(), blood_pressure=pressure)
                await user.send(f"Blood Pressure: {pressure}")
                break
            except ValueError:
                await user.send("Not a valid number")
    except asyncio.TimeoutError:
        await user.send("didn't register your pressure today. will remember to you tomorrow")

# --- Scheduler ---
scheduler = AsyncIOScheduler()

scheduler.add_job(send_message_pill, CronTrigger(hour=8, minute=0))
scheduler.add_job(send_message_pill, CronTrigger(hour=21, minute=0))

scheduler.add_job(send_message_bp, CronTrigger(hour=8, minute=30))
scheduler.add_job(send_message_bp, CronTrigger(hour=21, minute=30))


# --- Init event ---
@bot.event
async def on_ready():
    user = await bot.fetch_user(DISCORD_USER_ID)
    await user.send("Bot started. Will send message at assing hours")
    print(f"Bot connected as {bot.user}")
    scheduler.start()

# --- Main ---
if __name__ == "__main__":
    init_db()
    bot.run(DISCORD_TOKEN)
