import os
import json
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Połączenie konta Discord z kierowcą w rankingu
DISCORD_PLAYERS = {
    "dawidy6q": "SRS Dawid-y6q"
}

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


def load_ranking():
    if not os.path.exists("ranking.json"):
        print("Nie znaleziono pliku ranking.json")
        return []

    with open(
        "ranking.json",
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


@bot.event
async def on_ready():
    print(f"Bot zalogowany jako {bot.user}")


@bot.event
async def on_message(message):

    # Bot nie odpowiada sam sobie
    if message.author.bot:
        return

    print(
        f"Otrzymano wiadomość: "
        f"{message.author.name} -> {message.content}"
    )

    await bot.process_commands(message)


@bot.command()
async def pozycja(ctx):

    discord_username = ctx.author.name.lower()

    print(
        f"Sprawdzam użytkownika: "
        f"{discord_username}"
    )

    if discord_username not in DISCORD_PLAYERS:
        await ctx.send(
            "❌ Nie mam przypisanego kierowcy "
            "do Twojego konta Discord."
        )
        return

    player_name = DISCORD_PLAYERS[
        discord_username
    ]

    ranking = load_ranking()

    if not ranking:
        await ctx.send(
            "❌ Nie znaleziono pliku ranking.json."
        )
        return

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
