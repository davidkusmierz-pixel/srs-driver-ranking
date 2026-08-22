import os
import re
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

    # Szuka DR i SR, np. "A+ S Poland"
    dr_sr_match = re.search(
        rf"{re.escape(psn)}.*?\b([A-E]\+?|S)\s+([A-E]|S)\b",
        text,
        re.IGNORECASE
    )

    # Szuka Edge Score, np. "54.73 Edge Score"
    score_match = re.search(
        r"(\d{1,3}\.\d{1,2})\s+Edge Score",
        text,
        re.IGNORECASE
    )

    dr = "?"
    sr = "?"

    if dr_sr_match:
        dr = dr_sr_match.group(1)
        sr = dr_sr_match.group(2)

    score = score_match.group(1) if score_match else "?"

    return {
        "psn": psn,
        "dr": dr,
        "sr": sr,
        "score": score
    }


def main():
    message = "🏆 **SRS DRIVER RANKING — TEST**\n\n"

    for player in PLAYERS:
        try:
            data = get_player(player)

            message += (
                f"👤 **{data['psn']}**\n"
                f"🏅 DR: **{data['dr']}** | SR: **{data['sr']}**\n"
                f"📊 Score: **{data['score']}**\n\n"
            )

            print(data)

        except Exception as error:
            message += f"❌ **{player}** — błąd pobierania\n"
            print(f"BŁĄD {player}: {error}")

    requests.post(
        WEBHOOK_URL,
        json={"content": message},
        timeout=30
    )


if __name__ == "__main__":
    main()
