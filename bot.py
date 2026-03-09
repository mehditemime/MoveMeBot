import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
#intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

PUBLIC_VC_ID = int(os.getenv('PUBLIC_VC_ID', '0'))  # Env var or 0
PRIVATE_VC_ID = int(os.getenv('PRIVATE_VC_ID', '0'))  # Env var or 0

@bot.event
async def on_ready():
    print(f'{bot.user} online in {len(bot.guilds)} guilds!')

@bot.event
async def on_voice_state_update(member, before, after):
    if after.channel and after.channel.id == PUBLIC_VC_ID and (not before.channel or before.channel.id != PUBLIC_VC_ID):
        private_vc = bot.get_channel(PRIVATE_VC_ID)
        if private_vc:
            privates = [m for m in private_vc.members if not m.bot and member != m]
            for private_member in privates:
                try:
                    await private_member.send(f"{member.mention} joined public VC. Move to private?")
                    print(f"DM sent to {private_member}")
                except discord.Forbidden:
                    print(f"DM failed for {private_member}")

if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("ERROR: DISCORD_TOKEN env var missing!")
        exit(1)
    bot.run(token)
