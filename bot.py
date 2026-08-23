```python
import os
import json
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

RANKING_FILE = "ranking.json"

# ==================================================
# POŁĄCZENIE DISCORD -> NAZWA KIEROWCY W RANKINGU
# ==================================================
#
# TU WPISZEMY PÓŹNIEJ ID KAŻDEGO UŻYTKOWNIKA DISCORD
#
# PRZYKŁAD:
# "123456789012345678": "Dawid",
#

DISCORD_TO_PLAYER = {
}


intents = discord.Intents.default()
bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


def load_ranking():
    if not os.path.exists(RANKING_FILE):
        return []

    try:
        with open(
            RANKING_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)

    except Exception as error:
        print(f"Błąd odczytu rankingu: {error}")
        return []


class RankingView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="POKAŻ MOJĄ POZYCJĘ",
        emoji="🔍",
        style=discord.ButtonStyle.primary,
        custom_id="show_my_position"
    )
    async def show_my_position(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        discord_id = str(interaction.user.id)

        # Sprawdzenie, czy użytkownik jest przypisany
        if discord_id not in DISCORD_TO_PLAYER:

            await interaction.response.send_message(
                "❌ Nie mam jeszcze przypisanej Twojej nazwy "
                "z Gran Turismo do konta Discord.",
                ephemeral=True
            )

            return

        player_name = DISCORD_TO_PLAYER[discord_id]

        ranking = load_ranking()

        # Szukanie kierowcy
        player_data = None
        position = None

        for index, player in enumerate(
            ranking,
            start=1
        ):

            if player.get("username") == player_name:

                player_data = player
                position = index
                break

        # Jeśli nie znaleziono
        if not player_data:

            await interaction.response.send_message(
                f"❌ Nie znaleziono kierowcy **{player_name}** "
                "w aktualnym rankingu.",
                ephemeral=True
            )

            return

        # Medale
        if position == 1:
            medal = "🥇"

        elif position == 2:
            medal = "🥈"

        elif position == 3:
            medal = "🥉"

        else:
            medal = "🏁"

        # Prywatna odpowiedź
        message = (
            "🏁 **TWOJA POZYCJA W RANKINGU**\n\n"
            f"{medal} **Pozycja: {position}**\n"
            f"👤 Kierowca: **{player_data['username']}**\n"
            f"🏅 PK: **{player_data['pk']}**\n"
            f"🏁 PFK: **{player_data['pfk']}**\n"
            f"📊 Edge Score: "
            f"**{player_data['score']:.2f}**"
        )

        await interaction.response.send_message(
            message,
            ephemeral=True
        )


@bot.event
async def on_ready():

    bot.add_view(
        RankingView()
    )

    print(
        f"Bot zalogowany jako {bot.user}"
    )


@bot.command()
async def rankingbutton(ctx):

    await ctx.send(
        "🔍 Kliknij przycisk, aby sprawdzić "
        "swoją aktualną pozycję w rankingu.",
        view=RankingView()
    )


@bot.command()
async def test(ctx):

    await ctx.send(
        "🏁 SRS Ranking Bot działa!"
    )


bot.run(TOKEN)
```
