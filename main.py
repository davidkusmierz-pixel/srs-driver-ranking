import requests
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

    print("=" * 70)
    print("POBIERAM STRONĘ GTSH")
    print("=" * 70)

    response = requests.get(
        URL,
        headers=HEADERS,
        timeout=30
    )

    print("STATUS:", response.status_code)
    print("ADRES:", response.url)

    response.raise_for_status()

    html = response.text

    print("DŁUGOŚĆ HTML:", len(html))

    print("")
    print("=" * 70)
    print("SZUKAM FUNKCJI getProfile()")
    print("=" * 70)

    matches = list(
        re.finditer(
            r"function\s+getProfile\s*\(\s*\)",
            html,
            re.IGNORECASE
        )
    )

    print(
        "LICZBA ZNALEZIONYCH:",
        len(matches)
    )

    if not matches:

        print("")
        print("NIE ZNALEZIONO FUNKCJI getProfile()")

        return

    for number, match in enumerate(
        matches,
        start=1
    ):

        print("")
        print("=" * 70)
        print(
            f"FUNKCJA getProfile() — WYNIK {number}"
        )
        print("=" * 70)

        start = max(
            0,
            match.start() - 500
        )

        end = min(
            len(html),
            match.end() + 15000
        )

        fragment = html[start:end]

        print(fragment)

        print("")
        print("=" * 70)
        print("KONIEC FRAGMENTU")
        print("=" * 70)

    print("")
    print("=" * 70)
    print("DODATKOWO SZUKAM fetch()")
    print("=" * 70)

    fetch_matches = list(
        re.finditer(
            r"fetch\s*\(",
            html,
            re.IGNORECASE
        )
    )

    print(
        "LICZBA fetch():",
        len(fetch_matches)
    )

    for number, match in enumerate(
        fetch_matches[:10],
        start=1
    ):

        print("")
        print("-" * 70)
        print(
            f"FETCH {number}"
        )
        print("-" * 70)

        start = max(
            0,
            match.start() - 1000
        )

        end = min(
            len(html),
            match.end() + 5000
        )

        print(
            html[start:end]
        )

    print("")
    print("=" * 70)
    print("KONIEC TESTU")
    print("=" * 70)


if __name__ == "__main__":
    main()
