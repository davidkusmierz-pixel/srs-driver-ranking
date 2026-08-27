import os
import json
import time
import hashlib
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo


# ==================================================
# PSN ID : NAZWA NA DISCORDZIE
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


WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
KNOWN_EVENTS_FILE = "known_events.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


# ==================================================
# PLIK Z ZAPAMIĘTANYMI WYNIKAMI
# ==================================================

def load_known_events():
    if not os.path.exists(KNOWN_EVENTS_FILE):
        return {}

    try:
        with open(
            KNOWN_EVENTS_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)

    except Exception:
        return {}


def save_known_events(data):
    with open(
        KNOWN_EVENTS_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )


# ==================================================
# POBIERANIE PROFILU
# ==================================================

def get_player_events(psn):

    url = (
        f"https://www.dg-edge.com/players/{psn}"
    )

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    if response.status_code == 404:
        print(f"⚠️ Nie znaleziono profilu: {psn}")
        return []

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    events = []

    # Szukamy wszystkich elementów strony
    for element in soup.find_all(
        ["div", "article", "li", "tr"]
    ):

        text = element.get_text(
            " ",
            strip=True
        )

        # Interesują nas tylko elementy
        # zawierające dane wyników
        if (
            "Score Impact" not in text
            and "GLOBAL" not in text
            and "COUNTRY" not in text
        ):
            continue

        if len(text) < 30:
            continue

        # Usuwamy zbyt długie kontenery
        if len(text) > 2000:
            continue

        event_id = hashlib.sha256(
            f"{psn}|{text}".encode(
                "utf-8"
            )
        ).hexdigest()

        events.append({
            "id": event_id,
            "raw": text
        })

    # Usuwanie duplikatów
    unique = {}
    for event in events:
        unique[event["id"]] = event

    return list(unique.values())


# ==================================================
# FORMATOWANIE WYNIKU
# ==================================================

def format_event(username, raw):

    now = datetime.now(
        ZoneInfo("Europe/Warsaw")
    ).strftime("%d.%m.%Y %H:%M")

    return (
        "🏁 **NOWY WYNIK SRS**\n\n"
        f"👤 **{username}**\n\n"
        f"📊 {raw[:1400]}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🕒 {now}"
    )


# ==================================================
# WYSYŁANIE NA DISCORD
# ==================================================

def send_discord(message):

    response = requests.post(
        WEBHOOK_URL,
        json={
            "content": message
        },
        timeout=30
    )

    response.raise_for_status()


# ==================================================
# GŁÓWNY PROGRAM
# ==================================================

def main():

    print(
        "========== START WYNIKÓW SRS =========="
    )

    if not WEBHOOK_URL:
        print(
            "BŁĄD: Brak DISCORD_WEBHOOK!"
        )
        return

    known = load_known_events()

    total_new = 0


    for psn, username in PLAYERS.items():

        print(
            f"\nSprawdzam: {username}"
        )

        try:

            events = get_player_events(psn)

            print(
                f"Znaleziono wyników: "
                f"{len(events)}"
            )

            if psn not in known:
                known[psn] = []


            for event in events:

                if event["id"] in known[psn]:
                    continue


                message = format_event(
                    username,
                    event["raw"]
                )

                send_discord(message)

                known[psn].append(
                    event["id"]
                )

                total_new += 1

                print(
                    "📤 Wysłano nowy wynik"
                )

                time.sleep(1)


            save_known_events(known)

            time.sleep(1)


        except Exception as error:

            print(
                f"BŁĄD {username}: {error}"
            )


    print(
        "\n======================================"
    )

    print(
        f"NOWYCH WYNIKÓW: {total_new}"
    )

    print(
        "========== KONIEC =========="
    )


if __name__ == "__main__":
    main()
