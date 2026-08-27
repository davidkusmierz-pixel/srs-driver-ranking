import os
import json
import time
import hashlib
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
# USTAWIENIA
# ==================================================

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")

KNOWN_EVENTS_FILE = "known_events.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/120 Safari/537.36"
    )
}


# ==================================================
# WCZYTANIE STARYCH WYNIKÓW
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
            f"BŁĄD odczytu known_events.json: {error}"
        )

        return {}


# ==================================================
# ZAPIS WYNIKÓW
# ==================================================

def save_known_events(events):

    with open(
        KNOWN_EVENTS_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            events,
            file,
            ensure_ascii=False,
            indent=2
        )


# ==================================================
# POBRANIE PROFILU
# ==================================================

def get_player_page(psn):

    url = (
        f"https://www.dg-edge.com/players/{psn}"
    )

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    return response.text


# ==================================================
# WYSZUKANIE KART EVENTS RESULTS
# ==================================================

def extract_event_cards(html):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    cards = []

    selectors = [
        "[class*='event']",
        "[class*='Event']",
        "article",
        "tr"
    ]

    seen = set()

    for selector in selectors:

        elements = soup.select(selector)

        for element in elements:

            text = element.get_text(
                " ",
                strip=True
            )

            if len(text) < 20:
                continue

            keywords = [
                "GLOBAL",
                "COUNTRY",
                "Best Time",
                "Score Impact",
                "Daily Race",
                "Time Trial"
            ]

            matches = sum(
                1
                for keyword in keywords
                if keyword.lower() in text.lower()
            )

            if matches < 2:
                continue

            event_id = hashlib.sha256(
                text.encode("utf-8")
            ).hexdigest()

            if event_id in seen:
                continue

            seen.add(event_id)

            cards.append({
                "id": event_id,
                "raw": text
            })

    return cards


# ==================================================
# WYCIĄGANIE DANYCH Z KARTY
# ==================================================

def parse_event(raw_text):

    lines = raw_text.replace(
        "\n",
        " "
    )

    lines = " ".join(
        lines.split()
    )

    event_type = "Event"
    track = "Nieznany tor"
    car = "Brak danych"
    best_time = "Brak danych"
    global_rank = "Brak danych"
    country_rank = "Brak danych"
    score_impact = "Brak danych"

    event_match = None

    for pattern in [
        r"(Daily Race [ABC])",
        r"(Time Trial)",
        r"(Weekly Challenge)",
        r"(Race [ABC])"
    ]:

        event_match = __import__("re").search(
            pattern,
            lines,
            __import__("re").IGNORECASE
        )

        if event_match:
            event_type = event_match.group(1)
            break

    time_match = __import__("re").search(
        r"\b(\d{1,2}:\d{2}\.\d{3})\b",
        lines
    )

    if time_match:
        best_time = time_match.group(1)

    global_match = __import__("re").search(
        r"GLOBAL[^0-9#]*(?:#)?(\d+)",
        lines,
        __import__("re").IGNORECASE
    )

    if global_match:
        global_rank = (
            f"#{global_match.group(1)}"
        )

    country_match = __import__("re").search(
        r"COUNTRY[^0-9#]*(?:#)?(\d+)",
        lines,
        __import__("re").IGNORECASE
    )

    if country_match:
        country_rank = (
            f"#{country_match.group(1)}"
        )

    impact_match = __import__("re").search(
        r"Score Impact[^+\-0-9]*"
        r"([+\-]?\d+(?:\.\d+)?)",
        lines,
        __import__("re").IGNORECASE
    )

    if impact_match:
        score_impact = impact_match.group(1)

    # Próba pobrania nazwy toru
    parts = lines.split()

    for keyword in [
        "Race",
        "Trial",
        "Challenge"
    ]:

        if keyword in lines:
            track = lines[:120]
            break

    return {
        "event_type": event_type,
        "track": track,
        "car": car,
        "best_time": best_time,
        "global_rank": global_rank,
        "country_rank": country_rank,
        "score_impact": score_impact
    }


# ==================================================
# WYSŁANIE NA DISCORD
# ==================================================

def send_discord_event(
    username,
    event
):

    now = datetime.now(
        ZoneInfo("Europe/Warsaw")
    ).strftime(
        "%d.%m.%Y %H:%M"
    )

    message = (
        "🏁 **NOWY WYNIK SRS**\n\n"

        f"👤 **{username}**\n\n"

        f"🎮 **{event['event_type']}**\n"
        f"📍 **{event['track']}**\n"
        f"⏱️ Najlepszy czas: "
        f"**{event['best_time']}**\n\n"

        f"🌍 GLOBAL: "
        f"**{event['global_rank']}**\n"

        f"🇵🇱 COUNTRY: "
        f"**{event['country_rank']}**\n"

        f"📈 SCORE IMPACT: "
        f"**{event['score_impact']}**\n\n"

        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🕒 {now}"
    )

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
            "BŁĄD: Brak sekretu DISCORD_WEBHOOK!"
        )

        return


    known_events = load_known_events()

    new_events_count = 0


    for psn, username in PLAYERS.items():

        try:

            print(
                f"\nSprawdzam: {username}"
            )

            html = get_player_page(psn)

            cards = extract_event_cards(html)

            print(
                f"Znaleziono kart: {len(cards)}"
            )


            if psn not in known_events:
                known_events[psn] = []


            for card in cards:

                event_id = card["id"]


                # Już wysłany wynik
                if event_id in known_events[psn]:

                    continue


                event = parse_event(
                    card["raw"]
                )


                print(
                    f"NOWY WYNIK: "
                    f"{username} | "
                    f"{event['event_type']}"
                )


                send_discord_event(
                    username,
                    event
                )


                known_events[psn].append(
                    event_id
                )

                new_events_count += 1


                # Mała przerwa
                time.sleep(1)


            # Zapis po każdym zawodniku
            save_known_events(
                known_events
            )


            time.sleep(2)


        except Exception as error:

            print(
                f"BŁĄD {username}: {error}"
            )


    print(
        "\n======================================"
    )

    print(
        f"NOWYCH WYNIKÓW: {new_events_count}"
    )

    print(
        "========== KONIEC =========="
    )


if __name__ == "__main__":
    main()
