import discord
from discord.ext import commands
from discord import app_commands
import datetime
import discord.utils

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

VERIFICATION_CHANNEL_ID = 1378297006140948560
PLAYER_ROLE_NAME = "Player"
USERS_LIST = []

@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")
    try:
        channel = bot.get_channel(VERIFICATION_CHANNEL_ID)
        if channel:
            pinned = await channel.pins()
            for message in pinned:
                for attachment in message.attachments:
                    if attachment.filename == "UsersList.txt":
                        content = await attachment.read()
                        global USERS_LIST
                        USERS_LIST = content.decode("utf-8").splitlines()
                        print(f"✅ Loaded {len(USERS_LIST)} users from UsersList.txt")
        else:
            print("❌ Verification channel not found.")
    except Exception as e:
        print(f"❌ Failed to load UsersList.txt: {e}")

    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"❌ Slash command sync failed: {e}")

@bot.event
async def on_member_join(member):
    await verify_new_member(member)

async def verify_new_member(member):
    guild = member.guild
    channel = guild.get_channel(VERIFICATION_CHANNEL_ID)
    if not channel:
        print("❌ Verification channel missing")
        return

    try:
        messages = []
        async for m in channel.history(limit=100):
            # Only messages from user sent at or after join time
            if m.author.id == member.id and m.created_at >= member.joined_at:
                messages.append(m)

        if not messages:
            print(f"ℹ No messages from {member.display_name} after joining")
            return

        latest_message = max(messages, key=lambda m: m.created_at)
        nickname = latest_message.content.strip()

        if nickname not in USERS_LIST:
            print(f"❌ {nickname} not in UsersList.txt")
            return

        # Check if nickname already used
        for m in guild.members:
            if m.nick == nickname or m.name == nickname:
                print(f"❌ Nickname {nickname} already in use")
                return

        await member.edit(nick=nickname)
        role = discord.utils.get(guild.roles, name=PLAYER_ROLE_NAME)
        if role:
            await member.add_roles(role)
        print(f"✅ {member} verified as {nickname}")

    except Exception as e:
        print(f"❌ Verification error: {e}")

@bot.tree.command(name="hello", description="Say hello")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello, {interaction.user.mention}!", ephemeral=True)

@bot.tree.command(name="serverinfo", description="Show info about the server")
async def serverinfo(interaction: discord.Interaction):
    guild = interaction.guild
    bots = len([m for m in guild.members if m.bot])
    online = len([m for m in guild.members if m.status != discord.Status.offline])
    embed = discord.Embed(
        title=guild.name,
        description="Protanki Enjoyers is an open server created by **unkown**, you can invite your friends (if you want).",
        color=discord.Color.green()
    )
    embed.add_field(name="Total Members", value=guild.member_count)
    embed.add_field(name="Online Members", value=online)
    embed.add_field(name="Bots", value=bots)
    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="say", description="Make the bot say something (admin only)")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(message="The message to say")
async def say(interaction: discord.Interaction, message: str):
    await interaction.response.send_message("✅ Sent!", ephemeral=True)
    await interaction.channel.send(message)

@bot.tree.command(name="react", description="Make the bot react to a message (admin only)")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(message_id="ID of the message", emoji="Emoji to react with")
async def react(interaction: discord.Interaction, message_id: str, emoji: str):
    try:
        msg = await interaction.channel.fetch_message(int(message_id))
        await msg.add_reaction(emoji)
        await interaction.response.send_message("✅ Reaction added.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed: {e}", ephemeral=True)

@bot.tree.command(name="avatar", description="Show someone's avatar")
@app_commands.describe(user="The user to show avatar of")
async def avatar(interaction: discord.Interaction, user: discord.User):
    embed = discord.Embed(title=f"{user.name}'s Avatar")
    embed.set_image(url=user.display_avatar.url)
    await interaction.response.send_message(embed=embed)

@hello.error
@say.error
@react.error
@avatar.error
async def command_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ Error: {str(error)}", ephemeral=True)

# Keep Alive
import keep_alive  # your keep_alive.py for uptime robot
keep_alive.keep_alive()

import os
bot.run(os.getenv("TOKEN"))
