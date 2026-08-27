import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo


# ==================================================
# PSN ID : NAZWA WYŚWIETLANA NA DISCORDZIE
# ==================================================

PLAYERS = {
    "SolidSnakePoland": "RickyK",
    "ALF7": "SRS ALF7_VR2",
    "lucekbks": "SRS-Popek",
    "MTE_JaXoN_GT": "@JaXoN_GT_YT",
    "Przemo7117": "SRS Borko",
    "Dawid-y6q": "SRS Dawid-y6q",
    "Oligo1234": "SRS_skawa_gt7",
    "MaddMikke992": "SRS BearRacer",
    "Chudinius": "TCS_Chudinius",
    "sajgon89": "sajgon",
    "DoMeme_21": "SRS DoMeme",
    "Tomas225566": "SRS TomaszPL",
    "szymson70": "Fymek",
    "TastyLsD": "SRS TastyXD",
    "JankesKP": "SRS_JankesKP",
    "BoloBagno": "SRS Bolo",
    "GrandNoobPl": "SRS NAJTI",
    "adihanys85": "SRS Adi",
    "betterWanzzi": "SRS Adi",
    "ActiveShockPL": "SRS-ActiveShock",
    "Hrupek98": "SRS-Hrupek98",
    "Jaras_GD": "Jaras_GD",
    "PRT_El_Chapo": "PRT_EL_CHAPO",
    "Piko88-Z": "NRT_Piko",
    "destro2207": "Desmond",
    "Wojtek_Kl69": "Wojtek_Kl",
    "zeusek22": "zeusek666",
    "jupiter977gaudy": "SRS Mario",
    "CUSTOM_PUNCH85": "SRS_CUSTOM PUNCH",
    "demon23mor": "SRS Demon23mor"
}


# ==================================================
# DISCORD WEBHOOK Z GITHUB SECRETS
# ==================================================

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

MESSAGE_IDS_FILE = "message_ids.txt"


# ==================================================
# POBIERANIE DANYCH KIEROWCY
# ==================================================

def get_player(psn, username):

    url = f"https://www.dg-edge.com/players/{psn}"

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

    text = soup.get_text(
        " ",
        strip=True
    )

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

    pk = (
        pk_pfk_match.group(1)
        if pk_pfk_match
        else "?"
    )

    pfk = (
        pk_pfk_match.group(2)
        if pk_pfk_match
        else "?"
    )

    score = (
        float(score_match.group(1))
        if score_match
        else 0.0
    )

    return {
        "username": username,
        "pk": pk,
        "pfk": pfk,
        "score": score
    }


# ==================================================
# ODCZYT STARYCH ID WIADOMOŚCI
# ==================================================

def load_message_ids():

    if not os.path.exists(MESSAGE_IDS_FILE):
        print("Brak starego pliku message_ids.txt")
        return []

    with open(
        MESSAGE_IDS_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        message_ids = [
            line.strip()
            for line in file
            if line.strip().isdigit()
        ]

    print(
        f"Znaleziono starych wiadomości: "
        f"{len(message_ids)}"
    )

    return message_ids


# ==================================================
# ZAPIS NOWYCH ID
# ==================================================

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

    print(
        f"Zapisano {len(message_ids)} "
        f"nowych ID"
    )


# ==================================================
# WYSYŁANIE WIADOMOŚCI
# ==================================================

def send_discord_message(message):

    if not WEBHOOK_URL:
        raise Exception(
            "Brak DISCORD_WEBHOOK w GitHub Secrets"
        )

    response = requests.post(
        WEBHOOK_URL,
        params={
            "wait": "true"
        },
        json={
            "content": message
        },
        timeout=30
    )

    print(
        f"Discord status wysyłania: "
        f"{response.status_code}"
    )

    response.raise_for_status()

    data = response.json()

    message_id = str(
        data["id"]
    )

    print(
        f"NOWE ID: {message_id}"
    )

    return message_id


# ==================================================
# USUWANIE STAREJ WIADOMOŚCI
# ==================================================

def delete_discord_message(message_id):

    if not WEBHOOK_URL:
        raise Exception(
            "Brak DISCORD_WEBHOOK w GitHub Secrets"
        )

    response = requests.delete(
        f"{WEBHOOK_URL}/messages/{message_id}",
        timeout=30
    )

    if response.status_code == 204:

        print(
            f"🗑️ Usunięto: "
            f"{message_id}"
        )

        return

    if response.status_code == 404:

        print(
            f"⚠️ Wiadomość już nie istnieje: "
            f"{message_id}"
        )

        return

    print(
        f"Błąd usuwania {message_id}: "
        f"{response.status_code}"
    )

    print(
        response.text
    )


# ==================================================
# GŁÓWNY PROGRAM
# ==================================================

def main():

    print(
        "========== START RANKINGU =========="
    )

    if not WEBHOOK_URL:

        print(
            "BŁĄD: Brak DISCORD_WEBHOOK!"
        )

        return

    ranking = []


    # ==================================================
    # POBIERANIE DANYCH KIEROWCÓW
    # ==================================================

    for psn, username in PLAYERS.items():

        try:

            print(
                f"Pobieram dane: "
                f"{username}"
            )

            player = get_player(
                psn,
                username
            )

            ranking.append(player)

        except Exception as error:

            print(
                f"BŁĄD {username}: "
                f"{error}"
            )


    # ==================================================
    # SORTOWANIE
    # ==================================================

    ranking.sort(
        key=lambda x: x["score"],
        reverse=True
    )


    # ==================================================
    # TWORZENIE RANKINGU
    # ==================================================

    current_message = (
        "\u200b\n"
        "📈 **RANKING GŁÓWNY**\n\n"
        "🏁 Klasyfikacja według "
        "**EDGE SCORE**\n\n"

        "📊 **Punkty są liczone na podstawie:**\n"
        "⏱️ **Czasówek Daily Race** – "
        "uzyskanych czasów kwalifikacyjnych\n"
        "🏁 **Wyzwań i czasówek** – "
        "uzyskanych wyników i czasów\n\n"

        "💬 **Im lepsze czasy i wyniki, "
        "tym więcej punktów zdobywa kierowca.**\n\n"

        "🔄 **Aktualizacja: raz dziennie**\n\n"

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


        player_text = (
            f"{medal} "
            f"**{i}. {player['username']}**\n"

            f"🏅 PK "
            f"**{player['pk']}** • "
            f"PFK **{player['pfk']}**\n"

            f"📊 Score: "
            f"**{player['score']:.2f}**\n\n"
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
                f"📈 **RANKING GŁÓWNY — "
                f"CZĘŚĆ {message_number}**\n\n"

                "━━━━━━━━━━━━━━━━━━━━\n\n"
            )


        current_message += player_text


    if current_message:

        messages.append(
            current_message
        )


    # ==================================================
    # DATA AKTUALIZACJI
    # ==================================================

    messages[-1] += (
        "━━━━━━━━━━━━━━━━━━━━\n\n"

        f"🕒 **Ostatnia aktualizacja:** "
        f"{datetime.now(ZoneInfo('Europe/Warsaw')).strftime('%d.%m.%Y %H:%M')}"
    )


    # ==================================================
    # USUWANIE STARYCH WIADOMOŚCI
    # ==================================================

    print(
        "========== USUWANIE STARYCH =========="
    )

    old_message_ids = load_message_ids()

    for message_id in old_message_ids:

        try:

            delete_discord_message(
                message_id
            )

        except Exception as error:

            print(
                f"BŁĄD USUWANIA "
                f"{message_id}: {error}"
            )


    # ==================================================
    # WYSYŁANIE NOWYCH WIADOMOŚCI
    # ==================================================

    print(
        "========== WYSYŁANIE NOWYCH =========="
    )

    new_message_ids = []

    for number, message in enumerate(
        messages,
        start=1
    ):

        try:

            message_id = send_discord_message(
                message
            )

            new_message_ids.append(
                message_id
            )

            print(
                f"📩 Wysłano część "
                f"{number}/{len(messages)}"
            )

        except Exception as error:

            print(
                f"BŁĄD WYSYŁANIA "
                f"CZĘŚCI {number}: {error}"
            )


    # ==================================================
    # ZAPIS ID NOWYCH WIADOMOŚCI
    # ==================================================

    print(
        "========== ZAPIS ID =========="
    )

    save_message_ids(
        new_message_ids
    )

    print(
        f"ID zapisane do pliku: "
        f"{new_message_ids}"
    )

    print(
        "========== KONIEC =========="
    )


if __name__ == "__main__":
    main()
