import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo

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
    "Piko88-Z",
    "destro2207",
    "Wojtek_Kl",
    "zeusek22",
    "jupiter977gaudy",
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


# Pobieranie zapisanych ID wiadomości
def load_message_ids():
    if not os.path.exists(MESSAGE_IDS_FILE):
        return []

    with open(MESSAGE_IDS_FILE, "r", encoding="utf-8") as file:
        return [
            line.strip()
            for line in file.readlines()
            if line.strip().isdigit()
        ]


# Zapisywanie ID wiadomości
def save_message_ids(message_ids):
    with open(MESSAGE_IDS_FILE, "w", encoding="utf-8") as file:
        for message_id in message_ids:
            file.write(f"{message_id}\n")


# Wysyłanie nowej wiadomości
def send_discord_message(message):
    response = requests.post(
        f"{WEBHOOK_URL}?wait=true",
        json={"content": message},
        timeout=30
    )

    response.raise_for_status()

    return response.json()["id"]


# Aktualizacja istniejącej wiadomości
def update_discord_message(message_id, message):
    response = requests.patch(
        f"{WEBHOOK_URL}/messages/{message_id}",
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

    # Nagłówek rankingu + opis punktów
    current_message = (
        "\u200b\n"
        "📈 **RANKING GŁÓWNY**\n\n"
        "🏁 Klasyfikacja według **EDGE SCORE**\n\n"

        "📊 **Punkty są liczone na podstawie:**\n"
        "⏱️ **Czasówek Daily Race** – uzyskanych czasów kwalifikacyjnych\n"
        "🏁 **Wyzwań i czasówek** – uzyskanych wyników i czasów\n\n"

        "💬 **Im lepsze czasy i wyniki, "
        "tym więcej punktów zdobywa kierowca.**\n\n"

        "🔄 **Aktualizacja: raz dziennie**\n\n"
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

    # Polska data i godzina
    messages[-1] += (
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🕒 **Ostatnia aktualizacja:** "
        f"{datetime.now(ZoneInfo('Europe/Warsaw')).strftime('%d.%m.%Y %H:%M')}"
    )

    # Pobieranie ID starych wiadomości
    old_message_ids = load_message_ids()

    # Nowe ID wiadomości
    new_message_ids = []

    # Aktualizacja lub wysyłanie wiadomości
    for number, message in enumerate(messages):

        # Jeśli wiadomość już istnieje
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
                    f"Nie udało się zaktualizować części "
                    f"{number + 1}: {error}"
                )

                # Jeśli wiadomość została usunięta,
                # wysyłamy nową
                message_id = send_discord_message(message)

                new_message_ids.append(message_id)

                print(
                    f"Wysłano nową część "
                    f"{number + 1}/{len(messages)}"
                )

        # Pierwsze uruchomienie
        else:
            message_id = send_discord_message(message)

            new_message_ids.append(message_id)

            print(
                f"Wysłano część "
                f"{number + 1}/{len(messages)}"
            )

    # Zapisanie ID wiadomości
    save_message_ids(new_message_ids)

    print("Ranking SRS został zaktualizowany!")


if __name__ == "__main__":
    main()
