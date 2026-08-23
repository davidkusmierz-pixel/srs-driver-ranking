import requests
from bs4 import BeautifulSoup
import base64
import json
import re
import time

URL = "https://gtsh-rank.com/profile/"

# ==========================================
# LISTA KIEROWCÓW SRS
# ==========================================

KIEROWCY = [
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

# ==========================================
# SESJA
# ==========================================

session = requests.Session()

session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9"
})


# ==========================================
# ODSZYFROWANIE XOR
# ==========================================

def xor_decrypt(data, key):
    result = []

    for i, char in enumerate(data):
        result.append(
            chr(ord(char) ^ ord(key[i % len(key)]))
        )

    return "".join(result)


# ==========================================
# POBRANIE KLUCZA ZE STRONY
# ==========================================

def pobierz_klucz():

    print("=" * 60)
    print("POBIERAM STRONĘ GTSH")
    print("=" * 60)

    response = session.get(URL, timeout=30)

    print("STATUS:", response.status_code)

    if response.status_code != 200:
        print("BŁĄD POBIERANIA STRONY")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    body = soup.find("body")

    if not body:
        print("NIE ZNALEZIONO TAGU BODY")
        return None

    key = body.get("header")

    if not key:
        print("NIE ZNALEZIONO KLUCZA 'header'")
        return None

    print("ZNALEZIONO KLUCZ:", key[:15] + "...")

    return key


# ==========================================
# POBIERANIE PROFILU
# ==========================================

def pobierz_kierowce(psnid, key):

    print()
    print("=" * 60)
    print("POBIERAM:", psnid)
    print("=" * 60)

    try:

        response = session.post(
            URL,
            data={
                "psnid": psnid
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": URL,
                "Accept": "application/json, text/javascript, */*; q=0.01"
            },
            timeout=30
        )

        print("STATUS POST:", response.status_code)

        if response.status_code != 200:
            print("BŁĄD ODPOWIEDZI")
            return None

        try:
            response_data = response.json()

        except Exception as e:
            print("ODPOWIEDŹ NIE JEST JSON:")
            print(response.text[:500])
            return None

        if "error" in response_data:
            print("BŁĄD GTSH:", response_data["error"])
            return None

        if "data" not in response_data:
            print("BRAK POLA DATA")
            print(response_data)
            return None

        encrypted_base64 = response_data["data"]

        # BASE64 -> TEKST
        encrypted_bytes = base64.b64decode(encrypted_base64)

        # Javascript używa atob()
        encrypted_data = encrypted_bytes.decode(
            "latin-1",
            errors="ignore"
        )

        # XOR DECRYPT
        decrypted_data = xor_decrypt(
            encrypted_data,
            key
        )

        # JSON
        data = json.loads(decrypted_data)

        print("PROFIL POBRANY POPRAWNIE")

        return data

    except Exception as e:

        print("BŁĄD:", str(e))

        return None


# ==========================================
# ODCZYT DANYCH
# ==========================================

def odczytaj_dane(data):

    wynik = {
        "dr": "-",
        "sr": "-",
        "pk": 0,
        "zawody": 0
    }

    try:

        user = (
            data
            .get("monthly_stats", {})
            .get("result", {})
            .get("user", {})
        )

        driver_rating_mapping = {
            1: "E",
            2: "D",
            3: "C",
            4: "B",
            5: "A",
            6: "A+",
            7: "S"
        }

        sportsmanship_rating_mapping = {
            1: "E",
            2: "D",
            3: "C",
            4: "B",
            5: "A",
            6: "S"
        }

        driver_rating = user.get("driver_rating")

        wynik["dr"] = (
            driver_rating_mapping.get(
                driver_rating,
                user.get("dr_level", "-")
            )
        )

        sportsmanship_rating = user.get(
            "sportsmanship_rating"
        )

        wynik["sr"] = (
            sportsmanship_rating_mapping.get(
                sportsmanship_rating,
                "-"
            )
        )

        # PK / punkty DR
        wynik["pk"] = int(
            user.get("dr_points", 0) or 0
        )

        # Liczba zawodów
        summary = (
            data
            .get("stats", {})
            .get("summary", {})
        )

        wynik["zawody"] = int(
            summary.get("total_entries", 0) or 0
        )

    except Exception as e:

        print("BŁĄD ODCZYTU:", e)

    return wynik


# ==========================================
# TEST
# ==========================================

def main():

    key = pobierz_klucz()

    if not key:

        print()
        print("NIE UDAŁO SIĘ POBRAĆ KLUCZA.")
        return

    print()
    print("=" * 60)
    print("ROZPOCZYNAM POBIERANIE KIEROWCÓW")
    print("=" * 60)

    ranking = []

    for psnid in KIEROWCY:

        data = pobierz_kierowce(
            psnid,
            key
        )

        if data:

            dane = odczytaj_dane(data)

            print(
                f"WYNIK: {psnid} | "
                f"DR: {dane['dr']} | "
                f"SR: {dane['sr']} | "
                f"PK: {dane['pk']} | "
                f"Zawody: {dane['zawody']}"
            )

            ranking.append({
                "psnid": psnid,
                "dr": dane["dr"],
                "sr": dane["sr"],
                "pk": dane["pk"],
                "zawody": dane["zawody"]
            })

        else:

            print(
                f"NIE UDAŁO SIĘ POBRAĆ: {psnid}"
            )

        # Mała przerwa między kierowcami
        time.sleep(1)

    print()
    print("=" * 60)
    print("WYNIKI")
    print("=" * 60)

    for zawodnik in ranking:

        print(
            f"{zawodnik['psnid']} | "
            f"DR {zawodnik['dr']} | "
            f"SR {zawodnik['sr']} | "
            f"PK {zawodnik['pk']} | "
            f"Zawody {zawodnik['zawody']}"
        )

    print()
    print("=" * 60)
    print("GOTOWE")
    print("=" * 60)


if __name__ == "__main__":
    main()
