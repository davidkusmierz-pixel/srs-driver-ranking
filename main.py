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


WEBHOOK_URL = os.getenv("https://discord.com/api/webhooks/1540826456802992178/kCh8knUjF5cb1ZXGegpXEV4vNMHtjIFmEzTBx5iTrG_YgsEQ2ekMAhhcWPk40P895muo")

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
# ODCZYT ID STARYCH WIADOMOŚCI
# ==================================================

def load_message_ids():

    if not os.path.exists(
        MESSAGE_IDS_FILE
    ):
        print(
            "Nie znaleziono pliku message_ids.txt"
        )

        return []

    with open(
        MESSAGE_IDS_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        message_ids = [
            line.strip()
            for line in file
            if line.strip()
        ]

    print(
        f"Znaleziono zapisanych ID: "
        f"{len(message_ids)}"
    )

    for message_id in message_ids:
        print(
            f"STARE ID: {message_id}"
        )

    return message_ids


# ==================================================
# ZAPIS NOWYCH ID
# ==================================================

def save_message_ids(message_ids):

    print(
        f"Zapisuję {len(message_ids)} "
        f"nowych ID..."
    )

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
                f"ZAPISANO ID: "
                f"{message_id}"
            )


# ==================================================
# WYSYŁANIE WIADOMOŚCI
# ==================================================

def send_discord_message(message):

    if not WEBHOOK_URL:

        raise Exception(
            "Brak DISCORD_WEBHOOK "
            "w GitHub Secrets!"
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
        f"STATUS DISCORD: "
        f"{response.status_code}"
    )

    response.raise_for_status()

    data = response.json()

    print(
        f"ODPOWIEDŹ DISCORD: "
        f"{data}"
    )

    message_id = str(
        data["id"]
    )

    print(
        f"NOWE ID WIADOMOŚCI: "
        f"{message_id}"
    )

    return message_id


# ==================================================
# USUWANIE STAREJ WIADOMOŚCI
# ==================================================

def delete_discord_message(message_id):

    response = requests.delete(
        f"{WEBHOOK_URL}/messages/{message_id}",
        timeout=30
    )

    print(
        f"USUWANIE {message_id}: "
        f"STATUS {response.status_code}"
    )

    # Wiadomość została usunięta
    if response.status_code == 204:

        print(
            f"USUNIĘTO: {message_id}"
        )

        return

    # Wiadomości już nie ma
    if response.status_code == 404:

        print(
            f"NIE ZNALEZIONO: "
            f"{message_id}"
        )

        return

    response.raise_for_status()


# ==================================================
# GŁÓWNY PROGRAM
# ==================================================

def main():

    print(
        "========== START =========="
    )

    ranking = []


    # ==================================================
    # POBIERANIE DANYCH
