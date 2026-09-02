import os
import re
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import quote


# ==================================================
# DISCORD WEBHOOK
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
    "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7"
}

MESSAGE_IDS_FILE = "ranking_message_ids.txt"

MAX_MESSAGE_LENGTH = 1900

REQUEST_ATTEMPTS = 3

RETRY_DELAY = 2

# DG EDGE ma obecnie około 7764 stron.
MAX_PLAYERS_PAGES = 7764

# Na jednej stronie jest 250 kierowców.
PLAYERS_PER_PAGE = 250


# ==================================================
# NORMALIZACJA
# ==================================================

def normalize_text(value):

    if not value:
        return ""

    value = value.replace(
        "\xa0",
        " "
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip()


# ==================================================
# POBIERANIE STRONY
# ==================================================

def download_page(url):

    last_error = None

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

            if response.status_code == 404:

                raise RuntimeError(
                    "Strona nie istnieje (404)"
                )

            if response.status_code == 429:

                raise RuntimeError(
                    "DG EDGE zwróciło 429"
                )

            response.raise_for_status()

            if not response.text.strip():

                raise RuntimeError(
                    "Pusta odpowiedź DG EDGE"
                )

            return response.text

        except Exception as error:

            last_error = error

            print(
                f"    Próba "
                f"{attempt}/{REQUEST_ATTEMPTS}: "
                f"{error}"
            )

            if attempt < REQUEST_ATTEMPTS:

                time.sleep(
                    RETRY_DELAY
                )

    raise RuntimeError(
        str(last_error)
    )


# ==================================================
# SCORE Z TEKSTU PROFILU
# ==================================================

def extract_score(text):

    text = normalize_text(
        text
    )

    patterns = [

        r"(\d{1,3}(?:\.\d{1,2})?)"
        r"\s+Edge\s+Score\b",

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
# POZYCJA PL Z PROFILU
# ==================================================

def extract_country_position(text):

    text = normalize_text(
        text
    )

    patterns = [

        r"([\d,\.]+)"
        r"\s+Country\s+position\b",

        r"Country\s+position"
        r"\s*[:\-]?\s*"
        r"([\d,\.]+)"

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
# PROFIL KIEROWCY
# ==================================================

def get_player_profile(
    psn,
    username
):

    url = (
        "https://www.dg-edge.com/players/"
        +
        quote(
            psn,
            safe=""
        )
    )

    html = download_page(
        url
    )

    soup = BeautifulSoup(
        html,
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
            "Profil zwrócił pusty tekst"
        )

    score = extract_score(
        text
    )

    country_position = (
        extract_country_position(
            text
        )
    )

    if score is None:

        raise RuntimeError(
            "Nie udało się odczytać Edge Score"
        )

    print(
        f"    Profil: "
        f"Score={score} | "
        f"PL={country_position}"
    )

    return {

        "username": username,

        "psn": psn,

        "score": score,

        "country_position":
            country_position,

        "url": url
    }


# ==================================================
# ODCZYT TABELI DG EDGE
# ==================================================

def parse_players_page(
    html,
    wanted_psn
):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )


    # --------------------------------------------------
    # Szukamy dokładnego linku:
    #
    # /players/OliIgo1234
    #
    # --------------------------------------------------

    wanted_path = (
        "/players/"
        +
        quote(
            wanted_psn,
            safe=""
        )
    )


    link = None


    for a in soup.find_all(
        "a",
        href=True
    ):

        href = a.get(
            "href",
            ""
        )

        href = href.split("?")[0]

        if href == wanted_path:

            link = a

            break


    # --------------------------------------------------
    # JEŚLI ZNALEZIONO KIEROWCĘ
    # --------------------------------------------------

    if link is not None:

        row = link.find_parent(
            "tr"
        )

        if row is not None:

            cells = row.find_all(
                "td"
            )

            row_text = normalize_text(
                row.get_text(
                    " ",
                    strip=True
                )
            )

            print(
                f"    Znaleziono kierowcę "
                f"{wanted_psn}"
            )

            print(
                f"    Wiersz: {row_text}"
            )


            # --------------------------------------------------
            # DR/SR
            #
            # Z tabeli DG EDGE:
            #
            # 27731 | A S | ... | Score
            #
            # Pierwsza = DR / PK
            # Druga = SR / PPK
            # --------------------------------------------------

            dr_sr_match = re.search(

                r"\b"
                r"(A\+|B\+|C\+|D\+|E\+|"
                r"A|B|C|D|E|S)"
                r"\s+"
                r"(A\+|B\+|C\+|D\+|E\+|"
                r"A|B|C|D|E|S)"
                r"\b",

                row_text,

                re.IGNORECASE
            )


            if dr_sr_match:

                pk = (
                    dr_sr_match
                    .group(1)
                    .upper()
                )

                ppk = (
                    dr_sr_match
                    .group(2)
                    .upper()
                )

                print(
                    f"    DR/SR z tabeli: "
                    f"{pk} {ppk}"
                )

                return pk, ppk


            # --------------------------------------------------
            # DODATKOWE SPRAWDZENIE KOMÓREK
            # --------------------------------------------------

            for cell in cells:

                cell_text = normalize_text(
                    cell.get_text(
                        " ",
                        strip=True
                    )
                )

                match = re.fullmatch(

                    r"(A\+|B\+|C\+|D\+|E\+|"
                    r"A|B|C|D|E|S)"
                    r"\s+"
                    r"(A\+|B\+|C\+|D\+|E\+|"
                    r"A|B|C|D|E|S)",

                    cell_text,

                    re.IGNORECASE
                )

                if match:

                    pk = (
                        match.group(1)
                        .upper()
                    )

                    ppk = (
                        match.group(2)
                        .upper()
                    )

                    print(
                        f"    DR/SR z komórki: "
                        f"{pk} {ppk}"
                    )

                    return pk, ppk


    return None, None


# ==================================================
# POBRANIE KONKRETNEJ STRONY
# ==================================================

def get_players_page(
    page_number
):

    url = (
        "https://www.dg-edge.com/players/page-"
        +
        str(page_number)
    )

    print(
        f"    Sprawdzam stronę DG EDGE: "
        f"{page_number}"
    )

    html = download_page(
        url
    )

    return html


# ==================================================
# SCORE PIERWSZEGO I OSTATNIEGO GRACZA
# ==================================================

def get_page_score_range(
    html
):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    rows = soup.find_all(
        "tr"
    )

    scores = []

    for row in rows:

        text = normalize_text(
            row.get_text(
                " ",
                strip=True
            )
        )

        match = re.search(

            r"\b"
            r"(\d{1,3}\.\d{1,2})"
            r"\s+"
            r"(?:hours?|days?|weeks?|"
            r"months?|years?|minutes?|"
            r"hour|day|week|month|year)"
            r"\s+ago\b",

            text,

            re.IGNORECASE
        )

        # Nie zawsze potrzebujemy tego sposobu.
        # Szukamy wszystkich wartości podobnych
        # do Score w wierszu.

        score_matches = re.findall(

            r"\b"
            r"(\d{1,3}\.\d{1,2})"
            r"\b",

            text
        )

        if score_matches:

            # Wiersz tabeli zawiera Score przed
            # "Last update". Bierzemy przedostatnią
            # sensowną liczbę dziesiętną.

            for value in score_matches:

                try:

                    number = float(
                        value
                    )

                    if (
                        0 <= number <= 100
                    ):

                        scores.append(
                            number
                        )

                except ValueError:

                    pass


    if not scores:

        return None, None


    return (
        scores[0],
        scores[-1]
    )


# ==================================================
# SZUKANIE KIEROWCY PO SCORE
#
# Lista DG EDGE jest posortowana malejąco
# po Score.
#
# Zamiast przeszukiwać tysiące stron,
# używamy wyszukiwania binarnego.
# ==================================================

def find_player_on_score_pages(
    psn,
    score
):

    # --------------------------------------------------
    # Najpierw przewidujemy stronę.
    #
    # To tylko punkt startowy.
    # --------------------------------------------------

    estimated_page = int(
        (100 - score)
        *
        100
    )

    if estimated_page < 1:

        estimated_page = 1

    if estimated_page > MAX_PLAYERS_PAGES:

        estimated_page = (
            MAX_PLAYERS_PAGES
        )


    print(
        f"    Przybliżona strona "
        f"dla Score {score}: "
        f"{estimated_page}"
    )


    # --------------------------------------------------
    # NIE polegamy tylko na przybliżeniu.
    #
    # Sprawdzamy najpierw stronę wynikającą
    # z przybliżenia oraz okolice.
    # --------------------------------------------------

    pages_to_check = []


    for offset in range(
        0,
        15
    ):

        left = (
            estimated_page
            -
            offset
        )

        right = (
            estimated_page
            +
            offset
        )

        if (
            left >= 1
            and
            left not in pages_to_check
        ):

            pages_to_check.append(
                left
            )

        if (
            right <= MAX_PLAYERS_PAGES
            and
            right not in pages_to_check
        ):

            pages_to_check.append(
                right
            )


    # --------------------------------------------------
    # Sprawdzamy strony.
    # --------------------------------------------------

    for page_number in pages_to_check:

        try:

            html = get_players_page(
                page_number
            )

            pk, ppk = (
                parse_players_page(
                    html,
                    psn
                )
            )

            if (
                pk is not None
                and
                ppk is not None
            ):

                return pk, ppk


        except Exception as error:

            print(
                f"    Błąd strony "
                f"{page_number}: "
                f"{error}"
            )


    # --------------------------------------------------
    # JEŚLI NIE ZNALEZIONO:
    #
    # Robimy pełne wyszukiwanie binarne.
    # --------------------------------------------------

    print(
        f"    Kierowcy nie znaleziono "
        f"w okolicy strony "
        f"{estimated_page}."
    )

    print(
        f"    Uruchamiam wyszukiwanie "
        f"binarne..."
    )


    low = 1

    high = (
        MAX_PLAYERS_PAGES
    )


    visited = set()


    while low <= high:

        middle = (
            low + high
        ) // 2


        if middle in visited:

            break


        visited.add(
            middle
        )


        try:

            html = get_players_page(
                middle
            )


            # --------------------------------------------------
            # Najpierw bezpośrednio szukamy PSN.
            # --------------------------------------------------

            pk, ppk = (
                parse_players_page(
                    html,
                    psn
                )
            )


            if (
                pk is not None
                and
                ppk is not None
            ):

                return pk, ppk


            # --------------------------------------------------
            # Odczytujemy Score strony.
            # --------------------------------------------------

            page_scores = (
                get_page_score_range(
                    html
                )
            )


            if (
                page_scores[0]
                is None
                or
                page_scores[1]
                is None
            ):

                # Jeśli nie da się określić zakresu,
                # sprawdzamy sąsiednie strony.

                break


            first_score = (
                page_scores[0]
            )

            last_score = (
                page_scores[1]
            )


            # --------------------------------------------------
            # Strona jest posortowana malejąco.
            # --------------------------------------------------

            if score > first_score:

                high = (
                    middle - 1
                )

            elif score < last_score:

                low = (
                    middle + 1
                )

            else:

                # Score znajduje się w zakresie strony.
                #
                # Sprawdzamy sąsiadujące strony,
                # ponieważ wiele osób może mieć
                # identyczny Score.

                for nearby_page in range(

                    max(
                        1,
                        middle - 10
                    ),

                    min(
                        MAX_PLAYERS_PAGES,
                        middle + 10
                    )
                    +
                    1

                ):

                    if nearby_page in visited:

                        continue

                    try:

                        nearby_html = (
                            get_players_page(
                                nearby_page
                            )
                        )

                        pk, ppk = (
                            parse_players_page(
                                nearby_html,
                                psn
                            )
                        )

                        if (
                            pk is not None
                            and
                            ppk is not None
                        ):

                            return pk, ppk

                    except Exception:

                        pass


                # Nie znaleziono.
                # Przesuwamy się dalej.

                low = (
                    middle + 1
                )


        except Exception as error:

            print(
                f"    Błąd wyszukiwania "
                f"strony {middle}: "
                f"{error}"
            )

            break


    return "?", "?"


# ==================================================
# PEŁNE DANE KIEROWCY
# ==================================================

def get_player(
    psn,
    username
):

    # --------------------------------------------------
    # PROFIL
    # --------------------------------------------------

    profile = get_player_profile(
        psn,
        username
    )


    # --------------------------------------------------
    # PK / PPK Z TABELI
    # --------------------------------------------------

    pk, ppk = (
        find_player_on_score_pages(
            psn,
            profile["score"]
        )
    )


    print(
        f"    KOŃCOWO: "
        f"PK={pk} | "
        f"PPK={ppk} | "
        f"Score={profile['score']} | "
        f"PL={profile['country_position']}"
    )


    return {

        "username":
            username,

        "psn":
            psn,

        "pk":
            pk,

        "ppk":
            ppk,

        "score":
            profile["score"],

        "country_position":
            profile[
                "country_position"
            ],

        "url":
            profile["url"]

    }


# ==================================================
# ID WIADOMOŚCI
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
# ZAPIS ID
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
# WYSŁANIE DISCORD
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

    return str(
        response.json()["id"]
    )


# ==================================================
# NADPISANIE DISCORD
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
# CZYSZCZENIE STAREJ WIADOMOŚCI
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
# BLOK KIEROWCY
# ==================================================

def create_player_block(
    player
):

    position = (
        player["position"]
    )


    if position == 1:

        medal = "🥇"

    elif position == 2:

        medal = "🥈"

    elif position == 3:

        medal = "🥉"

    else:

        medal = "🏁"


    if player["score"] is None:

        score_text = "?"

    else:

        score_text = (
            f"{player['score']:.2f}"
        )


    if (
        player["country_position"]
        is None
    ):

        country_position_text = "?"

    else:

        country_position_text = str(
            player["country_position"]
        )


    return (

        f"{medal} "
        f"**{position}. "
        f"{player['username']}**\n"

        f"🏅 PK **{player['pk']}** "
        f"• PPK **{player['ppk']}**\n"

        f"📊 Score: "
        f"**{score_text}**\n"

        f"🇵🇱 Pozycja PL: "
        f"**{country_position_text}**\n\n"

        "━━━━━━━━━━━━━━━━━━━━\n\n"

    )


# ==================================================
# MAIN
# ==================================================

def main():

    print(
        "========== START RANKINGU =========="
    )

    print(
        f"Liczba kierowców: "
        f"{len(PLAYERS)}"
    )


    # --------------------------------------------------
    # WEBHOOK
    # --------------------------------------------------

    if (
        not WEBHOOK_URL
        or
        WEBHOOK_URL
        ==
        "TU_WKLEJ_SWÓJ_WEBHOOK_DISCORDA"
    ):

        print(
            "BŁĄD: Wklej webhook Discorda!"
        )

        return


    ranking = []

    failed_players = []


    # ==================================================
    # KIEROWCY
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
            f"{username}"
        )

        print(
            f"PSN: {psn}"
        )


        try:

            player = get_player(
                psn,
                username
            )


            ranking.append(
                player
            )


        except Exception as error:

            print(
                f"  BŁĄD: {error}"
            )


            failed_players.append({

                "psn":
                    psn,

                "username":
                    username,

                "error":
                    str(error)

            })


            ranking.append({

                "username":
                    username,

                "psn":
                    psn,

                "pk":
                    "?",

                "ppk":
                    "?",

                "score":
                    None,

                "country_position":
                    None,

                "url":
                    f"https://www.dg-edge.com/"
                    f"players/"
                    f"{quote(psn, safe='')}"

            })


    # ==================================================
    # SORTOWANIE
    # ==================================================

    ranking.sort(

        key=lambda player: (

            player["score"] is not None,

            player["score"]
            if player["score"] is not None
            else 0

        ),

        reverse=True

    )


    # ==================================================
    # NUMERACJA
    # ==================================================

    for position, player in enumerate(

        ranking,

        start=1

    ):

        player[
            "position"
        ] = position


    # --------------------------------------------------
    # NAJLEPSZY NA DOLE
    # --------------------------------------------------

    ranking.reverse()


    # ==================================================
    # BLOKI
    # ==================================================

    player_blocks = [

        create_player_block(
            player
        )

        for player in ranking

    ]


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

        "🚗 Każdy kierowca otrzymuje miejsce "
        "w rankingu zgodnie ze swoim "
        "aktualnym EDGE SCORE.\n\n"

        "📊 **Ranking SRS tworzony jest "
        "na podstawie danych z DG EDGE**\n\n"

        "🇵🇱 Pozycja PL jest pobierana "
        "automatycznie z rankingu "
        "krajowego DG EDGE.\n\n"

        "🔄 Dane są automatycznie "
        "odświeżane, dzięki czemu ranking "
        "uwzględnia najnowsze wyniki "
        "z **DG EDGE**.\n\n"

        "━━━━━━━━━━━━━━━━━━━━\n"

        f"🕒 Ostatnia aktualizacja: "
        f"{update_time}\n"

        "🏁 **RANKING GŁÓWNY SRS** 🏁"

    )


    # ==================================================
    # DZIELENIE WIADOMOŚCI
    # ==================================================

    messages = []

    current_message = (
        "\u200b\n"
    )


    for block in player_blocks:

        if (
            len(current_message)
            +
            len(block)
            >
            MAX_MESSAGE_LENGTH
        ):

            messages.append(
                current_message
            )

            current_message = (
                "\u200b\n"
            )


        current_message += block


    if (
        len(current_message)
        +
        len(footer)
        <=
        MAX_MESSAGE_LENGTH
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
            +
            footer
        )


    # ==================================================
    # INFORMACJE
    # ==================================================

    print(
        "=================================="
    )

    print(
        f"Sprawdzono kierowców: "
        f"{len(PLAYERS)}"
    )

    print(
        f"W rankingu: "
        f"{len(ranking)}"
    )

    print(
        f"Błędy: "
        f"{len(failed_players)}"
    )

    print(
        f"Wiadomości Discord: "
        f"{len(messages)}"
    )


    # ==================================================
    # ID STARYCH WIADOMOŚCI
    # ==================================================

    old_message_ids = (
        load_message_ids()
    )

    print(
        f"Starych ID: "
        f"{len(old_message_ids)}"
    )


    new_message_ids = []


    # ==================================================
    # AKTUALIZACJA DISCORD
    # ==================================================

    for index, message in enumerate(
        messages
    ):

        if (
            index
            <
            len(old_message_ids)
        ):

            message_id = (
                old_message_ids[
                    index
                ]
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
                    f"Błąd nadpisywania "
                    f"części {index + 1}: "
                    f"{error}"
                )


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
                        f"Błąd wysyłania: "
                        f"{send_error}"
                    )


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
                    f"OK - wysłano "
                    f"część {index + 1}"
                )


            except Exception as error:

                print(
                    f"Błąd wysyłania "
                    f"części {index + 1}: "
                    f"{error}"
                )


    # ==================================================
    # CZYSZCZENIE STARYCH WIADOMOŚCI
    # ==================================================

    if (
        len(old_message_ids)
        >
        len(messages)
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
        f"Wysłano/nadpisano: "
        f"{len(new_message_ids)} części"
    )

    print(
        f"Kierowców: "
        f"{len(ranking)}"
    )

    print(
        "========== KONIEC =========="
    )


# ==================================================
# START
# ==================================================

if __name__ == "__main__":

    main()
