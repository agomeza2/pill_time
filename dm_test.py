import discord
from config import DISCORD_TOKEN, DISCORD_USER_ID

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print("Bot conectado. Enviando mensaje...")
    user = await client.fetch_user(DISCORD_USER_ID)
    await user.send("Hola, este es un mensaje directo del bot.")
    await client.close()

client.run(DISCORD_TOKEN)
