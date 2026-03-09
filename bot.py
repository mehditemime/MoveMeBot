import os
import sys
import signal
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
PUBLIC_VC_ID = int(os.getenv("PUBLIC_VC_ID", "0"))
PRIVATE_VC_ID = int(os.getenv("PRIVATE_VC_ID", "0"))

# Stores when each user joined the public VC
public_join_times = {}


def format_duration(seconds: int) -> str:
    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{sec}s")

    return " ".join(parts)


async def notify_private_vc_members(message: str, exclude_member_id=None):
    private_vc = bot.get_channel(PRIVATE_VC_ID)

    if private_vc is None:
        print("Private VC not found.")
        return

    recipients = [
        m for m in private_vc.members
        if not m.bot and m.id != exclude_member_id
    ]

    print(f"Found {len(recipients)} member(s) in private VC to notify.")

    for private_member in recipients:
        try:
            await private_member.send(message)
            print(f"DM sent to {private_member} ({private_member.id})")
        except discord.Forbidden:
            print(f"DM blocked for {private_member} ({private_member.id})")
        except Exception as e:
            print(f"Failed to DM {private_member} ({private_member.id}): {e}")


@bot.event
async def on_ready():
    print(f"{bot.user} is online.")
    print(f"Guild count: {len(bot.guilds)}")
    print(f"PUBLIC_VC_ID = {PUBLIC_VC_ID}")
    print(f"PRIVATE_VC_ID = {PRIVATE_VC_ID}")


@bot.event
async def on_voice_state_update(member, before, after):
    before_channel = before.channel
    after_channel = after.channel

    # 1) User joins the public VC
    if (
        after_channel is not None
        and after_channel.id == PUBLIC_VC_ID
        and (before_channel is None or before_channel.id != PUBLIC_VC_ID)
    ):
        public_join_times[member.id] = datetime.utcnow()
        print(f"{member} joined public VC at {public_join_times[member.id]}")

        join_message = (
            f"🚨 {member.mention} joined the public voice channel.\n"
            f"Please move them to the private channel if needed."
        )
        await notify_private_vc_members(join_message, exclude_member_id=member.id)
        return

    # 2) User leaves or is moved out of the public VC
    if (
        before_channel is not None
        and before_channel.id == PUBLIC_VC_ID
        and (after_channel is None or after_channel.id != PUBLIC_VC_ID)
    ):
        join_time = public_join_times.pop(member.id, None)

        if join_time is not None:
            seconds_spent = int((datetime.utcnow() - join_time).total_seconds())
            duration_text = format_duration(seconds_spent)
        else:
            duration_text = "an unknown amount of time"

        if after_channel is None:
            exit_reason = "left the public voice channel"
        else:
            exit_reason = f"was moved from the public voice channel to **{after_channel.name}**"

        leave_message = (
            f"ℹ️ {member.mention} {exit_reason}.\n"
            f"Time spent in public VC: **{duration_text}**."
        )
        print(f"{member} left public VC after {duration_text}")

        await notify_private_vc_members(leave_message, exclude_member_id=member.id)
        return


class RenderHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Discord bot is alive")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        return


def run_web_server():
    port = int(os.getenv("PORT", "10000"))
    server = HTTPServer(("0.0.0.0", port), RenderHandler)
    print(f"Web server running on port {port}")
    server.serve_forever()


def shutdown_handler(signum, frame):
    print("Shutting down...")
    sys.exit(0)


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("ERROR: DISCORD_TOKEN is missing.")
        sys.exit(1)

    if PUBLIC_VC_ID == 0 or PRIVATE_VC_ID == 0:
        print("ERROR: PUBLIC_VC_ID or PRIVATE_VC_ID is missing.")
        sys.exit(1)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()

    print("Starting Discord bot...")
    bot.run(DISCORD_TOKEN)
