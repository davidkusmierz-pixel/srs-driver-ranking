import requests
import base64
import json
import time
from bs4 import BeautifulSoup


# ============================================
# USTAWIENIA
# ============================================

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

URL = "https://gtsh-rank.com/profile/"


# ============================================
# XOR DECRYPT
# ============================================

def xor_decrypt(data, key):
    result = ""

    for i, char in enumerate(data):
        result += chr(
            ord(char) ^ ord(key[i % len(key)])
        )

    return result


# ============================================
# BEZPIECZNE POBIERANIE DANYCH
# ============================================

def safe_get(data, path, default=None):

    current = data

    for key in path:

        if not isinstance(current, dict):
            return default

        current = current.get(key)

        if current is None:
            return default

    return current


# ============================================
# SESJA
# ============================================

session = requests.Session()

session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/120 Safari/537.36"
    )
})


# ============================================
# POBRANIE KLUCZA
# ============================================

print()
print("=" * 60)
print("POBIERAM STRONĘ GTSH")
print("=" * 60)

response = session.get(URL, timeout=30)

print("STATUS:", response.status_code)

if response.status_code != 200:
    print("BŁĄD POBIERANIA STRONY!")
    raise SystemExit()

soup = BeautifulSoup(response.text, "html.parser")

body = soup.find("body")

if body is None:
    print("BŁĄD: Nie znaleziono BODY")
    raise SystemExit()

KEY = body.get("header")

if not KEY:
    print("BŁĄD: Nie znaleziono klucza")
    raise SystemExit()

print("ZNALEZIONO KLUCZ:", KEY[:15] + "...")


# ============================================
# POBIERANIE PROFILU
# ============================================

def pobierz_profil(psn):

    print()
    print("=" * 60)
    print("POBIERAM:", psn)
    print("=" * 60)

    maks_prob = 3

    for proba in range(1, maks_prob + 1):

        try:

            response = session.post(
                URL,
                data={
                    "psnid": psn
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                timeout=30
            )

            print("STATUS POST:", response.status_code)

            dane_odpowiedzi = response.json()

        except Exception as e:

            print("BŁĄD POŁĄCZENIA:", e)

            if proba < maks_prob:

                print("Czekam 12 sekund...")
                time.sleep(12)

                continue

            return None

        # ========================================
        # BŁĄD GTSH
        # ========================================

        if dane_odpowiedzi.get("error"):

            blad = str(
                dane_odpowiedzi.get("error", "")
            )

            print("BŁĄD GTSH:", blad)

            if "Too many requests" in blad:

                if proba < maks_prob:

                    print()
                    print("LIMIT ZAPYTAŃ!")
                    print("Czekam 12 sekund...")
                    print(
                        f"PRÓBA: {proba + 1} / {maks_prob}"
                    )

                    time.sleep(12)

                    continue

            return None

        # ========================================
        # POBRANIE DANYCH
        # ========================================

        encrypted = dane_odpowiedzi.get("data")

        if not encrypted:

            print("BŁĄD: Brak pola DATA")

            return None

        # ========================================
        # ODKODOWANIE
        # ========================================

        try:

            encrypted_bytes = base64.b64decode(
                encrypted
            )

            encrypted_text = encrypted_bytes.decode(
                "latin-1"
            )

            decrypted = xor_decrypt(
                encrypted_text,
                KEY
            )

            data = json.loads(decrypted)

            print("PROFIL POBRANY POPRAWNIE")

            return data

        except Exception as e:

            print("BŁĄD ODKODOWANIA:", e)

            return None

    return None


# ============================================
# ODCZYT KIEROWCY
# ============================================

def odczytaj_kierowce(psn, data):

    if not isinstance(data, dict):

        return {
            "psn": psn,
            "dr": "-",
            "sr": "-",
            "pk": 0,
            "zawody": 0
        }

    # ========================================
    # USER
    # ========================================

    user = safe_get(
        data,
        [
            "monthly_stats",
            "result",
            "user"
        ],
        {}
    )

    if not isinstance(user, dict):
        user = {}

    # ========================================
    # DR
    # ========================================

    dr_map = {
        1: "E",
        2: "D",
        3: "C",
        4: "B",
        5: "A",
        6: "A+",
        7: "S"
    }

    dr_rating = user.get("driver_rating")

    dr = dr_map.get(
        dr_rating,
        user.get("dr_level", "-")
    )

    if not dr:
        dr = "-"

    # ========================================
    # SR
    # ========================================

    sr_map = {
        1: "E",
        2: "D",
        3: "C",
        4: "B",
        5: "A",
        6: "S"
    }

    sr_rating = user.get(
        "sportsmanship_rating"
    )

    sr = sr_map.get(
        sr_rating,
        "-"
    )

    # ========================================
    # PK
    # ========================================

    pk = user.get(
        "dr_points",
        0
    )

    if pk is None:
        pk = 0

    try:
        pk = int(pk)
    except:
        pk = 0

    # ========================================
    # ZAWODY
    # ========================================

    zawody = 0

    stats = data.get("stats")

    if isinstance(stats, dict):

        summary = stats.get("summary")

        if isinstance(summary, dict):

            # Główne pole
            zawody = summary.get(
                "total_entries"
            )

            # Alternatywne pola
            if zawody is None:
                zawody = summary.get(
                    "total_races"
                )

            if zawody is None:
                zawody = summary.get(
                    "races"
                )

            if zawody is None:
                zawody = 0

    try:
        zawody = int(zawody)
    except:
        zawody = 0

    return {
        "psn": psn,
        "dr": dr,
        "sr": sr,
        "pk": pk,
        "zawody": zawody
    }


# ============================================
# POBIERANIE WSZYSTKICH KIEROWCÓW
# ============================================

print()
print("=" * 60)
print("ROZPOCZYNAM POBIERANIE KIEROWCÓW")
print("=" * 60)

wyniki = []

for numer, psn in enumerate(
    KIEROWCY,
    start=1
):

    print()
    print(
        f"KIEROWCA {numer} / {len(KIEROWCY)}"
    )

    data = pobierz_profil(psn)

    if data is not None:

        kierowca = odczytaj_kierowce(
            psn,
            data
        )

        print()

        print(
            f"WYNIK: "
            f"{kierowca['psn']} | "
            f"DR: {kierowca['dr']} | "
            f"SR: {kierowca['sr']} | "
            f"PK: {kierowca['pk']} | "
            f"Zawody: {kierowca['zawody']}"
        )

        wyniki.append(kierowca)

    else:

        print(
            "NIE UDAŁO SIĘ POBRAĆ:",
            psn
        )

    # ========================================
    # PRZERWA MIĘDZY KIEROWCAMI
    # ========================================

    if numer < len(KIEROWCY):

        print()
        print("Czekam 4 sekundy...")
        time.sleep(4)


# ============================================
# SORTOWANIE WEDŁUG PK
# ============================================

wyniki.sort(
    key=lambda x: x["pk"],
    reverse=True
)


# ============================================
# WYNIKI
# ============================================

print()
print("=" * 60)
print("WYNIKI KOŃCOWE")
print("=" * 60)

for pozycja, kierowca in enumerate(
    wyniki,
    start=1
):

    print(
        f"{pozycja}. "
        f"{kierowca['psn']} | "
        f"DR {kierowca['dr']} | "
        f"SR {kierowca['sr']} | "
        f"PK {kierowca['pk']} | "
        f"Zawody {kierowca['zawody']}"
    )


print()
print("=" * 60)
print("GOTOWE")
print("=" * 60)
