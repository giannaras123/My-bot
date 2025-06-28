import discord
from discord.ext import commands
import os
import requests
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.environ.get("TOKEN")
GUILD_ID = 1090287511525412944
VERIFICATION_CHANNEL_ID = 1378297006140948560
PINNED_FILE_NAME = "UsersList.txt"
PLAYER_ROLE_NAME = "Player"

valid_usernames = set()

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user}')
    await load_users_list()

async def load_users_list():
    """Loads the pinned UsersList.txt from the verification channel."""
    channel = bot.get_channel(VERIFICATION_CHANNEL_ID)
    if not channel:
        print("❌ Could not find verification channel.")
        return

    pins = await channel.pins()
    for message in pins:
        for attachment in message.attachments:
            if attachment.filename == PINNED_FILE_NAME:
                content = await attachment.read()
                decoded = content.decode("utf-8")
                global valid_usernames
                valid_usernames = set(line.strip() for line in decoded.splitlines() if line.strip())
                print(f"✅ Loaded {len(valid_usernames)} valid usernames.")
                return
    print("❌ UsersList.txt not found in pinned messages.")

@bot.event
async def on_member_join(member):
    if member.guild.id != GUILD_ID:
        return

    print(f"👤 {member} joined. Waiting for verification...")

    await asyncio.sleep(1)

    def check(msg):
        return (
            msg.channel.id == VERIFICATION_CHANNEL_ID and
            msg.author.id == member.id
        )

    try:
        msg = await bot.wait_for("message", check=check, timeout=300)
        nickname = msg.content.strip()

        if nickname not in valid_usernames:
            print(f"❌ Invalid nickname: {nickname}")
            return

        guild = bot.get_guild(GUILD_ID)
        for m in guild.members:
            if m.nick == nickname and m.id != member.id:
                print(f"❌ Nickname '{nickname}' already taken by another user.")
                return

        await member.edit(nick=nickname)
        role = discord.utils.get(guild.roles, name=PLAYER_ROLE_NAME)
        if role:
            await member.add_roles(role)
        print(f"✅ {member.name} verified as '{nickname}'")

    except asyncio.TimeoutError:
        print(f"⌛ {member.name} did not send message in time.")

@bot.slash_command(name="hello", description="Say hello")
async def hello(ctx):
    await ctx.respond(f"Hello {ctx.author.mention}!")

bot.run(TOKEN)
