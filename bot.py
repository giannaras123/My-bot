import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
import requests
from keep_alive import keep_alive
import datetime

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
GUILD_ID = 1090287511525412944  # Replace with your actual server ID
VERIFY_CHANNEL_ID = 1378297006140948560
PLAYER_ROLE_NAME = "Player"
PINNED_FILE_NAME = "UsersList.txt"

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Error syncing commands: {e}")
    verify_loop.start()

# --- Verification System ---
@tasks.loop(minutes=2)
async def verify_loop():
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return

    channel = guild.get_channel(VERIFY_CHANNEL_ID)
    if not channel:
        return

    pinned = await channel.pins()
    userlist_msg = next((msg for msg in pinned if msg.attachments), None)

    if not userlist_msg:
        return

    attachment = userlist_msg.attachments[0]
    content = await attachment.read()
    userlist = content.decode().splitlines()

    async for message in channel.history(limit=20):
        if message.author.bot:
            continue

        nickname = message.content.strip()
        member = guild.get_member(message.author.id)

        if not member:
            continue

        already_used = any(m.nick == nickname for m in guild.members if m.nick and m.id != member.id)

        if nickname in userlist and not already_used:
            try:
                await member.edit(nick=nickname)
                role = discord.utils.get(guild.roles, name=PLAYER_ROLE_NAME)
                if role:
                    await member.add_roles(role)
            except Exception as e:
                print(f"Failed to verify user {member.name}: {e}")

# --- Commands ---

@bot.tree.command(name="serverinfo", description="Shows info about the server")
async def serverinfo(interaction: discord.Interaction):
    guild = interaction.guild
    total = guild.member_count
    online = sum(1 for m in guild.members if m.status != discord.Status.offline)
    bots = sum(1 for m in guild.members if m.bot)

    embed = discord.Embed(title="Server Info", color=discord.Color.blurple())
    embed.add_field(name="Total Members", value=str(total))
    embed.add_field(name="Online Members", value=str(online))
    embed.add_field(name="Bots", value=str(bots))
    embed.add_field(
        name="About",
        value="Protanki Enjoyers is an open server created by **unkown**, you can invite your friends (if you want).",
        inline=False
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="hello", description="Say hello")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello, {interaction.user.mention}!")

@bot.tree.command(name="say", description="Bot repeats your message (admin only)")
@app_commands.describe(text="The message to send")
async def say(interaction: discord.Interaction, text: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You don't have permission to use this.", ephemeral=True)
        return
    await interaction.response.send_message("Sent.", ephemeral=True)
    await interaction.channel.send(text)

@bot.tree.command(name="react", description="Bot adds a reaction to a message (admin only)")
@app_commands.describe(message_id="ID of the message", emoji="Emoji to react with")
async def react(interaction: discord.Interaction, message_id: str, emoji: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You don't have permission to use this.", ephemeral=True)
        return
    try:
        msg = await interaction.channel.fetch_message(int(message_id))
        await msg.add_reaction(emoji)
        await interaction.response.send_message("Reaction added.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error: {e}", ephemeral=True)

@bot.tree.command(name="avatar", description="Shows the avatar of a user.")
@app_commands.describe(user="Select a user to view their avatar.")
async def avatar(interaction: discord.Interaction, user: discord.User):
    embed = discord.Embed(
        title=f"{user.name}'s Avatar",
        color=discord.Color.purple()
    )
    embed.set_image(url=user.display_avatar.url)
    await interaction.response.send_message(embed=embed)

# --- Keep Alive ---
keep_alive()

# --- Bot Token ---
bot.run(os.getenv("TOKEN"))




