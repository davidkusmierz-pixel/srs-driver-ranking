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
    "Przemo7117",
    "Dawid-y6q",
    "Oligo1234",
    "MaddMikke992",
    "Chudinius47",
    "sajgon89",
    "DoMeme_21",
    "Tomasz225566",
    "szymson70",
    "TastyLsD",
    "JankesKP",
    "BoloBagno",
    "GrandNoobPI",
    "adihanys85",
    "betterWanzzi",
    "ActiveShockPL",
    "Hrupek98",
    "Jaras_GD",
    "PRT_El_Chapo",
    "demon23mor"
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

    # Pobieranie PK i PFK
    pk_pfk_match = re.search(
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

    pk = pk_pfk_match.group(1) if pk_pfk_match else "?"
    pfk = pk_pfk_match.group(2) if pk_pfk_match else "?"
    score = float(score_match.group(1)) if score_match else 0.0

    return {
        "psn": psn,
        "pk": pk,
        "pfk": pfk,
        "score": score
    }


def send_discord_message(message):
    response = requests.post(
        WEBHOOK_URL,
        json={"content": message},
        timeout=30
    )

    response.raise_for_status()


def main():
    ranking = []

    # Pobieranie danych kierowców
    for player in PLAYERS:
        try:
            print(f"Pobieram: {player}")
            ranking.append(get_player(player))

        except Exception as error:
            print(f"BŁĄD {player}: {error}")

    # Sortowanie według Edge Score
    ranking.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    # Nagłówek rankingu
    current_message = (
        "\u200b\n"
        "📈 **RANKING GŁÓWNY**\n\n"
        "🏁 Klasyfikacja według **EDGE SCORE**\n\n"
        "🔄 **Aktualizacja: raz w tygodniu**\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    message_number = 1
    messages = []

    # Tworzenie rankingu
    for i, player in enumerate(ranking, start=1):

        if i == 1:
            medal = "🥇"
        elif i == 2:
            medal = "🥈"
        elif i == 3:
            medal = "🥉"
        else:
            medal = "🏁"

        player_text = (
            f"{medal} **{i}. {player['psn']}**\n"
            f"🏅 PK **{player['pk']}** • PFK **{player['pfk']}**\n"
            f"📊 Score: **{player['score']:.2f}**\n\n"
        )

        # Podział rankingu na kilka wiadomości
        if len(current_message) + len(player_text) > 1900:
            messages.append(current_message)
            message_number += 1

            current_message = (
                f"📈 **RANKING GŁÓWNY — CZĘŚĆ {message_number}**\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
            )

        current_message += player_text

    # Dodanie ostatniej części
    if current_message:
        messages.append(current_message)

    # Informacja o ostatniej aktualizacji
    messages[-1] += (
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🕒 **Ostatnia aktualizacja:** "
        f"{datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

    # Wysyłanie rankingu na Discord
    for number, message in enumerate(messages, start=1):
        send_discord_message(message)
        print(f"Wysłano część {number}/{len(messages)}")

    print("Ranking SRS został wysłany na Discord!")


if __name__ == "__main__":
    main()
