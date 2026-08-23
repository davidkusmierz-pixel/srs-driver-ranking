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
    "Tomas225566",
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

MESSAGE_IDS_FILE = "message_ids.txt"


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

    pk_pfk_match = re.search(
        rf"{re.escape(psn)}.*?\b([A-E]\+?|S)\s+([A-E]|S)\b",
        text,
        re.IGNORECASE
    )

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


def load_message_ids():
    if not os.path.exists(MESSAGE_IDS_FILE):
        return []

    with open(MESSAGE_IDS_FILE, "r") as file:
        return [
            line.strip()
            for line in file.readlines()
            if line.strip().isdigit()
        ]


def save_message_ids(message_ids):
    with open(MESSAGE_IDS_FILE, "w") as file:
        for message_id in message_ids:
            file.write(f"{message_id}\n")


def send_discord_message(message):
    response = requests.post(
        f"{WEBHOOK_URL}?wait=true",
        json={"content": message},
        timeout=30
    )

    response.raise_for_status()

    return response.json()["id"]


def update_discord_message(message_id, message):
    response = requests.patch(
        f"{WEBHOOK_URL}/messages/{message_id}",
        json={"content": message},
        timeout=30
    )

    response.raise_for_status()


def main():
    ranking = []

    for player in PLAYERS:
        try:
            print(f"Pobieram: {player}")
            ranking.append(get_player(player))

        except Exception as error:
            print(f"BŁĄD {player}: {error}")

    ranking.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    current_message = (
        "\u200b\n"
        "📈 **RANKING GŁÓWNY**\n\n"
        "🏁 Klasyfikacja według **EDGE SCORE**\n\n"
        "🔄 **Aktualizacja: raz w tygodniu**\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    message_number = 1
    messages = []

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

        if len(current_message) + len(player_text) > 1900:
            messages.append(current_message)

            message_number += 1

            current_message = (
                f"📈 **RANKING GŁÓWNY — CZĘŚĆ {message_number}**\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
            )

        current_message += player_text

    if current_message:
        messages.append(current_message)

    messages[-1] += (
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🕒 **Ostatnia aktualizacja:** "
        f"{datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

    old_message_ids = load_message_ids()
    new_message_ids = []

    for number, message in enumerate(messages):

        if number < len(old_message_ids):

            try:
                update_discord_message(
                    old_message_ids[number],
                    message
                )

                new_message_ids.append(
                    old_message_ids[number]
                )

                print(
                    f"Zaktualizowano część "
                    f"{number + 1}/{len(messages)}"
                )

            except Exception as error:
                print(
                    f"Nie udało się zaktualizować: {error}"
                )

                message_id = send_discord_message(message)
                new_message_ids.append(message_id)

        else:
            message_id = send_discord_message(message)
            new_message_ids.append(message_id)

            print(
                f"Wysłano część "
                f"{number + 1}/{len(messages)}"
            )

    save_message_ids(new_message_ids)

    print("Ranking SRS został zaktualizowany!")


if __name__ == "__main__":
    main()
