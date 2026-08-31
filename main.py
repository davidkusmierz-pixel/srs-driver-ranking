import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo

# ==================================================
# DISCORD WEBHOOK
# ==================================================

WEBHOOK_URL = "https://discord.com/api/webhooks/1540826456802992178/kCh8knUjF5cb1ZXGegpXEV4vNMHtjIFmEzTBx5iTrG_YgsEQ2ekMAhhcWPk40P895muo"


# ==================================================
# PSN ID : NAZWA WYŚWIETLANA NA DISCORDZIE
# ==================================================


PLAYERS = {
    
    SolidSnakePoland": "RickyK",
    "ALF7": "SRS ALF7_VR2",
    "lucekbks": "SRS-Popek",
    "MTE_JaXoN_GT": "@JaXoN_GT_YT",
    "Przemo7117": "SRS Borko",
    "Dawid-y6q": "SRS Dawid-y6q",
    "OliIgo1234": "SRS_skawa_gt7",
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
    "betterWanzzi": "SRS wnaz",
    "ActiveShockPL": "SRS-ActiveShock",
    "Hrupek98": "SRS-Hrupek98",
    "Jaras_GD": "Jaras_GD",
    "PRT_El_Chapo": "PRT_EL_CHAPO",
    "Piko88-Z": "NRT_Piko",
    "Wojtek_Kl69": "Wojtek_Kl",
    "zeusek22": "zeusek666",
    "jupiter977gaudy": "SRS Mario",
    "CUSTOM_PUNCH85": "SRS_CUSTOM PUNCH",
    "RRA_Tony": "Dawid_Tony11",
    "RM_Shifter": "D.Pawełka",
    "NormanPowerGT": "YT-NormanPowerGT",
    "destro2207": "Desmond",
    "apr_poke": "Poke",
    "HoseeMoralezz": "HoseeMoralezz",
    "Bogdan_Zastrzyk": "Zastrzyk",
    "Hour_BilonPro": "GreG_WrO70",
    "Ashish_PL": "Woocash_POL",
    "LOLOBERCIK": "LOLOBERCIK",
    "DIL_DORSZ": "DIL_DORSZ",
    "SRS-Tony-Montana": "SRS Tony Montana",
    "demon23mor": "SRS Demon23mor"
}


WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

MESSAGE_IDS_FILE = "message_ids.txt"


# ==================================================
# POBIERANIE DANYCH
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
# ODCZYT ID WIADOMOŚCI
# ==================================================

def load_message_ids():
    if not os.path.exists(MESSAGE_IDS_FILE):
        print("Brak pliku message_ids.txt")
        return []

    with open(
        MESSAGE_IDS_FILE,
        "r",
        encoding="utf-8"
    ) as file:
        return [
            line.strip()
            for line in file
            if line.strip().isdigit()
        ]


# ==================================================
# ZAPIS ID WIADOMOŚCI
# ==================================================

def save_message_ids(message_ids):
    with open(
        MESSAGE_IDS_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        for message_id in message_ids:
            file.write(f"{message_id}\n")


# ==================================================
# WYSŁANIE WIADOMOŚCI
# ==================================================

def send_discord_message(message):
    response = requests.post(
        WEBHOOK_URL,
        params={"wait": "true"},
        json={"content": message},
        timeout=30
    )

    response.raise_for_status()

    return str(
        response.json()["id"]
    )


# ==================================================
# AKTUALIZACJA WIADOMOŚCI
# ==================================================

def update_discord_message(message_id, message):
    response = requests.patch(
        f"{WEBHOOK_URL}/messages/{message_id}",
        json={"content": message},
        timeout=30
    )

    response.raise_for_status()


# ==================================================
# GŁÓWNY PROGRAM
# ==================================================

def main():
    print("========== START RANKINGU ==========")

    if not WEBHOOK_URL:
        print("BŁĄD: Brak DISCORD_WEBHOOK!")
        return

    ranking = []

    for psn, username in PLAYERS.items():
        try:
            print(f"Pobieram dane: {username}")

            player = get_player(
                psn,
                username
            )

            ranking.append(player)

        except Exception as error:
            print(
                f"BŁĄD {username}: {error}"
            )

    ranking.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    current_message = (
        "\u200b\n"
        "📈 **RANKING GŁÓWNY**\n\n"
        "🏁 Klasyfikacja według **EDGE SCORE**\n\n"
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
            f"{medal} **{i}. {player['username']}**\n"
            f"🏅 PK **{player['pk']}** • "
            f"PFK **{player['pfk']}**\n"
            f"📊 Score: **{player['score']:.2f}**\n\n"
        )

        if len(current_message) + len(player_text) > 1900:
            messages.append(current_message)

            message_number += 1

            current_message = (
                f"📈 **RANKING GŁÓWNY — "
                f"CZĘŚĆ {message_number}**\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
            )

        current_message += player_text

    if current_message:
        messages.append(current_message)

    messages[-1] += (
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🕒 **Ostatnia aktualizacja:** "
        f"{datetime.now(ZoneInfo('Europe/Warsaw')).strftime('%d.%m.%Y %H:%M')}"
    )

    old_message_ids = load_message_ids()
    new_message_ids = []

    print(
        f"Znaleziono ID wiadomości: "
        f"{len(old_message_ids)}"
    )

    for number, message in enumerate(messages):
        if number < len(old_message_ids):
            message_id = old_message_ids[number]

            try:
                update_discord_message(
                    message_id,
                    message
                )

                new_message_ids.append(
                    message_id
                )

                print(
                    f"Zaktualizowano część "
                    f"{number + 1}/{len(messages)}"
                )

            except Exception as error:
                print(
                    f"Błąd aktualizacji: {error}"
                )

                new_id = send_discord_message(
                    message
                )

                new_message_ids.append(
                    new_id
                )

        else:
            new_id = send_discord_message(
                message
            )

            new_message_ids.append(
                new_id
            )

            print(
                f"Wysłano dodatkową część "
                f"{number + 1}"
            )

    save_message_ids(new_message_ids)

    print("========== KONIEC ==========")


if __name__ == "__main__":
    main()
