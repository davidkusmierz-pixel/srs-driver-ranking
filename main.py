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
# PSN ID : NAZWA NA DISCORDZIE
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
    "GSR_Poke": "Poke",
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

MESSAGE_IDS_FILE = "ranking_message_ids.txt"

# Discord ma limit 2000 znaków.
# Zostawiamy zapas.
MAX_MESSAGE_LENGTH = 1900


# ==================================================
# POBIERANIE DANYCH Z DG EDGE
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


    # --------------------------------------------------
    # PK / PFK
    # --------------------------------------------------

    pk_pfk_match = re.search(
        rf"{re.escape(psn)}.*?\b([A-E]\+?|S)\s+([A-E]\+?|S)\b",
        text,
        re.IGNORECASE
    )


    # --------------------------------------------------
    # EDGE SCORE
    # --------------------------------------------------

    score_match = re.search(
        r"(\d{1,3}\.\d{1,2})\s+Edge Score",
        text,
        re.IGNORECASE
    )


    # --------------------------------------------------
    # POZYCJA W POLSCE
    # --------------------------------------------------

    country_position_match = re.search(
        r"([\d,]+)\s+Country position",
        text,
        re.IGNORECASE
    )


    pk = "?"
    pfk = "?"
    score = None
    country_position = None


    if pk_pfk_match:

        pk = pk_pfk_match.group(1)
        pfk = pk_pfk_match.group(2)


    if score_match:

        score = float(
            score_match.group(1)
        )


    if country_position_match:

        country_position = int(
            country_position_match.group(1).replace(",", "")
        )


    return {
        "username": username,
        "pk": pk,
        "pfk": pfk,
        "score": score,
        "country_position": country_position
    }


# ==================================================
# ODCZYT ID WIADOMOŚCI
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
# NOWA WIADOMOŚĆ
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

    data = response.json()

    return str(
        data["id"]
    )


# ==================================================
# NADPISANIE WIADOMOŚCI
# ==================================================

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
# WYCZYSZCZENIE STAREJ WIADOMOŚCI
#
# NIE USUWA WIADOMOŚCI.
# TYLKO ZMIENIA JEJ TREŚĆ NA PUSTĄ.
# ==================================================

def clear_discord_message(message_id):

    response = requests.patch(
        f"{WEBHOOK_URL}/messages/{message_id}",
        json={
            "content": "\u200b"
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
            "BŁĄD: Wklej webhook Discorda!"
        )

        return


    # ==================================================
    # RANKING
    # ==================================================

    ranking = []


    # ==================================================
    # POBIERANIE KAŻDEGO KIEROWCY
    # ==================================================

    for psn, username in PLAYERS.items():

        try:

            print(
                f"Pobieram: {username}"
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


            # Kierowca zostaje na liście,
            # ale bez fałszywego wyniku.

            ranking.append({
                "username": username,
                "pk": "?",
                "pfk": "?",
                "score": None,
                "country_position": None
            })


    # ==================================================
    # SORTOWANIE
    #
    # NAJLEPSZY = 1
    # ==================================================

    ranking.sort(
        key=lambda player: (
            player["score"] is not None,
            player["score"] or 0
        ),
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
    # ODWRÓCENIE
    #
    # GÓRA:
    # 41
    # 40
    # 39
    #
    # DÓŁ:
    # 3
    # 2
    # 1
    # ==================================================

    ranking.reverse()


    # ==================================================
    # TWORZENIE TEKSTÓW ZAWODNIKÓW
    # ==================================================

    player_blocks = []


    for player in ranking:

        position = player["position"]


        # --------------------------------------------------
        # MEDAL
        # --------------------------------------------------

        if position == 1:

            medal = "🥇"

        elif position == 2:

            medal = "🥈"

        elif position == 3:

            medal = "🥉"

        else:

            medal = "🏁"


        # --------------------------------------------------
        # SCORE
        # --------------------------------------------------

        if player["score"] is None:

            score_text = "?"

        else:

            score_text = f"{player['score']:.2f}"


        # --------------------------------------------------
        # POZYCJA PL
        # --------------------------------------------------

        if player["country_position"] is None:

            country_position_text = "?"

        else:

            country_position_text = str(
                player["country_position"]
            )


        # --------------------------------------------------
        # ZAWODNIK
        # --------------------------------------------------

        block = (
            f"{medal} **{position}. "
            f"{player['username']}**\n"

            f"🏅 PK **{player['pk']}** • "
            f"PFK **{player['pfk']}**\n"

            f"📊 Score: **{score_text}**\n"

            f"🇵🇱 Pozycja PL: **{country_position_text}**\n\n"

            "━━━━━━━━━━━━━━━━━━━━\n\n"
        )


        player_blocks.append(
            block
        )


    # ==================================================
    # STOPKA
    # ==================================================

    update_time = datetime.now(
        ZoneInfo("Europe/Warsaw")
    ).strftime(
        "%d.%m.%Y %H:%M"
    )


    footer = (
        "🚗 Każdy kierowca otrzymuje miejsce w rankingu "
        "zgodnie ze swoim aktualnym EDGE SCORE.\n\n"

        "📊 **Ranking SRS tworzony jest na podstawie danych z DG EDGE**\n\n"

        "🇵🇱 Pozycja PL jest pobierana automatycznie "
        "z rankingu krajowego DG EDGE.\n\n"

        "🔄 Dane są automatycznie odświeżane, dzięki czemu ranking "
        "zawsze uwzględnia najnowsze wyniki z **DG EDGE**.\n\n"

        "━━━━━━━━━━━━━━━━━━━━\n"

        f"🕒 Ostatnia aktualizacja: "
        f"{update_time}\n"

        "🏁 **RANKING GŁÓWNY SRS** 🏁"
    )


    # ==================================================
    # DZIELENIE NA WIADOMOŚCI
    #
    # KAŻDY KIEROWCA JEST DODANY.
    # NIE UCINAMY RANKINGU.
    # ==================================================

    messages = []

    current_message = "\u200b\n"


    for block in player_blocks:

        # Jeżeli kolejny kierowca przekroczyłby limit,
        # kończymy aktualną wiadomość.

        if (
            len(current_message)
            + len(block)
            > MAX_MESSAGE_LENGTH
        ):

            messages.append(
                current_message
            )

            current_message = "\u200b\n"


        current_message += block


    # ==================================================
    # OSTATNIA CZĘŚĆ
    # ==================================================

    if (
        len(current_message)
        + len(footer)
        <= MAX_MESSAGE_LENGTH
    ):

        current_message += footer

        messages.append(
            current_message
        )

    else:

        messages.append(
            current_message
        )

        messages.append(
            "\u200b\n"
            + footer
        )


    # ==================================================
    # SPRAWDZENIE
    # ==================================================

    print(
        f"Liczba kierowców: {len(ranking)}"
    )


    print(
        f"Liczba wiadomości: {len(messages)}"
    )


    for number, message in enumerate(
        messages,
        start=1
    ):

        print(
            f"Część {number}: "
            f"{len(message)} znaków"
        )


    # ==================================================
    # STARE ID
    # ==================================================

    old_message_ids = load_message_ids()


    print(
        f"Starych ID: "
        f"{len(old_message_ids)}"
    )


    # ==================================================
    # AKTUALNE ID
    # ==================================================

    new_message_ids = []


    # ==================================================
    # NADPISYWANIE ISTNIEJĄCYCH
    # LUB TWORZENIE NOWYCH
    # ==================================================

    for index, message in enumerate(
        messages
    ):


        # --------------------------------------------------
        # MAMY STARE ID
        # --------------------------------------------------

        if index < len(old_message_ids):

            message_id = old_message_ids[index]


            try:

                update_discord_message(
                    message_id,
                    message
                )


                new_message_ids.append(
                    message_id
                )


                print(
                    f"OK - nadpisano część "
                    f"{index + 1}"
                )


            except Exception as error:

                print(
                    f"BŁĄD nadpisywania części "
                    f"{index + 1}: {error}"
                )


                # Jeżeli stare ID nie działa,
                # tworzymy nową wiadomość.

                try:

                    new_id = send_discord_message(
                        message
                    )


                    new_message_ids.append(
                        new_id
                    )


                    print(
                        f"Utworzono nową część "
                        f"{index + 1}"
                    )


                except Exception as send_error:

                    print(
                        f"BŁĄD wysyłania: "
                        f"{send_error}"
                    )


        # --------------------------------------------------
        # BRAK ID - NOWA WIADOMOŚĆ
        # --------------------------------------------------

        else:

            try:

                new_id = send_discord_message(
                    message
                )


                new_message_ids.append(
                    new_id
                )


                print(
                    f"OK - wysłano nową część "
                    f"{index + 1}"
                )


            except Exception as error:

                print(
                    f"BŁĄD wysyłania części "
                    f"{index + 1}: {error}"
                )


    # ==================================================
    # STARE DODATKOWE WIADOMOŚCI
    #
    # JEŻELI WCZEŚNIEJ BYŁO NP. 5 CZĘŚCI,
    # A TERAZ SĄ 4:
    #
    # PIĄTA NIE ZOSTAJE ZE STARYM RANKINGIEM.
    #
    # ZOSTAJE W DISCORDZIE, ALE JEJ TREŚĆ
    # ZOSTAJE WYCZYSZCZONA.
    # ==================================================

    if len(old_message_ids) > len(messages):

        for index in range(
            len(messages),
            len(old_message_ids)
        ):

            old_id = old_message_ids[index]


            try:

                clear_discord_message(
                    old_id
                )


                print(
                    f"Wyczyszczono starą część "
                    f"{index + 1}"
                )


            except Exception as error:

                print(
                    f"Nie można wyczyścić "
                    f"starej części {index + 1}: "
                    f"{error}"
                )


    # ==================================================
    # ZAPIS ID
    #
    # ZAPISUJEMY TYLKO AKTUALNE CZĘŚCI.
    # ==================================================

    save_message_ids(
        new_message_ids
    )


    # ==================================================
    # KONIEC
    # ==================================================

    print(
        "----------------------------------"
    )


    print(
        f"Wysłano/nadpisano "
        f"{len(new_message_ids)} części."
    )


    print(
        f"W rankingu jest "
        f"{len(ranking)} kierowców."
    )


    print(
        "========== KONIEC =========="
    )


# ==================================================
# START
# ==================================================

if __name__ == "__main__":

    main()
