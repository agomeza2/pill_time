import discord
import luigi
import asyncio
import sqlite3
from datetime import datetime, timedelta
from config import DISCORD_TOKEN, DISCORD_USER_ID

DB_FILE = "data.db"

# Table medi_data
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS medi_data (
            date TEXT PRIMARY KEY,
            pill_taken INTEGER,
            blood_pressure REAL
        )
    ''')
    conn.commit()
    conn.close()

# Save to db 
def save_to_db(date, medicamento, presion):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO medi_data (date, pill_taken,blood_pressure) VALUES (?, ?, ?)",
              (date, medicamento, presion))
    conn.commit()
    conn.close()

# Luigi schedule
class BaseNotification(luigi.Task):
    hour = luigi.Parameter()
    type = luigi.Parameter()  # 'morning' o 'evening'

    def output(self):
        return luigi.LocalTarget(f".notified_{self.hour}_{self.type}.txt")

    async def send_message(self):
        client = discord.Client(intents=discord.Intents.default())

        @client.event
        async def on_ready():
            print(f"✅ Servicio iniciado: Notificaciones en {self.hour} ({self.type})")
            user = await client.fetch_user(DISCORD_USER_ID)
            now = datetime.now()
            actual_date = now.strftime("%Y-%m-%d %H:%M")

            try:
                # step 1, do you take your pill
                await user.send(f"Pill Taken in ({self.type})?")
                def check_pill(m):
                    return m.author.id == DISCORD_USER_ID and isinstance(m.channel, discord.DMChannel)
                try:
                    msg1 = await client.wait_for('message', timeout=60*60*5, check=check_pill)
                    pill = 1 if msg1.content.lower() in ['si', 'sí', 's', 'yes', '1'] else 0
                except asyncio.TimeoutError:
                    await user.send("Didn't answer, i will remember to you tomorrow")
                    await client.close()
                    return

                # Paso 2: Preguntar por presión
                while True:
                    await user.send(f" Blood pressure in ({self.type})?")
                    def check_presion(m):
                        return m.author.id == DISCORD_USER_ID and isinstance(m.channel, discord.DMChannel)
                    try:
                        msg2 = await client.wait_for('message', timeout=60*60*5, check=check_presion)
                        try:
                            bp = float(msg2.content)
                            break
                        except ValueError:
                            await user.send("not a valid number")
                    except asyncio.TimeoutError:
                        await user.send("Didn't answer, i will remember to you tomorrow")
                        await client.close()
                        return

                # Guardar en base de datos
                save_to_db(now.strftime("%Y-%m-%d %H:%M"), pill, bp)
                await user.send("record saved. Thank you")

            except Exception as e:
                print(f"Error at message sending: {e}")
            finally:
                await client.close()

        await client.start(DISCORD_TOKEN)

    def run(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.send_message())
        with self.output().open('w') as f:
            f.write(f"Notified at {self.hour} ({self.type})")

# Tareas programadas (puedes ampliar con más horarios)
class NotifyMorning(BaseNotification):
    hour = "08:00"
    type = "morning"

class NotifyEvening(BaseNotification):
    hour = "21:00"
    type = "evening"

# Entry point
if __name__ == "__main__":
    init_db()
    luigi.build([
        NotifyMorning(),
        NotifyEvening()
    ], local_scheduler=True)
