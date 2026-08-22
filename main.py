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

    dr_sr_match = re.search(
        rf"{re.escape(psn)}.*?\b([A-E]\+?|S)\s+([A-E]|S)\b",
        text,
        re.IGNORECASE
    )

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

    for player in PLAYERS:
        try:
            ranking.append(get_player(player))
        except Exception as error:
            print(f"BŁĄD {player}: {error}")

    # Sortowanie od najwyższego Score
    ranking.sort(key=lambda x: x["score"], reverse=True)

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]

    message = "🏆 **SRS DRIVER RANKING**\n\n"

    for i, player in enumerate(ranking):
        message += (
            f"{medals[i]} **{player['psn']}**\n"
            f"🏅 DR: **{player['dr']}** | SR: **{player['sr']}**\n"
            f"📊 Score: **{player['score']:.2f}**\n\n"
        )

    message += (
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🔄 **Aktualizacja:** "
        f"{datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

    response = requests.post(
        WEBHOOK_URL,
        json={"content": message},
        timeout=30
    )

    response.raise_for_status()


if __name__ == "__main__":
    main()
