import os
import json
import asyncio
import threading

import discord
from discord.ext import commands

from flask import Flask, request, jsonify
from flask_cors import CORS


TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# ID kanału Discord, na który ma przychodzić wynik
CHANNEL_ID = 1511120399230832772


DISCORD_PLAYERS = {
    "dawidy6q": "SRS Dawid-y6q"
}


intents = discord.Intents.default()
intents.message_content = True


bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


app = Flask(__name__)

# Pozwala stronie GitHub Pages wysyłać dane
CORS(app)


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


@app.route("/losowanie", methods=["POST"])
def losowanie():

    data = request.get_json()

    if not data or "track" not in data:
        return jsonify({
            "success": False,
            "error": "Brak nazwy toru"
        }), 400

    track = data["track"]

    print(
        f"Otrzymano losowanie toru: {track}"
    )

    channel = bot.get_channel(CHANNEL_ID)

    if channel is None:
        return jsonify({
            "success": False,
            "error": "Nie znaleziono kanału Discord"
        }), 500

    message = (
        "🏁 **SRS LOSOWANIE TORU**\n\n"
        "🎲 Wylosowany tor:\n"
        f"🏆 **{track}**\n\n"
        "🔥 Powodzenia na torze!"
    )

    future = asyncio.run_coroutine_threadsafe(
        channel.send(message),
        bot.loop
    )

    try:
        future.result(timeout=10)

        return jsonify({
            "success": True
        })

    except Exception as error:

        print(
            f"Błąd wysyłania: {error}"
        )

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


@bot.event
async def on_ready():

    print(
        f"Bot zalogowany jako {bot.user}"
    )


@bot.event
async def on_message(message):

    if message.author.bot:
        return

    print(
        f"Otrzymano wiadomość: "
        f"{message.author.name} -> "
        f"{message.content}"
    )

    await bot.process_commands(message)


@bot.command()
async def pozycja(ctx):

    discord_username = ctx.author.name.lower()

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
            "❌ Nie znaleziono "
            "pliku ranking.json."
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


def run_flask():

    app.run(
        host="0.0.0.0",
        port=5000
    )


if __name__ == "__main__":

    flask_thread = threading.Thread(
        target=run_flask
    )

    flask_thread.daemon = True

    flask_thread.start()

    bot.run(TOKEN)
