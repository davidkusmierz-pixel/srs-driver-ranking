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
        "Chrome/120 Safari/537.36"
    )
}

MESSAGE_IDS_FILE = "message_ids.txt"

RANKING_URL = "https://gtsh-rank.com/ranking/"


def normalize_name(name):
    return name.strip().lower()


def get_all_players():

    response = requests.get(
        RANKING_URL,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    text = soup.get_text(
        "\n",
        strip=True
    )

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    players_data = []

    for index, line in enumerate(lines):

        # Szukamy klasy DR
        if line in [
            "E", "E+",
            "D", "D+",
            "C", "C+",
            "B", "B+",
            "A", "A+",
            "S"
        ]:

            dr_class = line

            # Szukamy kolejnej liczby będącej PK
            for offset in range(1, 10):

                if index + offset >= len(lines):
                    break

                value = lines[index + offset]

                if re.fullmatch(r"\d{4,6}", value):

                    # Szukamy nazwy kierowcy przed PK
                    player_name = None

                    for back in range(
                        1,
                        min(index, 10) + 1
                    ):

                        possible_name = (
                            lines[index - back]
                        )

                        if (
                            not re.fullmatch(
                                r"\d+\.?",
                                possible_name
                            )
                            and possible_name not in [
                                "Global",
                                "TOP Split 1",
                                "TOP Split 2",
                                "TOP Split 3",
                                "TOP Split 4",
                                "Nat.",
                                "Driver / Brand",
                                "DR / Avg",
                                "Stat",
                                "Trend"
                            ]
                        ):

                            player_name = possible_name
                            break

                    if player_name:

                        players_data.append({
                            "psn": player_name,
                            "pk": int(value),
                            "dr": dr_class
                        })

                    break

    return players_data


def get_player_data(all_players, psn):

    target = normalize_name(psn)

    for player in all_players:

        current_name = normalize_name(
            player["psn"]
        )

        if current_name == target:

            return {
                "psn": psn,
                "pk": player["pk"],
                "dr": player["dr"]
            }

    return {
        "psn": psn,
        "pk": 0,
        "dr": "?"
    }


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


    print(
        "Pobieram ranking z GTSH-Rank..."
    )

    try:

        all_players = get_all_players()

        print(
            f"Pobrano {len(all_players)} zawodników."
        )

    except Exception as error:

        print(
            f"BŁĄD pobierania rankingu: {error}"
        )

        return


    ranking = []


    for player in PLAYERS:

        try:

            print(
                f"Sprawdzam: {player}"
            )

            data = get_player_data(
                all_players,
                player
            )

            ranking.append(data)


            if data["pk"] == 0:

                print(
                    f"Nie znaleziono: {player}"
                )

            else:

                print(
                    f"Znaleziono: "
                    f"{player} | "
                    f"{data['dr']} | "
                    f"{data['pk']}"
                )

        except Exception as error:

            print(
                f"BŁĄD {player}: {error}"
            )


    # Sortowanie według PK
    ranking.sort(
        key=lambda x: x["pk"],
        reverse=True
    )


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


        if player["pk"] > 0:

            pk_text = (
                f"{player['pk']:,}"
                .replace(",", " ")
            )

        else:

            pk_text = "Brak danych"


        player_text = (
            f"{medal} **{i}. "
            f"{player['psn']}**\n"
            f"🏅 PK **{player['dr']}**"
            f" • **{pk_text} PK**\n\n"
        )


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
                f"— CZĘŚĆ "
                f"{message_number}**\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
            )


        current_message += player_text


    if current_message:

        messages.append(
            current_message
        )


    messages[-1] += (
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🕒 **Ostatnia aktualizacja:** "
        f"{datetime.now(ZoneInfo('Europe/Warsaw')).strftime('%d.%m.%Y %H:%M')}"
    )


    old_message_ids = (
        load_message_ids()
    )

    new_message_ids = []


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
                    f"Nie udało się zaktualizować "
                    f"części {number + 1}: "
                    f"{error}"
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


    save_message_ids(
        new_message_ids
    )


    print(
        "Ranking SRS został zaktualizowany!"
    )


if __name__ == "__main__":

    main()
