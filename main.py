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
    "SolidSnakePoland": "RickyK",
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
    "demon23mor": "SRS Demon23mor",
}


# ==================================================
# USTAWIENIA
# ==================================================

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# OSOBNY PLIK TYLKO DLA RANKINGU
MESSAGE_IDS_FILE = "ranking_message_ids.txt"


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

    # ==================================================
    # PK I PFK
    # ==================================================

    pk_pfk_match = re.search(
        rf"{re.escape(psn)}.*?\b([A-E]\+?|S)\s+([A-E]\+?|S)\b",
        text,
        re.IGNORECASE
    )

    # ==================================================
    # EDGE SCORE
    # ==================================================

    score_match = re.search(
        r"(\d{1,3}\.\d{1,2})\s+Edge Score",
        text,
        re.IGNORECASE
    )

    # ==================================================
    # MIEJSCE W POLSCE
    # ==================================================

    country_match = re.search(
        r"(\d[\d,.]*)\s+Country\s+position",
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

    country = (
        country_match.group(1)
        if country_match
        else "?"
    )

    return {
        "username": username,
        "pk": pk,
        "pfk": pfk,
        "country": country,
        "score": score
    }


# ==================================================
# ODCZYT ID WIADOMOŚCI
# ==================================================

def load_message_ids():

    if not os.path.exists(MESSAGE_IDS_FILE):

        print(
            f"Brak pliku {MESSAGE_IDS_FILE} - "
            f"zostanie utworzony automatycznie."
        )

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

            file.write(
                f"{message_id}\n"
            )


# ==================================================
# WYSŁANIE NOWEJ WIADOMOŚCI
# ==================================================

def send_discord_message(message):

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

    response.raise_for_status()

    return str(
        response.json()["id"]
    )


# ==================================================
# NADPISANIE WIADOMOŚCI
# ==================================================

def update_discord_message(message_id, message):

    response = requests.patch(
        f"{WEBHOOK_URL}/messages/{message_id}",
        json={
            "content": message
        },
        timeout=30
    )

    response.raise_for_status()


# ==================================================
# USUNIĘCIE WIADOMOŚCI
# ==================================================

def delete_discord_message(message_id):

    response = requests.delete(
        f"{WEBHOOK_URL}/messages/{message_id}",
        timeout=30
    )

    response.raise_for_status()


# ==================================================
# GŁÓWNY PROGRAM
# ==================================================

def main():

    print("========== START RANKINGU ==========")

    if not WEBHOOK_URL or WEBHOOK_URL == "TU_WKLEJ_SWÓJ_WEBHOOK":

        print(
            "BŁĄD: Wklej webhook Discorda na początku kodu!"
        )

        return

    ranking = []


    # ==================================================
    # POBIERANIE WSZYSTKICH KIEROWCÓW
    # ==================================================

    for psn, username in PLAYERS.items():

        try:

            print(
                f"Pobieram dane: {username}"
            )

            player = get_player(
                psn,
                username
            )

            ranking.append(player)

        except Exception as error:

            print(
                f"BŁĄD {username}: {error}"
            )

            # ==================================================
            # JEŚLI DG EDGE NIE ODPOWIE,
            # KIEROWCA NADAL ZOSTAJE W RANKINGU
            # ==================================================

            ranking.append({
                "username": username,
                "pk": "?",
                "pfk": "?",
                "country": "?",
                "score": 0.0
            })


    # ==================================================
    # SORTOWANIE OD NAJLEPSZEGO
    # ==================================================

    ranking.sort(
        key=lambda x: x["score"],
        reverse=True
    )


    # ==================================================
    # NADANIE MIEJSC
    # ==================================================

    for position, player in enumerate(
        ranking,
        start=1
    ):

        player["position"] = position


    # ==================================================
    # ODWRÓCENIE RANKINGU
    #
    # NA GÓRZE:
    # 40
    # 39
    # 38
    # ...
    #
    # NA DOLE:
    # 3
    # 2
    # 1
    # ==================================================

    ranking.reverse()


    # ==================================================
    # TWORZENIE WIADOMOŚCI
    # ==================================================

    messages = []

    current_message = ""

    message_number = 1


    for player in ranking:

        position = player["position"]


        # ==================================================
        # EMOTIKONA MIEJSCA
        # ==================================================

        if position == 1:

            medal = "🥇"

        elif position == 2:

            medal = "🥈"

        elif position == 3:

            medal = "🥉"

        else:

            medal = "🏁"


        # ==================================================
        # ZAWODNIK
        # ==================================================

        player_text = (
            f"{medal} **{position}. {player['username']}**\n\n"
            f"🏅 PK: **{player['pk']}**   "
            f"PFK: **{player['pfk']}**\n"
            f"🇵🇱 PL  **{player['country']}**\n"
            f"📊 PUNKTY: **{player['score']:.2f}**\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
        )


        # ==================================================
        # LIMIT DISCORDA
        # ==================================================

        if len(current_message) + len(player_text) > 1900:

            messages.append(
                current_message
            )

            message_number += 1

            current_message = (
                f"🏁 **RANKING SRS — "
                f"CZĘŚĆ {message_number}** 🏁\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
            )


        current_message += player_text


    # ==================================================
    # DODANIE OSTATNIEJ CZĘŚCI
    # ==================================================

    if current_message:

        messages.append(
            current_message
        )


    # ==================================================
    # STOPKA
    #
    # BĘDZIE NA SAMYM DOLE,
    # POD 1. MIEJSCEM
    # ==================================================

    footer = (
        "🏎️ Każdy kierowca otrzymuje miejsce w rankingu "
        "zgodnie ze swoim aktualnym EDGE SCORE..\n\n"

        "📊 **Ranking SRS tworzony jest na podstawie "
        "danych z DG EDGE**\n\n"

        "🔄 Dane są automatycznie odświeżane, dzięki czemu "
        "ranking zawsze uwzględnia najnowsze wyniki z **DG EDGE**.\n\n"

        "━━━━━━━━━━━━━━━━━━━━\n"

        f"🕒 Ostatnia aktualizacja: "
        f"{datetime.now(ZoneInfo('Europe/Warsaw')).strftime('%d.%m.%Y %H:%M')}\n"

        "🏁 **RANKING GŁÓWNY SRS** 🏁"
    )


    # ==================================================
    # STOPKA TYLKO NA SAMYM DOLE
    # ==================================================

    messages[-1] += footer


    # ==================================================
    # ODCZYT STARYCH ID
    # ==================================================

    old_message_ids = load_message_ids()

    new_message_ids = []

    print(
        f"Stare części rankingu: "
        f"{len(old_message_ids)}"
    )

    print(
        f"Nowe części rankingu: "
        f"{len(messages)}"
    )


    # ==================================================
    # NADPISYWANIE ISTNIEJĄCYCH WIADOMOŚCI
    # ==================================================

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
                    f"NADPISANO część "
                    f"{number + 1}/{len(messages)}"
                )

            except requests.exceptions.HTTPError as error:

                print(
                    f"Nie można nadpisać wiadomości "
                    f"{message_id}: {error}"
                )

                try:

                    new_id = send_discord_message(
                        message
                    )

                    new_message_ids.append(
                        new_id
                    )

                    print(
                        f"Utworzono nową część: "
                        f"{new_id}"
                    )

                except Exception as send_error:

                    print(
                        f"BŁĄD wysyłania: "
                        f"{send_error}"
                    )


        # ==================================================
        # BRAK ID - TWORZY NOWĄ WIADOMOŚĆ
        # ==================================================

        else:

            try:

                new_id = send_discord_message(
                    message
                )

                new_message_ids.append(
                    new_id
                )

                print(
                    f"Wysłano nową część "
                    f"{number + 1}/{len(messages)}"
                )

            except Exception as error:

                print(
                    f"BŁĄD wysyłania części "
                    f"{number + 1}: {error}"
                )


    # ==================================================
    # USUWANIE STARYCH CZĘŚCI
    # JEŚLI TERAZ JEST ICH MNIEJ
    # ==================================================

    if len(old_message_ids) > len(messages):

        print(
            "Usuwam stare części rankingu..."
        )

        for old_id in old_message_ids[len(messages):]:

            try:

                delete_discord_message(
                    old_id
                )

                print(
                    f"Usunięto starą część: "
                    f"{old_id}"
                )

            except Exception as error:

                print(
                    f"Nie można usunąć wiadomości "
                    f"{old_id}: {error}"
                )


    # ==================================================
    # ZAPIS AKTUALNYCH ID
    # ==================================================

    save_message_ids(
        new_message_ids
    )

    print(
        f"Zapisano {len(new_message_ids)} "
        f"ID wiadomości rankingu."
    )

    print(
        "========== KONIEC =========="
    )


# ==================================================
# START
# ==================================================

if __name__ == "__main__":

    main()
