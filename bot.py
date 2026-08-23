import os
import json
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Powiązanie nazwy użytkownika Discord
# z nazwą kierowcy w rankingu
DISCORD_PLAYERS = {
    "dawidy6q": "SRS Dawid-y6q"
}


intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


def load_ranking():

    if not os.path.exists("ranking.json"):
        return []

    with open(
        "ranking.json",
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


@bot.event
async def on_ready():

    print(
        f"Bot zalogowany jako {bot.user}"
    )


@bot.command()
async def pozycja(ctx):

    discord_username = ctx.author.name.lower()

    # Sprawdzenie, czy użytkownik
    # jest przypisany do kierowcy
    if discord_username not in DISCORD_PLAYERS:

        await ctx.send(
            "❌ Nie mam jeszcze przypisanego "
            "kierowcy do Twojego konta Discord."
        )

        return

    player_name = DISCORD_PLAYERS[
        discord_username
    ]

    ranking = load_ranking()

    if not ranking:

        await ctx.send(
            "❌ Nie znaleziono aktualnego rankingu."
        )

        return

    # Szukanie kierowcy w rankingu
    for position, player in enumerate(
        ranking,
        start=1
    ):

        if player["username"] == player_name:

            await ctx.send(
                f"🏁 **{player_name}**\n\n"
                f"📈 Twoja pozycja: "
                f"**{position}. miejsce**\n"
                f"🏅 PK: **{player['pk']}**\n"
                f"🏆 PFK: **{player['pfk']}**\n"
                f"📊 Edge Score: "
                f"**{player['score']:.2f}**"
            )

            return

    await ctx.send(
        "❌ Nie znalazłem Cię "
        "w aktualnym rankingu."
    )


bot.run(TOKEN)
