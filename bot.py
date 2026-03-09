import os
import discord
from discord.ext import commands
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import signal
import sys

# Intents for voice events (no VC connect/audio needed)
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Env vars (required)
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
PUBLIC_VC_ID = int(os.getenv('PUBLIC_VC_ID', '0'))
PRIVATE_VC_ID = int(os.getenv('PRIVATE_VC_ID', '0'))

@bot.event
async def on_ready():
    print(f'{bot.user} online! Guilds: {len(bot.guilds)}')
    print(f'Public VC ID: {PUBLIC_VC_ID}, Private VC ID: {PRIVATE_VC_ID}')

@bot.event
async def on_voice_state_update(member, before, after):
    # New join to public VC only
    if after.channel and after.channel.id == PUBLIC_VC_ID and (not before.channel or before.channel.id != PUBLIC_VC_ID):
        print(f'{member} ({member.id}) joined public VC {PUBLIC_VC_ID}')
        
        private_vc = bot.get_channel(PRIVATE_VC_ID)
        if private_vc:
            privates = [m for m in private_vc.members if not m.bot and m != member]
            print(f'{len(privates)} private users found')
            
            for private_member in privates:
                try:
                    await private_member.send(f"🚨 {member.mention} joined the **public voice channel**. Please move them to private!")
                    print(f'✅ DM sent to {private_member}')
                except discord.Forbidden:
                    print(f'❌ DM blocked by {private_member}')
        else:
            print('❌ Private VC not found')

# Fake HTTP handler for Render port scan
class RenderHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Discord Bot Alive!')
    
    def log_message(self, format, *args):
        pass  # Silent logs

def run_http_server():
    port = int(os.getenv('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), RenderHandler)
    print(f'HTTP server running on port {port}')
    server.serve_forever()

def signal_handler(sig, frame):
    print('Shutting down...')
    sys.exit(0)

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print('❌ ERROR: DISCORD_TOKEN env var missing!')
        sys.exit(1)
    if PUBLIC_VC_ID == 0 or PRIVATE_VC_ID == 0:
        print('❌ ERROR: PUBLIC_VC_ID or PRIVATE_VC_ID env var missing!')
        sys.exit(1)
    
    # Graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start HTTP server (Render requires)
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    
    # Start Discord bot
    print('🚀 Starting Discord bot...')
    bot.run(DISCORD_TOKEN)
