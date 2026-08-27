import os
import json
import time
import hashlib
import requests

from datetime import datetime
from zoneinfo import ZoneInfo

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
# POBIERANIE WYNIKÓW
# ==================================================

def get_player_events(page, psn):

    url = f"https://www.dg-edge.com/players/{psn}"

    response = page.goto(
        url,
        wait_until="domcontentloaded",
        timeout=60000
    )

    if response is None:
        print("⚠️ Brak odpowiedzi strony")
        return []

    if response.status == 404:

        print(
            f"⚠️ Nie znaleziono profilu: {psn}"
        )

        return []


    # Czekamy na JavaScript strony
    page.wait_for_timeout(4000)


    try:

        page.wait_for_load_state(
            "networkidle",
            timeout=15000
        )

    except Exception:
        pass


    # ==================================================
    # SZUKANIE PRAWDZIWYCH KART WYNIKÓW
    # ==================================================

    event_texts = page.evaluate(
        """
        () => {

            const allElements = Array.from(
                document.querySelectorAll(
                    "div, article, section, li"
                )
            );

            const candidates = [];

            for (const element of allElements) {

                const text = (
                    element.innerText || ""
                ).trim();

                const lower = text.toLowerCase();


                // Karta wyniku musi mieć
                // wszystkie najważniejsze dane
                const hasGlobal =
                    lower.includes("global");

                const hasCountry =
                    lower.includes("country");

                const hasImpact =
                    lower.includes("score impact");


                if (
                    !hasGlobal ||
                    !hasCountry ||
                    !hasImpact
                ) {
                    continue;
                }


                // Pomijamy zbyt krótkie
                if (text.length < 50) {
                    continue;
                }


                // Pomijamy ogromne kontenery strony
                if (text.length > 1500) {
                    continue;
                }


                candidates.push({
                    element,
                    text
                });
            }


            const smallest = [];


            for (const candidate of candidates) {

                let containsSmallerCandidate = false;


                for (
                    const other of candidates
                ) {

                    if (
                        candidate.element !== other.element &&
                        candidate.element.contains(
                            other.element
                        )
                    ) {

                        containsSmallerCandidate = true;
                        break;
                    }
                }


                if (
                    !containsSmallerCandidate
                ) {

                    smallest.push(
                        candidate.text
                    );
                }
            }


            return [
                ...new Set(smallest)
            ];
        }
        """
    )


    events = []


    for text in event_texts:

        cleaned_text = " ".join(
            text.split()
        )


        # Dodatkowe zabezpieczenie
        if len(cleaned_text) > 1500:
            continue


        event_id = hashlib.sha256(
            f"{psn}|{cleaned_text}".encode(
                "utf-8"
            )
        ).hexdigest()


        events.append({
            "id": event_id,
            "raw": cleaned_text
        })


    return events


# ==================================================
# FORMATOWANIE WIADOMOŚCI
# ==================================================

def format_event(username, raw):

    now = datetime.now(
        ZoneInfo("Europe/Warsaw")
    ).strftime(
        "%d.%m.%Y %H:%M"
    )


    # Maksymalna długość
    raw = raw[:1600]


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


                    print(
                        "📤 Wysłano na Discord"
                    )


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
