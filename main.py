import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


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
    print("Adres:", response.url)

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    # ========================================
    # FORMULARZE
    # ========================================

    print("")
    print("========================================")
    print("ZNALEZIONE FORMULARZE")
    print("========================================")

    forms = soup.find_all("form")

    print("Liczba formularzy:", len(forms))

    for number, form in enumerate(forms, start=1):

        print("")
        print("----------------------------------------")
        print(f"FORMULARZ NR {number}")
        print("----------------------------------------")

        print(
            "ACTION:",
            form.get("action")
        )

        print(
            "METHOD:",
            form.get("method")
        )

        print(
            "ID:",
            form.get("id")
        )

        print(
            "CLASS:",
            form.get("class")
        )

        print("")
        print("CAŁY FORMULARZ:")
        print(form.prettify())

        print("")
        print("POLA FORMULARZA:")

        fields = form.find_all(
            [
                "input",
                "button",
                "select",
                "textarea"
            ]
        )

        for field in fields:

            print("")
            print(
                "TAG:",
                field.name
            )

            print(
                "TYPE:",
                field.get("type")
            )

            print(
                "NAME:",
                field.get("name")
            )

            print(
                "ID:",
                field.get("id")
            )

            print(
                "VALUE:",
                field.get("value")
            )

            print(
                "ONCLICK:",
                field.get("onclick")
            )

            print(
                "ONCHANGE:",
                field.get("onchange")
            )

            print(
                "CLASS:",
                field.get("class")
            )

    # ========================================
    # PRZYCISKI
    # ========================================

    print("")
    print("========================================")
    print("WSZYSTKIE PRZYCISKI")
    print("========================================")

    buttons = soup.find_all(
        ["button", "input"]
    )

    for button in buttons:

        button_text = button.get_text(
            " ",
            strip=True
        )

        value = button.get("value")

        button_type = button.get("type")

        if (
            button_text
            or value
        ):

            print("")
            print(
                "TEKST:",
                button_text
            )

            print(
                "VALUE:",
                value
            )

            print(
                "TYPE:",
                button_type
            )

            print(
                "ID:",
                button.get("id")
            )

            print(
                "NAME:",
                button.get("name")
            )

            print(
                "ONCLICK:",
                button.get("onclick")
            )

            print(
                "HTML:"
            )

            print(
                str(button)
            )

    # ========================================
    # SKRYPTY INLINE
    # ========================================

    print("")
    print("========================================")
    print("SKRYPTY INLINE")
    print("========================================")

    scripts = soup.find_all("script")

    inline_count = 0

    for number, script in enumerate(
        scripts,
        start=1
    ):

        # Pomijamy zewnętrzne JS
        if script.get("src"):

            continue

        script_text = script.get_text(
            "\n",
            strip=True
        )

        if not script_text:

            continue

        inline_count += 1

        print("")
        print("----------------------------------------")
        print(
            f"SKRYPT INLINE NR "
            f"{inline_count}"
        )
        print("----------------------------------------")

        print(script_text)

    print("")
    print("========================================")
    print("KONIEC TESTU")
    print("========================================")


if __name__ == "__main__":
    main()
