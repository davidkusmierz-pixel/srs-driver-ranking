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
    "demon23mor": "SRS Demon23mor"
}


# ==================================================
# USTAWIENIA
# ==================================================

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# PLIK Z ID WIADOMOŚCI RANKINGU
MESSAGE_IDS_FILE = "ranking_message_ids.txt"

# Maksymalny rozmiar wiadomości Discorda
MAX_MESSAGE_LENGTH = 1900


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
        rf"{re.escape(psn)}.*?\b([A-E]\+?|S)\s+([A-E]|S)\b",
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
    # PK
    # ==================================================

    pk = (
        pk_pfk_match.group(1)
        if pk_pfk_match
        else "?"
    )

    # ==================================================
    # PFK
    # ==================================================

    pfk = (
        pk_pfk_match.group(2)
        if pk_pfk_match
        else "?"
    )

    # ==================================================
    # SCORE
    # ==================================================

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

        print(
            f"Brak pliku {MESSAGE_IDS_FILE}"
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
# GŁÓWNY PROGRAM
# ==================================================

def main():

    print(
        "========== START RANKINGU =========="
    )


    # ==================================================
    # SPRAWDZENIE WEBHOOKA
    # ==================================================

    if (
        not WEBHOOK_URL
        or WEBHOOK_URL == "TU_WKLEJ_NOWY_WEBHOOK"
    ):

        print(
            "BŁĄD: Wklej webhook Discorda "
            "na początku kodu!"
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

            ranking.append(
                player
            )

        except Exception as error:

            print(
                f"BŁĄD {username}: {error}"
            )

            # Kierowca nadal zostaje w rankingu
            ranking.append({
                "username": username,
                "pk": "?",
                "pfk": "?",
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
    # ODWRÓCENIE KOLEJNOŚCI
    #
    # GÓRA:
    # 40
    # 39
    # 38
    # ...
    #
    # DÓŁ:
    # 3
    # 2
    # 1
    # ==================================================

    ranking.reverse()


    # ==================================================
    # STOPKA - TYLKO NA SAMYM DOLE
    # ==================================================

    update_time = datetime.now(
        ZoneInfo("Europe/Warsaw")
    ).strftime(
        "%d.%m.%Y %H:%M"
    )


    footer = (
        "━━━━━━━━━━━━━━━━━━━━\n\n"

        "🏎️ Każdy kierowca otrzymuje miejsce w rankingu "
        "zgodnie ze swoim aktualnym EDGE SCORE..\n\n"

        "📊 **Ranking SRS tworzony jest na podstawie "
        "danych z DG EDGE**\n\n"

        "🔄 Dane są automatycznie odświeżane, dzięki czemu "
        "ranking zawsze uwzględnia najnowsze wyniki z "
        "**DG EDGE**.\n\n"

        "━━━━━━━━━━━━━━━━━━━━\n"

        f"🕒 **Ostatnia aktualizacja:** {update_time}\n"

        "🏁 **RANKING GŁÓWNY SRS** 🏁"
    )


    # ==================================================
    # TWORZENIE CZĘŚCI RANKINGU
    # ==================================================

    messages = []

    current_message = "\u200b\n"

    message_number = 1


    for player in ranking:

        position = player["position"]


        # ==================================================
        # MEDAL
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
            f"{medal} **{position}. "
            f"{player['username']}**\n"

            f"🏅 PK **{player['pk']}** • "
            f"PFK **{player['pfk']}**\n"

            f"📊 PUNKTY: "
            f"**{player['score']:.2f}**\n\n"

            "━━━━━━━━━━━━━━━━━━━━\n\n"
        )


        # ==================================================
        # LIMIT DISCORDA
        # ==================================================

        if (
            len(current_message)
            + len(player_text)
            > MAX_MESSAGE_LENGTH
        ):

            messages.append(
                current_message
            )

            message_number += 1

            current_message = (
                f"🏁 **RANKING SRS — "
                f"CZĘŚĆ {message_number}**\n\n"

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
    # STOPKA NA SAMYM DOLE
    #
    # TYLKO OSTATNIA WIADOMOŚĆ
    # ==================================================

    messages[-1] += footer


    # ==================================================
    # ODCZYT STARYCH ID
    # ==================================================

    old_message_ids = load_message_ids()

    new_message_ids = []


    print(
        f"Znaleziono ID wiadomości: "
        f"{len(old_message_ids)}"
    )

    print(
        f"Liczba aktualnych części: "
        f"{len(messages)}"
    )


    # ==================================================
    # NADPISYWANIE / DODAWANIE
    #
    # NICZEGO NIE USUWAMY
    # ==================================================

    for number, message in enumerate(
        messages
    ):


        # ==================================================
        # ISTNIEJE ID - NADPISUJEMY
        # ==================================================

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
                    f"BŁĄD aktualizacji części "
                    f"{number + 1}: {error}"
                )

                print(
                    "Tworzę nową wiadomość "
                    "dla tej części..."
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
        # BRAK ID - DODAJEMY NOWĄ CZĘŚĆ
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
                    f"DODANO nową część "
                    f"{number + 1}/{len(messages)}"
                )

            except Exception as error:

                print(
                    f"BŁĄD wysyłania części "
                    f"{number + 1}: {error}"
                )


    # ==================================================
    # ZACHOWANIE STARYCH ID
    #
    # NIC NIE USUWAMY
    #
    # PRZYKŁAD:
    #
    # BYŁO:
    # CZĘŚĆ 1
    # CZĘŚĆ 2
    # CZĘŚĆ 3
    # CZĘŚĆ 4
    #
    # TERAZ:
    # CZĘŚĆ 1 -> NADPISANA
    # CZĘŚĆ 2 -> NADPISANA
    # CZĘŚĆ 3 -> NADPISANA
    # CZĘŚĆ 4 -> ZOSTAJE BEZ ZMIAN
    # ==================================================

    ids_to_save = old_message_ids.copy()


    for index, message_id in enumerate(
        new_message_ids
    ):

        if index < len(ids_to_save):

            ids_to_save[index] = message_id

        else:

            ids_to_save.append(
                message_id
            )


    # ==================================================
    # ZAPIS ID
    # ==================================================

    save_message_ids(
        ids_to_save
    )


    print(
        f"Zapisano ID w pliku: "
        f"{MESSAGE_IDS_FILE}"
    )


    print(
        "========== KONIEC =========="
    )


# ==================================================
# START
# ==================================================

if __name__ == "__main__":

    main()
