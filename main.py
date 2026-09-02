import os
import re
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo


# ==================================================
# DISCORD WEBHOOK
# ==================================================
# Możesz użyć GitHub Secret:
# DISCORD_WEBHOOK_URL
#
# Jeżeli nie używasz Secret, wpisz webhook poniżej.
# ==================================================

WEBHOOK_URL = os.getenv(
    "DISCORD_WEBHOOK_URL",
    "https://discord.com/api/webhooks/1540826456802992178/kCh8knUjF5cb1ZXGegpXEV4vNMHtjIFmEzTBx5iTrG_YgsEQ2ekMAhhcWPk40P895muo"
)


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
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0 Safari/537.36"
    ),
    "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.8"
}

MESSAGE_IDS_FILE = "ranking_message_ids.txt"

MAX_MESSAGE_LENGTH = 1900

REQUEST_ATTEMPTS = 3

RETRY_DELAY = 2


# ==================================================
# CZYSZCZENIE TEKSTU
# ==================================================

def normalize_text(value):

    if not value:
        return ""

    value = value.replace("\xa0", " ")

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip()


# ==================================================
# ODCZYT PK / PPK
# ==================================================

def extract_pk_ppk(text):

    """
    DG EDGE może pokazywać np.:

    A S Poland
    A S Gdańsk, Poland
    B A Lublin, Poland
    B+ A Kraków, Poland

    Pierwsza wartość = PK
    Druga wartość = PPK
    """

    patterns = [

        # Najczęstszy przypadek:
        # A S Gdańsk, Poland

        r"\b([A-E]\+?|S)\s+([A-E]\+?|S)\s+[^\n]{0,100}?\bPoland\b",

        # Jeżeli pomiędzy klasami i Poland
        # znajduje się więcej tekstu

        r"\b([A-E]\+?|S)\s+([A-E]\+?|S)\b[^\n]{0,150}?\bPoland\b",

        # W przypadku nietypowego formatowania HTML

        r"\b([A-E]\+?|S)[\s|/]+([A-E]\+?|S)[\s|/]+[^\n]{0,150}?\bPoland\b"
    ]


    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            return (
                match.group(1).upper(),
                match.group(2).upper()
            )


    # ==================================================
    # DODATKOWA METODA
    # ==================================================

    for match in re.finditer(
        r".{0,180}\bPoland\b",
        text,
        re.IGNORECASE
    ):

        fragment = match.group(0)

        classes = re.findall(
            r"\b(?:[A-E]\+?|S)\b",
            fragment,
            re.IGNORECASE
        )

        if len(classes) >= 2:

            return (
                classes[-2].upper(),
                classes[-1].upper()
            )


    return "?", "?"


# ==================================================
# ODCZYT EDGE SCORE
# ==================================================

def extract_score(text):

    patterns = [

        r"(\d{1,3}(?:\.\d{1,2})?)\s+Edge\s+Score\b",

        r"Edge\s+Score\s*[:\-]?\s*"
        r"(\d{1,3}(?:\.\d{1,2})?)",

        r"\bScore\s*[:\-]?\s*"
        r"(\d{1,3}(?:\.\d{1,2})?)"
    ]


    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            try:

                return float(
                    match.group(1)
                )

            except ValueError:

                pass


    return None


# ==================================================
# ODCZYT POZYCJI W POLSCE
# ==================================================

def extract_country_position(text):

    patterns = [

        r"([\d,\.]+)\s+Country\s+position\b",

        r"Country\s+position\s*[:\-]?\s*"
        r"([\d,\.]+)",

        r"([\d,\.]+)\s+Poland\b"
    ]


    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            try:

                return int(
                    re.sub(
                        r"[,\.]",
                        "",
                        match.group(1)
                    )
                )

            except ValueError:

                pass


    return None


# ==================================================
# POBIERANIE DANYCH Z DG EDGE
# ==================================================

def get_player(psn, username):

    url = (
        f"https://www.dg-edge.com/players/{psn}"
    )

    last_error = None


    # ==================================================
    # 3 PRÓBY POBRANIA PROFILU
    # ==================================================

    for attempt in range(
        1,
        REQUEST_ATTEMPTS + 1
    ):

        try:

            response = requests.get(
                url,
                headers=HEADERS,
                timeout=30
            )


            # ==================================================
            # PROFIL NIE ISTNIEJE
            # ==================================================

            if response.status_code == 404:

                raise RuntimeError(
                    "Profil DG EDGE nie istnieje (404)"
                )


            # ==================================================
            # ZA DUŻO ZAPYTAŃ
            # ==================================================

            if response.status_code == 429:

                raise RuntimeError(
                    "DG EDGE zwróciło 429 - "
                    "za dużo zapytań"
                )


            response.raise_for_status()


            # ==================================================
            # PARSOWANIE HTML
            # ==================================================

            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )


            text = normalize_text(
                soup.get_text(
                    " ",
                    strip=True
                )
            )


            if not text:

                raise RuntimeError(
                    "DG EDGE zwróciło pustą stronę"
                )


            # ==================================================
            # ODCZYT DANYCH
            # ==================================================

            pk, ppk = extract_pk_ppk(
                text
            )

            score = extract_score(
                text
            )

            country_position = (
                extract_country_position(
                    text
                )
            )


            # ==================================================
            # ZWRACAMY DANE
            # ==================================================

            return {

                "username": username,

                "psn": psn,

                "pk": pk,

                "ppk": ppk,

                "score": score,

                "country_position":
                    country_position,

                "url": url
            }


        except Exception as error:

            last_error = error


            print(
                f"  Próba {attempt}/"
                f"{REQUEST_ATTEMPTS} - "
                f"błąd: {error}"
            )


            if attempt < REQUEST_ATTEMPTS:

                time.sleep(
                    RETRY_DELAY
                )


    raise RuntimeError(
        str(last_error)
    )


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

def save_message_ids(
    message_ids
):

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

def send_discord_message(
    message
):

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

        f"{WEBHOOK_URL}/messages/"
        f"{message_id}",

        json={
            "content": message
        },

        timeout=30
    )


    response.raise_for_status()


# ==================================================
# WYCZYSZCZENIE STAREJ WIADOMOŚCI
# ==================================================

def clear_discord_message(
    message_id
):

    response = requests.patch(

        f"{WEBHOOK_URL}/messages/"
        f"{message_id}",

        json={
            "content": "\u200b"
        },

        timeout=30
    )


    response.raise_for_status()


# ==================================================
# TWORZENIE BLOKU KIEROWCY
# ==================================================

def create_player_block(
    player
):

    position = player[
        "position"
    ]


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
    # SCORE
    # ==================================================

    if player[
        "score"
    ] is None:

        score_text = "?"

    else:

        score_text = (
            f"{player['score']:.2f}"
        )


    # ==================================================
    # POZYCJA PL
    # ==================================================

    if player[
        "country_position"
    ] is None:

        country_position_text = "?"

    else:

        country_position_text = str(
            player[
                "country_position"
            ]
        )


    # ==================================================
    # BLOK
    # ==================================================

    return (

        f"{medal} "
        f"**{position}. "
        f"{player['username']}**\n"

        f"🏅 PK **{player['pk']}** • "
        f"PPK **{player['ppk']}**\n"

        f"📊 Score: "
        f"**{score_text}**\n"

        f"🇵🇱 Pozycja PL: "
        f"**{country_position_text}**\n\n"

        "━━━━━━━━━━━━━━━━━━━━\n\n"
    )


# ==================================================
# GŁÓWNY PROGRAM
# ==================================================

def main():

    print(
        "========== START RANKINGU =========="
    )


    print(
        "Liczba kierowców do sprawdzenia: "
        f"{len(PLAYERS)}"
    )


    # ==================================================
    # SPRAWDZENIE WEBHOOKA
    # ==================================================

    if (

        not WEBHOOK_URL

        or WEBHOOK_URL
        == "TU_WKLEJ_SWÓJ_WEBHOOK_DISCORDA"

    ):

        print(
            "BŁĄD: Wklej webhook Discorda "
            "lub ustaw DISCORD_WEBHOOK_URL!"
        )

        return


    ranking = []

    failed_players = []


    # ==================================================
    # POBIERANIE KAŻDEGO KIEROWCY
    # ==================================================

    for number, (
        psn,
        username
    ) in enumerate(
        PLAYERS.items(),
        start=1
    ):

        print(
            "----------------------------------"
        )


        print(
            f"[{number}/{len(PLAYERS)}] "
            f"Pobieram: {username}"
        )


        print(
            f"PSN: {psn}"
        )


        try:

            player = get_player(
                psn,
                username
            )


            print(
                f"  PK = {player['pk']} | "
                f"PPK = {player['ppk']} | "
                f"Score = {player['score']} | "
                f"PL = {player['country_position']}"
            )


            ranking.append(
                player
            )


        except Exception as error:

            print(
                f"  BŁĄD: {error}"
            )


            print(
                f"  URL: "
                f"https://www.dg-edge.com/"
                f"players/{psn}"
            )


            failed_players.append({

                "psn": psn,

                "username": username,

                "error": str(error)

            })


            # ==================================================
            # KIEROWCA NIE ZNIKA Z RANKINGU
            # ==================================================

            ranking.append({

                "username": username,

                "psn": psn,

                "pk": "?",

                "ppk": "?",

                "score": None,

                "country_position": None,

                "url":
                    f"https://www.dg-edge.com/"
                    f"players/{psn}"
            })


    # ==================================================
    # SORTOWANIE PO EDGE SCORE
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

        player[
            "position"
        ] = position


    # ==================================================
    # ODWRÓCENIE RANKINGU
    #
    # Najlepszy będzie na dole,
    # tak jak w poprzedniej wersji.
    # ==================================================

    ranking.reverse()


    # ==================================================
    # BLOKI KIEROWCÓW
    # ==================================================

    player_blocks = []


    for player in ranking:

        player_blocks.append(

            create_player_block(
                player
            )

        )


    # ==================================================
    # STOPKA
    # ==================================================

    update_time = datetime.now(

        ZoneInfo(
            "Europe/Warsaw"
        )

    ).strftime(
        "%d.%m.%Y %H:%M"
    )


    footer = (

        "🚗 Każdy kierowca otrzymuje "
        "miejsce w rankingu "
        "zgodnie ze swoim aktualnym "
        "EDGE SCORE.\n\n"

        "📊 **Ranking SRS tworzony jest "
        "na podstawie danych z DG EDGE**\n\n"

        "🇵🇱 Pozycja PL jest pobierana "
        "automatycznie z rankingu "
        "krajowego DG EDGE.\n\n"

        "🔄 Dane są automatycznie "
        "odświeżane, dzięki czemu "
        "ranking zawsze uwzględnia "
        "najnowsze wyniki z **DG EDGE**.\n\n"

        "━━━━━━━━━━━━━━━━━━━━\n"

        f"🕒 Ostatnia aktualizacja: "
        f"{update_time}\n"

        "🏁 **RANKING GŁÓWNY SRS** 🏁"
    )


    # ==================================================
    # DZIELENIE NA WIADOMOŚCI DISCORD
    # ==================================================

    messages = []


    current_message = (
        "\u200b\n"
    )


    for block in player_blocks:

        if (

            len(current_message)

            + len(block)

            > MAX_MESSAGE_LENGTH

        ):

            messages.append(
                current_message
            )


            current_message = (
                "\u200b\n"
            )


        current_message += block


    # ==================================================
    # OSTATNIA WIADOMOŚĆ + STOPKA
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
    # INFORMACJE KOŃCOWE
    # ==================================================

    print(
        "=================================="
    )


    print(
        f"Sprawdzono kierowców: "
        f"{len(PLAYERS)}"
    )


    print(
        f"Dodano do rankingu: "
        f"{len(ranking)}"
    )


    print(
        f"Błędy pobierania: "
        f"{len(failed_players)}"
    )


    # ==================================================
    # KIEROWCY Z BŁĘDAMI
    # ==================================================

    if failed_players:

        print(
            "----------------------------------"
        )


        print(
            "KIEROWCY Z BŁĘDAMI:"
        )


        for player in failed_players:

            print(

                f"- {player['username']} "

                f"({player['psn']}): "

                f"{player['error']}"

            )


    print(
        "=================================="
    )


    print(
        f"Liczba wiadomości Discord: "
        f"{len(messages)}"
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
    # STARE ID WIADOMOŚCI
    # ==================================================

    old_message_ids = (
        load_message_ids()
    )


    print(
        f"Starych ID wiadomości: "
        f"{len(old_message_ids)}"
    )


    # ==================================================
    # NOWE ID
    # ==================================================

    new_message_ids = []


    # ==================================================
    # AKTUALIZOWANIE / TWORZENIE
    # ==================================================

    for index, message in enumerate(
        messages
    ):


        # ==================================================
        # ISTNIEJE STARE ID
        # ==================================================

        if index < len(
            old_message_ids
        ):

            message_id = (
                old_message_ids[index]
            )


            try:

                update_discord_message(

                    message_id,

                    message

                )


                new_message_ids.append(
                    message_id
                )


                print(

                    f"OK - nadpisano "
                    f"część {index + 1}"

                )


            except Exception as error:

                print(

                    f"BŁĄD nadpisywania "
                    f"części {index + 1}: "
                    f"{error}"

                )


                # ==================================================
                # STARE ID NIE DZIAŁA
                # ==================================================

                try:

                    new_id = (
                        send_discord_message(
                            message
                        )
                    )


                    new_message_ids.append(
                        new_id
                    )


                    print(

                        f"Utworzono nową "
                        f"część {index + 1}"

                    )


                except Exception as send_error:

                    print(

                        f"BŁĄD wysyłania "
                        f"części {index + 1}: "
                        f"{send_error}"

                    )


        # ==================================================
        # BRAK STAREGO ID
        # ==================================================

        else:

            try:

                new_id = (
                    send_discord_message(
                        message
                    )
                )


                new_message_ids.append(
                    new_id
                )


                print(

                    f"OK - wysłano nową "
                    f"część {index + 1}"

                )


            except Exception as error:

                print(

                    f"BŁĄD wysyłania "
                    f"części {index + 1}: "
                    f"{error}"

                )


    # ==================================================
    # STARE DODATKOWE WIADOMOŚCI
    # ==================================================

    if (

        len(old_message_ids)

        > len(messages)

    ):

        for index in range(

            len(messages),

            len(old_message_ids)

        ):

            old_id = (
                old_message_ids[index]
            )


            try:

                clear_discord_message(
                    old_id
                )


                print(

                    f"Wyczyszczono starą "
                    f"część {index + 1}"

                )


            except Exception as error:

                print(

                    f"Nie można wyczyścić "
                    f"starej części "
                    f"{index + 1}: "
                    f"{error}"

                )


    # ==================================================
    # ZAPIS ID
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
