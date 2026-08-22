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

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def get_player(psn):
    url = f"https://www.dg-edge.com/players/{psn}"

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(" ", strip=True)

    return {
        "psn": psn,
        "text": text
    }


def main():
    message = "🏆 **SRS DRIVER RANKING**\n\n"

    for player in PLAYERS:
        try:
            data = get_player(player)

            # Na razie testujemy pobieranie profili
            message += f"👤 **{data['psn']}** — profil znaleziony\n"

            print(f"\n===== {player} =====")
            print(data["text"][:3000])

        except Exception as error:
            message += f"❌ **{player}** — profil nie znaleziony\n"
            print(f"BŁĄD {player}: {error}")

    message += (
        "\n━━━━━━━━━━━━━━━━━━━━\n"
        f"🔄 **Test:** {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

    requests.post(
        WEBHOOK_URL,
        json={"content": message},
        timeout=30
    )


if __name__ == "__main__":
    main()
