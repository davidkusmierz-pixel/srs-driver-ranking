import requests
import base64
import json
import time
from datetime import datetime


# ============================================================
# USTAWIENIA
# ============================================================

URL = "https://gtsh-rank.com/profile/"

PLAYERS = [
    "SolidSnakePoland",
    "ALF7",
    "lucekbks",
    "MTE_JaXoN_GT",
    "Przemo7117",
    "Dawid-y6q",
    "OliIgo1234",
    "MaddMikke992",
    "Chudinius47",
    "sajgon89",
    "DoMeme_21",
    "Tomas225566",
    "szymson70",
    "TastyLsD",
    "JankesKP",
    "BoloBagno",
    "GrandNoobPI",
    "adihanys85",
    "betterWanzzi",
    "ActiveShockPL",
    "Hrupek98",
    "Jaras_GD",
    "PRT_El_Chapo",
    "SRS-Tony-Montana",
    "demon23mor"
]

WAIT_SECONDS = 4


# ============================================================
# POMOCNICZE
# ============================================================

def line():
    print()
    print("=" * 60)


def xor_decrypt(data, key):
    key_bytes = key.encode("utf-8")

    decrypted = bytes(
        byte ^ key_bytes[index % len(key_bytes)]
        for index, byte in enumerate(data)
    )

    return decrypted.decode("utf-8")


def get_value(data, path, default=None):
    current = data

    for key in path:
        if not isinstance(current, dict):
            return default

        current = current.get(key)

        if current is None:
            return default

    return current


# ============================================================
# POBIERANIE KLUCZA
# ============================================================

def get_encryption_key(session):

    line()
    print("POBIERAM STRONĘ GTSH")
    line()

    response = session.get(URL, timeout=30)

    print(f"STATUS: {response.status_code}")

    if response.status_code != 200:
        print("BŁĄD: Nie udało się pobrać strony.")
        return None

    html = response.text

    marker = 'header="'

    if marker not in html:
        print("BŁĄD: Nie znaleziono klucza.")
        return None

    key_start = html.find(marker) + len(marker)
    key_end = html.find('"', key_start)

    key = html[key_start:key_end]

    if not key:
        print("BŁĄD: Klucz jest pusty.")
        return None

    print(f"ZNALEZIONO KLUCZ: {key[:15]}...")

    return key


# ============================================================
# ODSZYFROWANIE DANYCH
# ============================================================

def decrypt_response(encrypted_text, key):

    encrypted_data = base64.b64decode(encrypted_text)

    decrypted_text = xor_decrypt(
        encrypted_data,
        key
    )

    return json.loads(decrypted_text)


# ============================================================
# POBIERANIE JEDNEGO KIEROWCY
# ============================================================

def get_driver(session, player_name, key):

    line()
    print(f"POBIERAM: {player_name}")
    line()

    try:

        response = session.post(
            URL,
            data={
                "psnid": player_name
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            },
            timeout=30
        )

        print(f"STATUS POST: {response.status_code}")

        if response.status_code != 200:
            print("BŁĄD: Niepoprawny status serwera.")
            return None

        response_data = response.json()

        if response_data.get("error"):

            print(
                f"BŁĄD GTSH: "
                f"{response_data.get('error')}"
            )

            return None

        encrypted_data = response_data.get("data")

        if not encrypted_data:
            print("BŁĄD: Brak danych profilu.")
            return None

        data = decrypt_response(
            encrypted_data,
            key
        )

        print("PROFIL POBRANY POPRAWNIE")

        user = get_value(
            data,
            ["monthly_stats", "result", "user"],
            {}
        )

        if not isinstance(user, dict):
            user = {}

        driver_rating_mapping = {
            1: "E",
            2: "D",
            3: "C",
            4: "B",
            5: "A",
            6: "A+",
            7: "S"
        }

        driver_rating = user.get("driver_rating")

        dr = driver_rating_mapping.get(
            driver_rating,
            user.get("dr_level", "-")
        )

        sportsmanship_rating_mapping = {
            1: "E",
            2: "D",
            3: "C",
            4: "B",
            5: "A",
            6: "S"
        }

        sportsmanship_rating = user.get(
            "sportsmanship_rating"
        )

        sr = sportsmanship_rating_mapping.get(
            sportsmanship_rating,
            "-"
        )

        pk = user.get(
            "dr_points",
            0
        )

        if pk is None:
            pk = 0

        try:
            pk = int(pk)
        except (ValueError, TypeError):
            pk = 0

        summary = get_value(
            data,
            ["stats", "summary"],
            {}
        )

        if not isinstance(summary, dict):
            summary = {}

        races = summary.get(
            "total_entries",
            0
        )

        if races is None:
            races = 0

        try:
            races = int(races)
        except (ValueError, TypeError):
            races = 0

        result = {
            "name": player_name,
            "dr": dr,
            "sr": sr,
            "pk": pk,
            "races": races
        }

        print()
        print(
            f"WYNIK: {player_name} | "
            f"DR: {dr} | "
            f"SR: {sr} | "
            f"PK: {pk} | "
            f"Zawody: {races}"
        )

        return result

    except Exception as error:

        print(
            f"BŁĄD PODCZAS POBIERANIA "
            f"{player_name}: {error}"
        )

        return None


# ============================================================
# GŁÓWNY PROGRAM
# ============================================================

def main():

    session = requests.Session()

    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    })

    key = get_encryption_key(session)

    if not key:

        print()
        print("NIE UDAŁO SIĘ POBRAĆ KLUCZA.")

        return

    line()
    print("ROZPOCZYNAM POBIERANIE KIEROWCÓW")
    line()

    results = []

    total_players = len(PLAYERS)

    for index, player in enumerate(PLAYERS, start=1):

        print()
        print(f"KIEROWCA {index} / {total_players}")

        result = get_driver(
            session,
            player,
            key
        )

        if result:

            results.append(result)

        else:

            print(
                f"NIE UDAŁO SIĘ POBRAĆ: "
                f"{player}"
            )

        if index < total_players:

            print()
            print(
                f"Czekam {WAIT_SECONDS} sekundy..."
            )

            time.sleep(WAIT_SECONDS)

    results.sort(
        key=lambda driver: driver["pk"],
        reverse=True
    )

    for position, driver in enumerate(
        results,
        start=1
    ):
        driver["position"] = position

    line()
    print("WYNIKI KOŃCOWE")
    line()

    for driver in results:

        print(
            f"{driver['position']}. "
            f"{driver['name']} | "
            f"DR {driver['dr']} | "
            f"SR {driver['sr']} | "
            f"PK {driver['pk']} | "
            f"Zawody {driver['races']}"
        )

    now = datetime.now()

    update_date = now.strftime(
        "%d.%m.%Y %H:%M"
    )

    ranking_data = {
        "last_update": update_date,
        "drivers": results
    }

    with open(
        "ranking.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            ranking_data,
            file,
            ensure_ascii=False,
            indent=4
        )

    line()
    print("RANKING ZAPISANY DO PLIKU: ranking.json")
    print(f"DATA AKTUALIZACJI: {update_date}")
    line()

    print("GOTOWE")


# ============================================================
# START PROGRAMU
# ============================================================

if __name__ == "__main__":
    main()
