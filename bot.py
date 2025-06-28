import discord
from discord.ext import commands
from discord import app_commands
import requests
import asyncio
import os
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.messages = True
intents.message_content = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)

GUILD_ID = YOUR_GUILD_ID_HERE  # Replace with your server's guild ID
VERIFICATION_CHANNEL_ID = YOUR_CHANNEL_ID_HERE  # Replace with your verification channel ID

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"Synced {len(synced)} command(s).")
    except Exception as e:
        print(e)

# /hello
@bot.tree.command(name="hello", description="Say hello", guild=discord.Object(id=GUILD_ID))
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello, {interaction.user.name}!")

# /say (admin only)
@bot.tree.command(name="say", description="Make the bot say something", guild=discord.Object(id=GUILD_ID))
@app_commands.checks.has_permissions(administrator=True)
async def say(interaction: discord.Interaction, message: str):
    await interaction.response.send_message(f"✅ Sent!", ephemeral=True)
    await interaction.channel.send(message)

# /react (admin only)
@bot.tree.command(name="react", description="Bot adds a reaction to a message", guild=discord.Object(id=GUILD_ID))
@app_commands.checks.has_permissions(administrator=True)
async def react(interaction: discord.Interaction, message_id: str, emoji: str):
    try:
        msg = await interaction.channel.fetch_message(int(message_id))
        await msg.add_reaction(emoji)
        await interaction.response.send_message("✅ Reaction added!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed: {e}", ephemeral=True)

# /serverinfo
@bot.tree.command(name="serverinfo", description="Shows info about the server", guild=discord.Object(id=GUILD_ID))
async def serverinfo(interaction: discord.Interaction):
    guild = interaction.guild
    total_members = guild.member_count
    bots = len([m for m in guild.members if m.bot])
    online = len([m for m in guild.members if m.status != discord.Status.offline])

    embed = discord.Embed(title="Server Info", color=discord.Color.blue())
    embed.add_field(name="Total Members", value=total_members, inline=True)
    embed.add_field(name="Online Members", value=online, inline=True)
    embed.add_field(name="Bots", value=bots, inline=True)
    embed.add_field(name="Info", value="Protanki Enjoyers is an open server created by **unkown**, you can invite your friends (if you want).", inline=False)
    await interaction.response.send_message(embed=embed)

# /avatar
@bot.tree.command(name="avatar", description="Get user's avatar", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="Select a user")
async def avatar(interaction: discord.Interaction, user: discord.Member):
    embed = discord.Embed(title=f"{user.name}'s Avatar")
    embed.set_image(url=user.display_avatar.url)
    await interaction.response.send_message(embed=embed)

# Verification system
@bot.event
async def on_member_join(member):
    await asyncio.sleep(1)  # Delay to let Discord register member join
    channel = member.guild.get_channel(VERIFICATION_CHANNEL_ID)
    if not channel:
        return

    try:
        messages = [msg async for msg in channel.history(limit=10) if msg.author == member]
        if messages:
            last_msg = messages[0].content.strip()
            file_msg = await channel.fetch_message(channel.last_message_id)
            if file_msg and file_msg.attachments:
                file_url = file_msg.attachments[0].url
                response = requests.get(file_url)
                if response.status_code == 200:
                    lines = response.text.splitlines()
                    for line in lines:
                        parts = line.split("=")
                        if len(parts) == 2 and parts[1].strip() == last_msg:
                            await member.edit(nick=parts[0].strip())
                            break
    except Exception as e:
        print(f"Verification error: {e}")

keep_alive()
bot.run(os.getenv("TOKEN"))
