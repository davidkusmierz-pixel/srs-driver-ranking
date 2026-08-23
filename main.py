import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import quote


PLAYERS = [
    "SolidSnakePoland",
    "ALF7",
    "lucekbks",
    "MTE_JaXoN_GT",
    "Przemo7117",
    "Dawid-y6q",
    "OliIgo1234",
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
    "SRS-Tony-Montana",
    "demon23mor"
]


WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/120.0 Safari/537.36"
    )
}


MESSAGE_IDS_FILE = "message_ids.txt"


def get_player(psn):

    # Profil konkretnego zawodnika
    url = (
        "https://gtsh-rank.com/profile/?id="
        + quote(psn)
    )

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    # Cały tekst strony
    text = soup.get_text(
        "\n",
        strip=True
    )

    # Usuwamy nadmiarowe spacje
    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    # DR Points
    points_match = re.search(
        r"DR Points:\s*([0-9\s,]+)",
        text,
        re.IGNORECASE
    )

    # Liczba zawodów
    races_match = re.search(
        r"Races:\s*([0-9,]+)",
        text,
        re.IGNORECASE
    )

    # Online ID
    online_id_match = re.search(
        r"Online ID:\s*([^\n]+)",
        text,
        re.IGNORECASE
    )

    # Pobranie DR i SR z tekstu strony
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    dr = "?"
    sr = "?"

    # GTSH pokazuje na profilu:
    #
    # DR
    # SR
    # C
    # S
    #
    # Szukamy tego układu

    for index, line in enumerate(lines):

        if line.upper() == "DR":

            for offset in range(
                1,
                min(10, len(lines) - index)
            ):

                possible_dr = (
                    lines[index + offset]
                    .upper()
                )

                if possible_dr in [
                    "E",
                    "E+",
                    "D",
                    "D+",
                    "C",
                    "C+",
                    "B",
                    "B+",
                    "A",
                    "A+",
                    "S"
                ]:

                    dr = possible_dr
                    break


        if line.upper() == "SR":

            for offset in range(
                1,
                min(10, len(lines) - index)
            ):

                possible_sr = (
                    lines[index + offset]
                    .upper()
                )

                if possible_sr in [
                    "E",
                    "E+",
                    "D",
                    "D+",
                    "C",
                    "C+",
                    "B",
                    "B+",
                    "A",
                    "A+",
                    "S"
                ]:

                    sr = possible_sr
                    break


    # DR Points
    if points_match:

        points_text = (
            points_match.group(1)
            .replace(" ", "")
            .replace(",", "")
        )

        points = int(points_text)

    else:

        points = 0


    # Liczba zawodów
    if races_match:

        races_text = (
            races_match.group(1)
            .replace(",", "")
        )

        races = int(races_text)

    else:

        races = 0


    # Sprawdzenie, czy profil faktycznie został znaleziony
    if not online_id_match:

        print(
            f"Nie znaleziono profilu: {psn}"
        )

        return {
            "psn": psn,
            "dr": "?",
            "sr": "?",
            "points": 0,
            "races": 0
        }


    print(
        f"Znaleziono: {psn} | "
        f"DR {dr} | "
        f"SR {sr} | "
        f"PK {points} | "
        f"Zawody {races}"
    )


    return {
        "psn": psn,
        "dr": dr,
        "sr": sr,
        "points": points,
        "races": races
    }


# Pobieranie zapisanych ID wiadomości
def load_message_ids():

    if not os.path.exists(
        MESSAGE_IDS_FILE
    ):
        return []

    with open(
        MESSAGE_IDS_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return [
            line.strip()
            for line in file.readlines()
            if line.strip().isdigit()
        ]


# Zapisywanie ID wiadomości
def save_message_ids(message_ids):

    with open(
        MESSAGE_IDS_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        for message_id in message_ids:

            file.write(
                f"{message_id}\n"
            )


# Wysyłanie nowej wiadomości
def send_discord_message(message):

    response = requests.post(
        f"{WEBHOOK_URL}?wait=true",
        json={
            "content": message
        },
        timeout=30
    )

    response.raise_for_status()

    return response.json()["id"]


# Aktualizacja istniejącej wiadomości
def update_discord_message(
    message_id,
    message
):

    response = requests.patch(
        f"{WEBHOOK_URL}/messages/{message_id}",
        json={
            "content": message
        },
        timeout=30
    )

    response.raise_for_status()


def main():

    if not WEBHOOK_URL:

        print(
            "BŁĄD: Brak DISCORD_WEBHOOK!"
        )

        return


    ranking = []


    # Pobieranie każdego zawodnika osobno
    for player in PLAYERS:

        try:

            print(
                f"Pobieram: {player}"
            )

            data = get_player(
                player
            )

            ranking.append(
                data
            )

        except Exception as error:

            print(
                f"BŁĄD {player}: {error}"
            )

            ranking.append({
                "psn": player,
                "dr": "?",
                "sr": "?",
                "points": 0,
                "races": 0
            })


    # Sortowanie według DR Points
    ranking.sort(
        key=lambda x: x["points"],
        reverse=True
    )


    # Nagłówek rankingu
    current_message = (
        "\u200b\n"
        "📈 **RANKING GŁÓWNY SRS**\n\n"
        "🏁 Klasyfikacja według **PK**\n\n"
        "🌐 Źródło: **GTSH-Rank**\n\n"
        "🔄 **Aktualizacja: raz w tygodniu**\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
    )


    messages = []

    message_number = 1


    # Tworzenie rankingu
    for i, player in enumerate(
        ranking,
        start=1
    ):

        if i == 1:

            medal = "🥇"

        elif i == 2:

            medal = "🥈"

        elif i == 3:

            medal = "🥉"

        else:

            medal = "🏁"


        if player["points"] > 0:

            points_text = (
                f"{player['points']:,}"
                .replace(",", " ")
            )

        else:

            points_text = "Brak danych"


        if player["races"] > 0:

            races_text = (
                f"{player['races']:,}"
                .replace(",", " ")
            )

        else:

            races_text = "Brak danych"


        player_text = (
            f"{medal} **{i}. {player['psn']}**\n"
            f"🏅 DR **{player['dr']}**"
            f" • SR **{player['sr']}**\n"
            f"📊 PK: **{points_text}**\n"
            f"🏁 Zawody: **{races_text}**\n\n"
        )


        # Podział na kilka wiadomości
        if (
            len(current_message)
            + len(player_text)
            > 1900
        ):

            messages.append(
                current_message
            )

            message_number += 1

            current_message = (
                f"📈 **RANKING GŁÓWNY SRS "
                f"— CZĘŚĆ {message_number}**\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
            )


        current_message += player_text


    # Dodanie ostatniej części
    if current_message:

        messages.append(
            current_message
        )


    # Data aktualizacji
    messages[-1] += (
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🕒 **Ostatnia aktualizacja:** "
        f"{datetime.now(ZoneInfo('Europe/Warsaw')).strftime('%d.%m.%Y %H:%M')}"
    )


    # Pobranie starych ID wiadomości
    old_message_ids = (
        load_message_ids()
    )

    new_message_ids = []


    # Aktualizacja lub wysyłanie
    for number, message in enumerate(
        messages
    ):

        if number < len(
            old_message_ids
        ):

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
                    f"Nie udało się "
                    f"zaktualizować części "
                    f"{number + 1}: {error}"
                )

                message_id = (
                    send_discord_message(
                        message
                    )
                )

                new_message_ids.append(
                    message_id
                )


        else:

            message_id = (
                send_discord_message(
                    message
                )
            )

            new_message_ids.append(
                message_id
            )

            print(
                f"Wysłano część "
                f"{number + 1}/{len(messages)}"
            )


    # Zapisanie ID wiadomości
    save_message_ids(
        new_message_ids
    )


    print(
        "Ranking SRS został zaktualizowany!"
    )


if __name__ == "__main__":

    main()
