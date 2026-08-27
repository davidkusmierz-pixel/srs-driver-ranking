import os
import json
import time
import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from playwright.sync_api import sync_playwright


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
# USTAWIENIA
# ==================================================

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")

KNOWN_EVENTS_FILE = "known_events.json"


# ==================================================
# WCZYTANIE ZAPAMIĘTANYCH WYNIKÓW
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

    except Exception as error:

        print(
            f"BŁĄD known_events.json: {error}"
        )

        return {}


# ==================================================
# ZAPIS ZAPAMIĘTANYCH WYNIKÓW
# ==================================================

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
# POBIERANIE EVENTS RESULTS
# ==================================================

def get_player_events(page, psn):

    url = (
        f"https://www.dg-edge.com/players/{psn}"
    )

    response = page.goto(
        url,
        wait_until="networkidle",
        timeout=60000
    )

    if not response:
        return []

    if response.status == 404:

        print(
            f"⚠️ Nie znaleziono profilu: {psn}"
        )

        return []

    try:

        page.wait_for_timeout(3000)

    except Exception:
        pass


    # Pobieramy cały tekst już po załadowaniu JS
    body_text = page.locator(
        "body"
    ).inner_text()

    # Sprawdzamy czy sekcja istnieje
    if "Events results" not in body_text:

        print(
            "⚠️ Nie znaleziono sekcji Events results"
        )

        return []


    # Szukamy elementu z tekstem
    events_heading = page.get_by_text(
        "Events results",
        exact=False
    ).first


    try:

        # Przewijamy do sekcji
        events_heading.scroll_into_view_if_needed()

        page.wait_for_timeout(2000)

    except Exception:
        pass


    # Pobieramy elementy zawierające wyniki
    elements = page.locator(
        "div, article, li"
    )

    count = elements.count()

    events = []
    seen = set()


    for index in range(count):

        try:

            element = elements.nth(index)

            text = element.inner_text(
                timeout=3000
            ).strip()


            # Karta musi zawierać dane charakterystyczne
            keywords = [
                "GLOBAL",
                "COUNTRY",
                "Score Impact",
                "Best Time"
            ]


            matches = sum(
                1
                for keyword in keywords
                if keyword.lower()
                in text.lower()
            )


            if matches < 2:
                continue


            # Pomijamy ogromne kontenery strony
            if len(text) < 20:
                continue

            if len(text) > 2500:
                continue


            event_id = hashlib.sha256(
                f"{psn}|{text}".encode(
                    "utf-8"
                )
            ).hexdigest()


            if event_id in seen:
                continue


            seen.add(event_id)


            events.append({
                "id": event_id,
                "raw": text
            })


        except Exception:

            continue


    return events


# ==================================================
# FORMAT WIADOMOŚCI
# ==================================================

def format_event(username, raw):

    now = datetime.now(
        ZoneInfo("Europe/Warsaw")
    ).strftime(
        "%d.%m.%Y %H:%M"
    )


    # Zabezpieczenie długości Discorda
    raw = raw[:1500]


    return (
        "🏁 **NOWY WYNIK SRS**\n\n"
        f"👤 **{username}**\n\n"
        f"{raw}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🕒 **Wykryto:** {now}"
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


    with sync_playwright() as p:


        browser = p.chromium.launch(
            headless=True
        )


        context = browser.new_context(
            viewport={
                "width": 1920,
                "height": 1080
            },
            user_agent=(
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/120.0.0.0 "
                "Safari/537.36"
            )
        )


        page = context.new_page()


        for psn, username in PLAYERS.items():

            print(
                f"\nSprawdzam: {username}"
            )


            try:

                events = get_player_events(
                    page,
                    psn
                )


                print(
                    f"Znaleziono wyników: "
                    f"{len(events)}"
                )


                if psn not in known:

                    known[psn] = []


                for event in events:


                    if (
                        event["id"]
                        in known[psn]
                    ):

                        continue


                    print(
                        "🆕 Wykryto nowy wynik"
                    )


                    message = format_event(
                        username,
                        event["raw"]
                    )


                    send_discord(
                        message
                    )


                    known[psn].append(
                        event["id"]
                    )


                    total_new += 1


                    time.sleep(1)


                save_known_events(
                    known
                )


                time.sleep(1)


            except Exception as error:

                print(
                    f"BŁĄD {username}: {error}"
                )


        browser.close()


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
