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
        "Chrome/142.0 Safari/537.36"
    ),
    "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
}

MESSAGE_IDS_FILE = "ranking_message_ids.txt"
MAX_MESSAGE_LENGTH = 1900
REQUEST_ATTEMPTS = 3
RETRY_DELAY = 2


# ==================================================
# NORMALIZACJA TEKSTU
# ==================================================
def normalize_text(text):
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ==================================================
# PK / PPK
# ==================================================
def extract_pk_ppk(text):
    """
    Pobiera PK i PPK jako DWIE klasy obok siebie.

    NIE sprawdzamy:
    - Poland
    - PL
    - miasta
    - Gdańska
    - Lublina
    - nazwy użytkownika

    Przykłady:

        A S Gdańsk, Poland -> A / S
        C S Lublin, Poland -> C / S
        B A Poland         -> B / A
        A+ S Poland        -> A+ / S
    """

    text = normalize_text(text)

    patterns = [
        r"(?<![A-Za-z0-9+])([A-E]\+?|S)(?![A-Za-z0-9+])\s+"
        r"([A-E]\+?|S)(?![A-Za-z0-9+])",

        r"\b([A-E]\+?|S)\s+([A-E]\+?|S)\b",
    ]

    for pattern in patterns:
        matches = list(
            re.finditer(
                pattern,
                text,
                re.IGNORECASE
            )
        )

        if matches:
            for match in matches:
                pk = match.group(1).upper()
                ppk = match.group(2).upper()

                if pk in {
                    "A", "B", "C", "D", "E",
                    "A+", "B+", "C+", "D+", "E+", "S"
                }:
                    if ppk in {
                        "A", "B", "C", "D", "E",
                        "A+", "B+", "C+", "D+", "E+", "S"
                    }:
                        return pk, ppk

    return "?", "?"


# ==================================================
# EDGE SCORE
# ==================================================
def extract_score(text):
    text = normalize_text(text)

    patterns = [
        r"(\d{1,3}(?:\.\d{1,2})?)\s+Edge Score\b",
        r"Edge Score\s*:?\s*(\d{1,3}(?:\.\d{1,2})?)",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass

    return None


# ==================================================
# POZYCJA W POLSCE
# ==================================================
def extract_country_position(text):
    text = normalize_text(text)

    patterns = [
        r"([\d,]+)\s+Country position\b",
        r"Country position\s*:?\s*([\d,]+)",
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
                    match.group(1).replace(",", "")
                )
            except ValueError:
                pass

    return None


# ==================================================
# POBIERANIE DANYCH Z DG EDGE
# ==================================================
def get_player(psn, username):
    url = f"https://www.dg-edge.com/players/{psn}"

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
                    "Profil DG EDGE nie istnieje (404)."
                )

            if response.status_code == 429:
                raise RuntimeError(
                    "DG EDGE ograniczył liczbę zapytań (429)."
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

            text = normalize_text(text)

            pk, ppk = extract_pk_ppk(text)
            score = extract_score(text)
            country_position = extract_country_position(text)

            return {
                "username": username,
                "psn": psn,
                "pk": pk,
                "ppk": ppk,
                "score": score,
                "country_position": country_position,
                "url": url,
            }

        except Exception as error:
            last_error = error

            if attempt < REQUEST_ATTEMPTS:
                print(
                    f"  Próba {attempt}/{REQUEST_ATTEMPTS} "
                    f"nieudana: {error}"
                )

                time.sleep(RETRY_DELAY)

    raise RuntimeError(
        f"Nie udało się pobrać profilu po "
        f"{REQUEST_ATTEMPTS} próbach: {last_error}"
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
        or WEBHOOK_URL ==
        "TU_WKLEJ_SWÓJ_WEBHOOK_DISCORDA"
    ):

        print(
            "BŁĄD: Wklej webhook Discorda!"
        )

        return

    ranking = []
    failed_players = []

    # ==================================================
    # POBIERANIE KIEROWCÓW
    # ==================================================
    total = len(PLAYERS)

    for number, (psn, username) in enumerate(
        PLAYERS.items(),
        start=1
    ):

        print(
            f"[{number}/{total}] "
            f"Pobieram: {username}"
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
                f"  BŁĄD {username}: {error}"
            )

            failed_players.append(
                username
            )

            # Kierowca ZAWSZE zostaje w rankingu.
            ranking.append({
                "username": username,
                "psn": psn,
                "pk": "?",
                "ppk": "?",
                "score": None,
                "country_position": None,
                "url":
                    f"https://www.dg-edge.com/players/{psn}",
            })

    # ==================================================
    # SORTOWANIE PO EDGE SCORE
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

    # Najlepszy kierowca na dole.
    ranking.reverse()

    # ==================================================
    # TWORZENIE BLOKÓW KIEROWCÓW
    # ==================================================
    player_blocks = []

    for player in ranking:

        position = player["position"]

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
        if player["score"] is None:
            score_text = "?"

        else:
            score_text = (
                f"{player['score']:.2f}"
            )

        # ==================================================
        # POZYCJA PL
        # ==================================================
        if player["country_position"] is None:
            country_position_text = "?"

        else:
            country_position_text = str(
                player["country_position"]
            )

        # ==================================================
        # BLOK KIEROWCY
        # ==================================================
        block = (
            f"{medal} **{position}. "
            f"{player['username']}**\n"

            f"🏅 PK **{player['pk']}** • "
            f"PPK **{player['ppk']}**\n"

            f"📊 Score: **{score_text}**\n"

            f"🇵🇱 Pozycja PL: "
            f"**{country_position_text}**\n\n"

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
        "🚗 Każdy kierowca otrzymuje miejsce "
        "w rankingu zgodnie ze swoim aktualnym "
        "EDGE SCORE.\n\n"

        "📊 **Ranking SRS tworzony jest "
        "na podstawie danych z DG EDGE**\n\n"

        "🇵🇱 Pozycja PL jest pobierana automatycznie "
        "z rankingu krajowego DG EDGE.\n\n"

        "🔄 Dane są automatycznie odświeżane, "
        "dzięki czemu ranking zawsze uwzględnia "
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

    current_message = "\u200b\n"

    for block in player_blocks:

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
            "\u200b\n" + footer
        )

    # ==================================================
    # INFORMACJE
    # ==================================================
    print(
        "----------------------------------"
    )

    print(
        f"Liczba kierowców: {len(ranking)}"
    )

    print(
        f"Liczba wiadomości: {len(messages)}"
    )

    if failed_players:

        print(
            "----------------------------------"
        )

        print(
            "KIEROWCY Z BŁĘDEM:"
        )

        for username in failed_players:

            print(
                f" - {username}"
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
    old_message_ids = load_message_ids()

    print(
        f"Starych ID: {len(old_message_ids)}"
    )

    new_message_ids = []

    # ==================================================
    # AKTUALIZOWANIE / TWORZENIE
    # ==================================================
    for index, message in enumerate(
        messages
    ):

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
                    f"OK - nadpisano część "
                    f"{index + 1}"
                )

            except Exception as error:

                print(
                    f"BŁĄD nadpisywania części "
                    f"{index + 1}: {error}"
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
                        f"Utworzono nową część "
                        f"{index + 1}"
                    )

                except Exception as send_error:

                    print(
                        f"BŁĄD wysyłania: "
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
    # ==================================================
    if len(old_message_ids) > len(messages):

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
                    f"Wyczyszczono starą część "
                    f"{index + 1}"
                )

            except Exception as error:

                print(
                    f"Nie można wyczyścić "
                    f"starej części "
                    f"{index + 1}: {error}"
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
