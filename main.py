import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re


URL = "https://gtsh-rank.com/profile/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/131.0.0.0 "
        "Safari/537.36"
    )
}


def main():

    print("========================================")
    print("POBIERAM STRONĘ GTSH PROFILE")
    print("========================================")

    response = requests.get(
        URL,
        headers=HEADERS,
        timeout=30
    )

    print("Status:", response.status_code)

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    # Wszystkie pliki JavaScript
    scripts = []

    for script in soup.find_all("script"):

        src = script.get("src")

        if src:

            script_url = urljoin(
                URL,
                src
            )

            scripts.append(script_url)

    print("")
    print("========================================")
    print("ZNALEZIONE PLIKI JAVASCRIPT")
    print("========================================")

    for script_url in scripts:

        print(script_url)

    print("")
    print("========================================")
    print("ANALIZA JAVASCRIPT")
    print("========================================")

    # Pobieranie każdego pliku JS
    for script_url in scripts:

        print("")
        print("----------------------------------------")
        print("PLIK:")
        print(script_url)
        print("----------------------------------------")

        try:

            js_response = requests.get(
                script_url,
                headers=HEADERS,
                timeout=30
            )

            print(
                "Status:",
                js_response.status_code
            )

            js_text = js_response.text

            # Szukamy słów związanych z API
            keywords = [
                "fetch(",
                "axios",
                "ajax",
                "XMLHttpRequest",
                "/api/",
                "profile",
                "player",
                "driver",
                "psn",
                "GET"
            ]

            for keyword in keywords:

                if keyword.lower() in js_text.lower():

                    print("")
                    print(
                        f"ZNALEZIONO SŁOWO: {keyword}"
                    )

                    # Wypisanie fragmentów
                    for match in re.finditer(
                        re.escape(keyword),
                        js_text,
                        re.IGNORECASE
                    ):

                        start = max(
                            0,
                            match.start() - 250
                        )

                        end = min(
                            len(js_text),
                            match.end() + 500
                        )

                        print("")
                        print(js_text[start:end])
                        print("")

        except Exception as error:

            print(
                "BŁĄD:",
                error
            )

    print("")
    print("========================================")
    print("KONIEC TESTU")
    print("========================================")


if __name__ == "__main__":
    main()
