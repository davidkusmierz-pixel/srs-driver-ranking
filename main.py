import os
import requests
from bs4 import BeautifulSoup

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

message = "🏆 **SRS DRIVER RANKING**\n\n"

for player in PLAYERS:
    try:
        response = requests.get(
            "https://gtstats.live/",
            params={"psn": player},
            headers=HEADERS,
            timeout=30
        )

        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        message += f"👤 **{player}** — sprawdzanie DR\n"

        print(f"\n===== {player} =====")
        print(soup.get_text(" ", strip=True)[:5000])

    except Exception as error:
        message += f"❌ **{player}** — błąd\n"
        print(f"BŁĄD {player}: {error}")

message += "\n🔄 **Test pobierania danych**"

if WEBHOOK_URL:
    requests.post(
        WEBHOOK_URL,
        json={"content": message},
        timeout=30
    )
