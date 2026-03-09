import os
import discord
from discord.ext import commands

# Intents - voice_states for events ONLY (no audio/VC connect needed) [web:41]
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True  # REQUIRED for on_voice_state_update [web:201]

bot = commands.Bot(command_prefix='!', intents=intents)

# Env vars from Render (fallback 0 for safety)
PUBLIC_VC_ID = int(os.getenv('PUBLIC_VC_ID', '0'))
PRIVATE_VC_ID = int(os.getenv('PRIVATE_VC_ID', '0'))

@bot.event
async def on_ready():
    print(f'{bot.user} online! Guilds: {len(bot.guilds)}')
    if PUBLIC_VC_ID == 0 or PRIVATE_VC_ID == 0:
        print('WARNING: Set PUBLIC_VC_ID & PRIVATE_VC_ID env vars!')
    print(f'Public VC: {PUBLIC_VC_ID}, Private VC: {PRIVATE_VC_ID}')

@bot.event
async def on_voice_state_update(member, before, after):
    # Safety: Skip if no after.channel or not new join [web:201]
    if not after.channel or before.channel == after.channel:
        return
    
    print(f'{member} joined {after.channel.id}')  # Debug log
    
    if after.channel.id == PUBLIC_VC_ID:
        private_vc = bot.get_channel(PRIVATE_VC_ID)
        if private_vc:
            privates = [m for m in private_vc.members if not m.bot and m != member]
            print(f'Found {len(privates)} private users')
            for private_member in privates:
                try:
                    await private_member.send(f"{member.mention} joined public VC. Move to private?")
                    print(f"DM sent to {private_member}")
                except discord.Forbidden:
                    print(f"DM blocked by {private_member}")
        else:
            print('Private VC not found')

if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print('ERROR: DISCORD_TOKEN missing!')
        exit(1)
    if PUBLIC_VC_ID == 0 or PRIVATE_VC_ID == 0:
        print('ERROR: PUBLIC_VC_ID or PRIVATE_VC_ID missing!')
        exit(1)
    print('Starting bot...')
    bot.run(token)
