import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone

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


def get_player(psn_id):
    response = requests.get(
        "https://gtstats.live/",
        params={"psn": psn_id},
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(" ", strip=True)

    # Szuka liczby DR w formacie np. 42,350
    matches = re.findall(
        r"(?:Driver Rating|DR)[^\d]{0,50}(\d{1,3}(?:,\d{3})+|\d+)",
        text,
        re.IGNORECASE
    )

    if matches:
        dr_text = matches[0].replace(",", "")
        dr = int(dr_text)
    else:
        dr = 0

    # Automatycznie ustala klasę
    if dr >= 50000:
        rank = "A+"
    elif dr >= 30000:
        rank = "A"
    elif dr >= 10000:
        rank = "B"
    elif dr >= 4000:
        rank = "C"
    else:
        rank = "D"

    return {
        "psn": psn_id,
        "dr": dr,
        "rank": rank
    }


def main():
    ranking = []

    for player in PLAYERS:
        try:
            data = get_player(player)
            ranking.append(data)
            print(f"Pobrano: {player} — {data['dr']} DR")
        except Exception as error:
            print(f"Błąd dla {player}: {error}")

    # Sortowanie od najwyższego DR
    ranking.sort(key=lambda x: x["dr"], reverse=True)

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]

    message = "🏆 **SRS DRIVER RANKING**\n\n"

    for i, player in enumerate(ranking):
        message += (
            f"{medals[i]} **{player['psn']}** — "
            f"**{player['rank']} | {player['dr']:,} DR**\n"
        )

    now = datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")

    message += (
        "\n━━━━━━━━━━━━━━━━━━━━\n"
        f"🔄 **Ostatnia aktualizacja:** {now}"
    )

    if not WEBHOOK_URL:
        raise ValueError("Brak DISCORD_WEBHOOK!")

    response = requests.post(
        WEBHOOK_URL,
        json={"content": message},
        timeout=30
    )

    response.raise_for_status()

    print("Ranking wysłany na Discord!")


if __name__ == "__main__":
    main()
