import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

PLAYERS = [
    "SolidSnakePoland",
    "ALF7",
    "lucekbks",
    "MTE_JaXoN_GT",
    "Przemo7117"
]

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")


def get_player(psn_id):
    url = "https://gtstats.live/"

    response = requests.get(
        url,
        params={"psn": psn_id},
        timeout=20
    )

    soup = BeautifulSoup(response.text, "html.parser")

    # Na tym etapie sprawdzimy dokładny format danych
    # pobieranych z profilu GTStats.
    text = soup.get_text(" ", strip=True)

    return {
        "psn": psn_id,
        "data": text
    }


def main():
    ranking = []

    for player in PLAYERS:
        try:
            data = get_player(player)
            ranking.append(data)
        except Exception as e:
            print(f"Błąd dla {player}: {e}")

    message = "🏆 **SRS DRIVER RANKING**\n\n"

    for i, player in enumerate(ranking, start=1):
        message += f"**{i}. {player['psn']}**\n"

    message += (
        "\n━━━━━━━━━━━━━━\n"
        f"🔄 **Aktualizacja:** "
        f"{datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

    if WEBHOOK_URL:
        requests.post(
            WEBHOOK_URL,
            json={"content": message},
            timeout=20
        )


if __name__ == "__main__":
    main()
