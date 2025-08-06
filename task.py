import asyncio
import sqlite3
import datetime
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

import discord
from discord.ext import commands
from config import DISCORD_TOKEN, DISCORD_USER_ID

# --- Configuración del bot ---
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Base de datos ---
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

# --- Guardar en base de datos ---
def save_db(date, pill_taken=None, blood_pressure=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO medi_data (date,pill_taken,blood_pressure) VALUES (?, ?, ?)", (date, pill_taken, blood_pressure))
    conn.commit()
    conn.close()

# --- Funciones de interacción por DM ---
async def send_message_pill():
    user = await bot.fetch_user(DISCORD_USER_ID)
    await user.send("Did you take your pills?")
    
    def check(msg):
        return msg.author.id == DISCORD_USER_ID and isinstance(msg.channel, discord.DMChannel)
    
    try:
        msg = await bot.wait_for('message', check=check, timeout=5*60*60)
        guardar_en_db(datetime.date.today().isoformat(), medicamento=1)
        await user.send("✅ Medicamento registrado.")
    except asyncio.TimeoutError:
        await user.send("⚠️ No registraste tu medicamento hoy. Te lo recordaré mañana.")
        guardar_en_db(datetime.date.today().isoformat(), medicamento=0)

async def send_message_bp():
    user = await bot.fetch_user(DISCORD_USER_ID)
    await user.send("🩺 Por favor ingresa tu medida de presión arterial como un número (ej. 120.5).")

    def check(msg):
        return msg.author.id == DISCORD_USER_ID and isinstance(msg.channel, discord.DMChannel)

    try:
        while True:
            msg = await bot.wait_for('message', check=check, timeout=5*60*60)
            try:
                presion = float(msg.content)
                guardar_en_db(datetime.date.today().isoformat(), presion=presion)
                await user.send(f"✅ Presión registrada: {presion}")
                break
            except ValueError:
                await user.send("❌ Por favor ingresa un número válido (ej. 120.5)")
    except asyncio.TimeoutError:
        await user.send("⚠️ No registraste tu presión hoy. Te lo recordaré mañana.")

# --- Scheduler ---
scheduler = AsyncIOScheduler()

# Dos veces al día para medicamento (8:00 AM y 9:00 PM)
scheduler.add_job(lambda: asyncio.create_task(enviar_recordatorio_med()), CronTrigger(hour=8, minute=0))
scheduler.add_job(lambda: asyncio.create_task(enviar_recordatorio_med()), CronTrigger(hour=21, minute=0))

# Dos veces al día para presión arterial (8:30 AM y 9:30 PM)
scheduler.add_job(lambda: asyncio.create_task(enviar_recordatorio_presion()), CronTrigger(hour=8, minute=30))
scheduler.add_job(lambda: asyncio.create_task(enviar_recordatorio_presion()), CronTrigger(hour=21, minute=30))

# --- Evento al iniciar ---
@bot.event
async def on_ready():
    user = await bot.fetch_user(DISCORD_USER_ID)
    await user.send("✅ Bot iniciado. Te enviaré notificaciones a las horas programadas.")
    print(f"Bot conectado como {bot.user}")
    scheduler.start()

# --- Main ---
if __name__ == "__main__":
    init_db()
    bot.run(DISCORD_TOKEN)
