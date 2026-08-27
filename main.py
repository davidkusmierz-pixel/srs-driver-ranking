import os
import requests


# ==========================================
# USTAWIENIA
# ==========================================

WEBHOOK_URL = os.getenv("https://discord.com/api/webhooks/1540826456802992178/kCh8knUjF5cb1ZXGegpXEV4vNMHtjIFmEzTBx5iTrG_YgsEQ2ekMAhhcWPk40P895muo")

MESSAGE_IDS_FILE = "message_ids.txt"


# ==========================================
# START
# ==========================================

print("==========================================")
print("START TESTU")
print("URUCHOMIONO MAIN.PY")
print("==========================================")


# ==========================================
# SPRAWDZENIE WEBHOOKA
# ==========================================

if WEBHOOK_URL:
    print("WEBHOOK: OK")
else:
    print("WEBHOOK: BRAK!")


# ==========================================
# ZAPIS TESTOWEGO ID
# ==========================================

test_message_id = "123456789012345678"

print("")
print("ZAPISUJĘ TESTOWE ID...")
print(f"ID: {test_message_id}")

with open(
    MESSAGE_IDS_FILE,
    "w",
    encoding="utf-8"
) as file:

    file.write(
        test_message_id + "\n"
    )


# ==========================================
# SPRAWDZENIE CZY PLIK ISTNIEJE
# ==========================================

print("")
print("SPRAWDZAM PLIK...")

if os.path.exists(
    MESSAGE_IDS_FILE
):

    print("PLIK ISTNIEJE")

    print(
        f"ROZMIAR: "
        f"{os.path.getsize(MESSAGE_IDS_FILE)} bajtów"
    )

    with open(
        MESSAGE_IDS_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        content = file.read()

    print(
        f"ZAWARTOŚĆ: {content}"
    )

else:

    print("BŁĄD: PLIK NIE ISTNIEJE!")


# ==========================================
# TEST DISCORDA
# ==========================================

if WEBHOOK_URL:

    try:

        print("")
        print(
            "WYSYŁAM TESTOWĄ WIADOMOŚĆ..."
        )

        response = requests.post(
            WEBHOOK_URL,
            params={
                "wait": "true"
            },
            json={
                "content": (
                    "🧪 **TEST SRS RANKING**\n"
                    "Sprawdzanie zapisu ID wiadomości."
                )
            },
            timeout=30
        )

        print(
            f"STATUS DISCORD: "
            f"{response.status_code}"
        )

        print(
            f"ODPOWIEDŹ: "
            f"{response.text}"
        )

        if response.status_code in (
            200,
            204
        ):

            print(
                "WIADOMOŚĆ TESTOWA WYSŁANA!"
            )

        else:

            print(
                "BŁĄD WYSYŁANIA!"
            )

    except Exception as error:

        print(
            f"BŁĄD DISCORD: {error}"
        )


# ==========================================
# KONIEC
# ==========================================

print("")
print("==========================================")
print("KONIEC TESTU")
print("==========================================")
