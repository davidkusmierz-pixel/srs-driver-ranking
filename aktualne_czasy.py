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
    "betterWanzzi": "SRS Wanzzi",
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
# WKLEJ TUTAJ CAŁY ADRES WEBHOOKA NOWEGO KANAŁU
# ==================================================

WEBHOOK_URL = "https://discord.com/api/webhooks/1542271061830402192/Nb_2yFaNNJHmFkpxMg3NC2zFLRaj1aF6xZuBv4cpFsqheDpQvPtBAKGo3UBdVnsUuRa_"


# ==================================================
# USTAWIENIA
# ==================================================

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

MESSAGE_IDS_FILE = "aktualne_czasy_message_ids.txt"


# ==================================================
# SPRAWDZENIE WEBHOOKA
# ==================================================

def check_webhook():

    if (
        not WEBHOOK_URL
        or WEBHOOK_URL == "WKLEJ_TUTAJ_ADRES_WEBHOOKA"
    ):
        raise RuntimeError(
            "Nie wklejono adresu webhooka!"
        )


# ==================================================
# POBIERANIE STRONY
# ==================================================

def get_page(url):

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    return BeautifulSoup(
        response.text,
        "html.parser"
    )


# ==================================================
# POBIERANIE AKTUALNYCH DAILY A, B, C
# ==================================================

def get_current_daily_events():

    soup = get_page(
        "https://www.dg-edge.com/events"
    )

    events = {}

    for link in soup.find_all(
        "a",
        href=True
    ):

        text = link.get_text(
            " ",
            strip=True
        )

        href = link.get(
            "href",
            ""
        )

        if not text or not href:
            continue

        event_name = None

        if re.search(
            r"Daily\s*(Race\s*)?A",
            text,
            re.IGNORECASE
        ):
            event_name = "Daily Race A"

        elif re.search(
            r"Daily\s*(Race\s*)?B",
            text,
            re.IGNORECASE
        ):
            event_name = "Daily Race B"

        elif re.search(
            r"Daily\s*(Race\s*)?C",
            text,
            re.IGNORECASE
        ):
            event_name = "Daily Race C"

        if not event_name:
            continue

        if event_name in events:
            continue

        if href.startswith("http"):
            full_url = href
        else:
            full_url = (
                "https://www.dg-edge.com"
                + href
            )

        events[event_name] = {
            "name": event_name,
            "url": full_url
        }

    return events


# ==================================================
# POBIERANIE NAZWY TORU
# ==================================================

def get_event_track(event):

    soup = get_page(
        event["url"]
    )

    headings = []

    for tag in soup.find_all(
        ["h1", "h2", "h3"]
    ):

        value = tag.get_text(
            " ",
            strip=True
        )

        if value:
            headings.append(value)

    unique_headings = []

    for heading in headings:

        if (
            heading not in unique_headings
            and heading != event["name"]
        ):
            unique_headings.append(
                heading
            )

    if unique_headings:
        return unique_headings[0]

    return "Aktualny tor"


# ==================================================
# ZAMIANA CZASU NA SEKUNDY
# ==================================================

def time_to_seconds(time_value):

    try:

        minutes, seconds = (
            time_value.split(":")
        )

        return (
            int(minutes) * 60
            + float(seconds)
        )

    except Exception:

        return 999999


# ==================================================
# POBIERANIE CZASÓW KIEROWCÓW
# ==================================================

def get_event_player_times(event):

    soup = get_page(
        event["url"]
    )

    page_text = soup.get_text(
        " ",
        strip=True
    )

    results = []

    for psn, username in PLAYERS.items():

        position = page_text.lower().find(
            psn.lower()
        )

        if position == -1:
            continue

        fragment = page_text[
            max(0, position - 250):
            position + 350
        ]

        times = re.findall(
            r"\b\d{1,2}:\d{2}\.\d{3}\b",
            fragment
        )

        if not times:
            continue

        player_time = times[0]

        results.append({
            "username": username,
            "time": player_time,
            "seconds": time_to_seconds(
                player_time
            )
        })

    # SORTOWANIE OD NAJSZYBSZEGO DO NAJWOLNIEJSZEGO
    results.sort(
        key=lambda x: x["seconds"]
    )

    return results


# ==================================================
# PLIK ID WIADOMOŚCI
# ==================================================

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


# ==================================================
# DISCORD WEBHOOK
# ==================================================

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


# ==================================================
# TWORZENIE BLOKU DAILY
# ==================================================

def create_daily_block(
    event_name,
    track,
    results
):

    block = (
        f"🏎️ **{event_name.upper()}**\n"
        f"📍 **{track}**\n\n"
    )

    if not results:

        block += (
            "❌ Brak aktualnych czasów "
            "zawodników SRS.\n\n"
        )

        return block

    for position, player in enumerate(
        results,
        start=1
    ):

        if position == 1:
            icon = "🥇"

        elif position == 2:
            icon = "🥈"

        elif position == 3:
            icon = "🥉"

        else:
            icon = "🏁"

        block += (
            f"{icon} **{position}. "
            f"{player['username']}**\n"
            f"⏱️ `{player['time']}`\n\n"
        )

    return block


# ==================================================
# GŁÓWNY PROGRAM
# ==================================================

def main():

    check_webhook()

    print(
        "Pobieram aktualne Daily Race..."
    )

    events = get_current_daily_events()

    daily_order = [
        "Daily Race A",
        "Daily Race B",
        "Daily Race C"
    ]

    current_message = (
        "🏁 **AKTUALNE CZASY SRS**\n\n"
        "⏱️ Aktualne czasy kwalifikacyjne "
        "zawodników SRS\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    messages = []

    for event_name in daily_order:

        print(
            f"Sprawdzam: {event_name}"
        )

        if event_name not in events:

            event_block = (
                f"🏎️ **{event_name.upper()}**\n\n"
                "❌ Nie znaleziono aktualnego "
                "wydarzenia.\n\n"
            )

        else:

            event = events[event_name]

            try:

                track = get_event_track(
                    event
                )

                results = (
                    get_event_player_times(
                        event
                    )
                )

                event_block = (
                    create_daily_block(
                        event_name,
                        track,
                        results
                    )
                )

            except Exception as error:

                print(
                    f"Błąd {event_name}: "
                    f"{error}"
                )

                event_block = (
                    f"🏎️ **{event_name.upper()}**\n\n"
                    "❌ Błąd podczas pobierania "
                    "aktualnych czasów.\n\n"
                )

        event_block += (
            "━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        if (
            len(current_message)
            + len(event_block)
            > 1900
        ):

            messages.append(
                current_message
            )

            current_message = (
                "🏁 **AKTUALNE CZASY SRS "
                "— KOLEJNA CZĘŚĆ**\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
            )

        current_message += event_block

    current_message += (
        f"🕒 **Ostatnia aktualizacja:** "
        f"{datetime.now(ZoneInfo('Europe/Warsaw')).strftime('%d.%m.%Y %H:%M')}"
    )

    messages.append(
        current_message
    )


    # ==================================================
    # AKTUALIZACJA WIADOMOŚCI NA DISCORDZIE
    # ==================================================

    old_message_ids = load_message_ids()

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

            except Exception as error:

                print(
                    f"Błąd aktualizacji: "
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

    save_message_ids(
        new_message_ids
    )

    print(
        "Gotowe! Aktualne czasy SRS "
        "zostały zaktualizowane."
    )


if __name__ == "__main__":
    main()
