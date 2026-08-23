import os
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


@bot.event
async def on_ready():
    print(
        f"Bot zalogowany jako {bot.user}"
    )


@bot.command()
async def test(ctx):
    await ctx.send(
        "🏁 SRS Ranking Bot działa!"
    )


bot.run(TOKEN)
