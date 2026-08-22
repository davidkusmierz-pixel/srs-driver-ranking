import os
import re
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

    # Pobieranie DR i SR
    dr_sr_match = re.search(
        rf"{re.escape(psn)}.*?\b([A-E]\+?|S)\s+([A-E]|S)\b",
        text,
        re.IGNORECASE
    )

    # Pobieranie Edge Score
    score_match = re.search(
        r"(\d{1,3}\.\d{1,2})\s+Edge Score",
        text,
        re.IGNORECASE
    )

    dr = dr_sr_match.group(1) if dr_sr_match else "?"
    sr = dr_sr_match.group(2) if dr_sr_match else "?"
    score = float(score_match.group(1)) if score_match else 0.0

    return {
        "psn": psn,
        "dr": dr,
        "sr": sr,
        "score": score
    }


def main():
    ranking = []

    # Pobieranie danych kierowców
    for player in PLAYERS:
        try:
            ranking.append(get_player(player))
        except Exception as error:
            print(f"BŁĄD {player}: {error}")

    # Sortowanie od najwyższego Score
    ranking.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    message = "🏆 **SRS DRIVER RANKING**\n\n"

    # Tworzenie czytelnego rankingu
    for i, player in enumerate(ranking, start=1):

        if i == 1:
            medal = "🥇"
        elif i == 2:
            medal = "🥈"
        elif i == 3:
            medal = "🥉"
        else:
            medal = "🏁"

        message += (
            f"{medal} **{i}. {player['psn']}**\n"
            f"🏅 DR **{player['dr']}** • SR **{player['sr']}**\n"
            f"📊 Score: **{player['score']:.2f}**\n\n"
        )

    # Data aktualizacji
    message += (
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🔄 **Ostatnia aktualizacja:** "
        f"{datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

    # Wysyłanie rankingu na Discord
    response = requests.post(
        WEBHOOK_URL,
        json={"content": message},
        timeout=30
    )

    response.raise_for_status()

    print("Ranking SRS został wysłany na Discord!")


if __name__ == "__main__":
    main()
