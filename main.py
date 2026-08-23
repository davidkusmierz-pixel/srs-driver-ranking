import requests
import re

URL = "https://gtsh-rank.com/profile/"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(
    URL,
    headers=HEADERS,
    timeout=30
)

html = response.text

print("STATUS:", response.status_code)
print("DŁUGOŚĆ HTML:", len(html))

keywords = [
    "function getProfile",
    "getProfile()",
    "getProfile",
    "fetch(",
    "XMLHttpRequest",
    "$.ajax",
    "/api/",
    "profile.php",
    "ajax"
]

for keyword in keywords:

    print("\n")
    print("=" * 70)
    print("SZUKAM:", keyword)
    print("=" * 70)

    matches = list(
        re.finditer(
            re.escape(keyword),
            html,
            re.IGNORECASE
        )
    )

    print("LICZBA ZNALEZIONYCH:", len(matches))

    for i, match in enumerate(matches[:10], start=1):

        start = max(0, match.start() - 1000)
        end = min(len(html), match.end() + 2000)

        print(f"\n--- WYNIK {i} ---\n")
        print(html[start:end])

print("\n")
print("=" * 70)
print("KONIEC TESTU")
print("=" * 70)
