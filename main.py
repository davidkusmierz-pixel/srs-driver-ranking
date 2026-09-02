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
        "Chrome/142.0 Safari/537.36"
    ),
    "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
}

MESSAGE_IDS_FILE = "ranking_message_ids.txt"
MAX_MESSAGE_LENGTH = 1900
REQUEST_ATTEMPTS = 3
RETRY_DELAY = 2

VALID_CLASSES = {
    "E", "D", "C", "B", "A", "S",
    "E+", "D+", "C+", "B+", "A+"
}

CLASS_PATTERN = r"(?:A\+|B\+|C\+|D\+|E\+|A|B|C|D|E|S)"

# ==================================================
# NORMALIZACJA
# ==================================================
def normalize_text(value):
    if not value:
        return ""
    value = value.replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()

# ==================================================
# PK / PPK
#
# DG EDGE pokazuje klasę kierowcy w profilu jako np.:
# A S Poland
# A S Gdańsk, Poland
# C S Poland
#
# Pierwsza klasa = PK/DR
# Druga klasa = PPK/SR
#
# Nie przeszukujemy tysięcy stron /players/page-X.
# Czytamy bezpośrednio profil danego kierowcy.
# ==================================================
def extract_pk_ppk(soup, full_text):
    patterns = [
        re.compile(
            rf"(?<![A-Za-z0-9+])({CLASS_PATTERN})\s+({CLASS_PATTERN})"
            rf"(?=\s+(?:[^\n,]{{1,80}}\s*,\s*)?Poland\b)",
            re.IGNORECASE,
        ),
        re.compile(
            rf"(?<![A-Za-z0-9+])({CLASS_PATTERN})\s+({CLASS_PATTERN})"
            rf"\s+[^\n]{{1,100}}?,\s*Poland\b",
            re.IGNORECASE,
        ),
    ]

    # Najpierw małe elementy HTML. To zapobiega złapaniu przypadkowego
    # "S A" z dalszej części całej strony.
    candidates = []
    for tag in soup.find_all(["h1", "h2", "div", "span", "p", "li", "section", "header"]):
        t = normalize_text(tag.get_text(" ", strip=True))
        if "Poland" in t and 1 <= len(t) <= 180:
            candidates.append(t)

    # Krótsze elementy mają pierwszeństwo.
    candidates.sort(key=len)

    for candidate in candidates:
        for pattern in patterns:
            match = pattern.search(candidate)
            if match:
                pk = match.group(1).upper()
                ppk = match.group(2).upper()
                if pk in VALID_CLASSES and ppk in VALID_CLASSES:
                    return pk, ppk

    # Fallback: profil może mieć cały blok jako jeden element.
    for pattern in patterns:
        match = pattern.search(full_text)
        if match:
            pk = match.group(1).upper()
            ppk = match.group(2).upper()
            if pk in VALID_CLASSES and ppk in VALID_CLASSES:
                return pk, ppk

    return "?", "?"

# ==================================================
# SCORE
# ==================================================
def extract_score(text):
    text = normalize_text(text)
    patterns = [
        r"(\d{1,3}(?:\.\d{1,2})?)\s+Edge\s+Score\b",
        r"Edge\s+Score\s*[:\-]?\s*(\d{1,3}(?:\.\d{1,2})?)",
        r"\bScore\s*[:\-]?\s*(\d{1,3}(?:\.\d{1,2})?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
    return None

# ==================================================
# POZYCJA PL
# ==================================================
def extract_country_position(text):
    text = normalize_text(text)
    patterns = [
        r"([\d,\.]+)\s+Country\s+position\b",
        r"Country\s+position\s*[:\-]?\s*([\d,\.]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return int(re.sub(r"[,\.]", "", match.group(1)))
            except ValueError:
                pass
    return None

# ==================================================
# POBIERANIE STRONY
# ==================================================
def download_page(url):
    last_error = None
    for attempt in range(1, REQUEST_ATTEMPTS + 1):
        try:
            response = requests.get(
                url,
                headers=HEADERS,
                timeout=30,
            )
            if response.status_code == 404:
                raise RuntimeError("Profil DG EDGE nie istnieje (404)")
            if response.status_code == 429:
                raise RuntimeError("DG EDGE zwróciło 429")
            response.raise_for_status()
            if not response.text.strip():
                raise RuntimeError("Pusta odpowiedź DG EDGE")
            return response.text
        except Exception as error:
            last_error = error
            print(f"    Próba {attempt}/{REQUEST_ATTEMPTS}: {error}")
            if attempt < REQUEST_ATTEMPTS:
                time.sleep(RETRY_DELAY)
    raise RuntimeError(str(last_error))

# ==================================================
# PROFIL KIEROWCY
# ==================================================
def get_player(psn, username):
    url = "https://www.dg-edge.com/players/" + quote(psn, safe="")
    html = download_page(url)
    soup = BeautifulSoup(html, "html.parser")
    text = normalize_text(soup.get_text(" ", strip=True))

    if not text:
        raise RuntimeError("Profil zwrócił pusty tekst")

    pk, ppk = extract_pk_ppk(soup, text)
    score = extract_score(text)
    country_position = extract_country_position(text)

    if score is None:
        raise RuntimeError("Nie udało się odczytać Edge Score")

    print(
        f"    PK={pk} | PPK={ppk} | "
        f"Score={score:.2f} | PL={country_position}"
    )

    return {
        "username": username,
        "psn": psn,
        "pk": pk,
        "ppk": ppk,
        "score": score,
        "country_position": country_position,
        "url": url,
    }

# ==================================================
# ID WIADOMOŚCI
# ==================================================
def load_message_ids():
    if not os.path.exists(MESSAGE_IDS_FILE):
        return []
    with open(MESSAGE_IDS_FILE, "r", encoding="utf-8") as file:
        return [line.strip() for line in file if line.strip().isdigit()]

def save_message_ids(message_ids):
    with open(MESSAGE_IDS_FILE, "w", encoding="utf-8") as file:
        for message_id in message_ids:
            file.write(f"{message_id}\n")

# ==================================================
# DISCORD
# ==================================================
def send_discord_message(message):
    response = requests.post(
        WEBHOOK_URL,
        params={"wait": "true"},
        json={"content": message},
        timeout=30,
    )
    response.raise_for_status()
    return str(response.json()["id"])

def update_discord_message(message_id, message):
    response = requests.patch(
        f"{WEBHOOK_URL}/messages/{message_id}",
        json={"content": message},
        timeout=30,
    )
    response.raise_for_status()

def clear_discord_message(message_id):
    response = requests.patch(
        f"{WEBHOOK_URL}/messages/{message_id}",
        json={"content": "\u200b"},
        timeout=30,
    )
    response.raise_for_status()

# ==================================================
# BLOK KIEROWCY
# ==================================================
def create_player_block(player):
    position = player["position"]
    if position == 1:
        medal = "🥇"
    elif position == 2:
        medal = "🥈"
    elif position == 3:
        medal = "🥉"
    else:
        medal = "🏁"

    score_text = "?" if player["score"] is None else f"{player['score']:.2f}"
    pl_text = "?" if player["country_position"] is None else str(player["country_position"])

    return (
        f"{medal} **{position}. {player['username']}**\n"
        f"🏅 PK **{player['pk']}** • PPK **{player['ppk']}**\n"
        f"📊 Score: **{score_text}**\n"
        f"🇵🇱 Pozycja PL: **{pl_text}**\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
    )

# ==================================================
# MAIN
# ==================================================
def main():
    print("========== START RANKINGU ==========")
    print(f"Liczba kierowców: {len(PLAYERS)}")

    if not WEBHOOK_URL or WEBHOOK_URL == "TU_WKLEJ_SWÓJ_WEBHOOK_DISCORDA":
        print("BŁĄD: Wklej webhook Discorda!")
        return

    ranking = []
    failed_players = []

    for number, (psn, username) in enumerate(PLAYERS.items(), start=1):
        print("----------------------------------")
        print(f"[{number}/{len(PLAYERS)}] {username}")
        print(f"PSN: {psn}")
        try:
            ranking.append(get_player(psn, username))
        except Exception as error:
            print(f"  BŁĄD: {error}")
            failed_players.append({"psn": psn, "username": username, "error": str(error)})
            ranking.append({
                "username": username,
                "psn": psn,
                "pk": "?",
                "ppk": "?",
                "score": None,
                "country_position": None,
                "url": f"https://www.dg-edge.com/players/{quote(psn, safe='')}",
            })

    ranking.sort(
        key=lambda player: (
            player["score"] is not None,
            player["score"] if player["score"] is not None else 0,
        ),
        reverse=True,
    )

    for position, player in enumerate(ranking, start=1):
        player["position"] = position

    ranking.reverse()

    player_blocks = [create_player_block(player) for player in ranking]

    update_time = datetime.now(ZoneInfo("Europe/Warsaw")).strftime("%d.%m.%Y %H:%M")

    footer = (
        "🚗 Każdy kierowca otrzymuje miejsce w rankingu zgodnie ze swoim aktualnym EDGE SCORE.\n\n"
        "📊 **Ranking SRS tworzony jest na podstawie danych z DG EDGE**\n\n"
        "🇵🇱 Pozycja PL jest pobierana automatycznie z rankingu krajowego DG EDGE.\n\n"
        "🔄 Dane są automatycznie odświeżane, dzięki czemu ranking uwzględnia najnowsze wyniki z **DG EDGE**.\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🕒 Ostatnia aktualizacja: {update_time}\n"
        "🏁 **RANKING GŁÓWNY SRS** 🏁"
    )

    messages = []
    current_message = "\u200b\n"

    for block in player_blocks:
        if len(current_message) + len(block) > MAX_MESSAGE_LENGTH:
            messages.append(current_message)
            current_message = "\u200b\n"
        current_message += block

    if len(current_message) + len(footer) <= MAX_MESSAGE_LENGTH:
        current_message += footer
        messages.append(current_message)
    else:
        messages.append(current_message)
        messages.append("\u200b\n" + footer)

    print("==================================")
    print(f"Sprawdzono kierowców: {len(PLAYERS)}")
    print(f"W rankingu: {len(ranking)}")
    print(f"Błędy: {len(failed_players)}")
    print(f"Wiadomości Discord: {len(messages)}")

    if failed_players:
        print("----------------------------------")
        print("KIEROWCY Z BŁĘDAMI:")
        for player in failed_players:
            print(f"- {player['username']} ({player['psn']}): {player['error']}")

    old_message_ids = load_message_ids()
    print(f"Starych ID: {len(old_message_ids)}")

    new_message_ids = []

    for index, message in enumerate(messages):
        if index < len(old_message_ids):
            message_id = old_message_ids[index]
            try:
                update_discord_message(message_id, message)
                new_message_ids.append(message_id)
                print(f"OK - nadpisano część {index + 1}")
            except Exception as error:
                print(f"Błąd nadpisywania części {index + 1}: {error}")
                try:
                    new_id = send_discord_message(message)
                    new_message_ids.append(new_id)
                    print(f"Utworzono nową część {index + 1}")
                except Exception as send_error:
                    print(f"Błąd wysyłania: {send_error}")
        else:
            try:
                new_id = send_discord_message(message)
                new_message_ids.append(new_id)
                print(f"OK - wysłano część {index + 1}")
            except Exception as error:
                print(f"Błąd wysyłania części {index + 1}: {error}")

    if len(old_message_ids) > len(messages):
        for index in range(len(messages), len(old_message_ids)):
            try:
                clear_discord_message(old_message_ids[index])
                print(f"Wyczyszczono starą część {index + 1}")
            except Exception as error:
                print(f"Nie można wyczyścić starej części {index + 1}: {error}")

    save_message_ids(new_message_ids)

    print("----------------------------------")
    print(f"Wysłano/nadpisano: {len(new_message_ids)} części")
    print(f"Kierowców: {len(ranking)}")
    print("========== KONIEC ==========")


if __name__ == "__main__":
    main()
