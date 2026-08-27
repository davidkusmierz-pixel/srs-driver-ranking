from playwright.sync_api import sync_playwright


PSN = "Tomas225566"


def main():

    print("========== TEST DG EDGE ==========")

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True
        )

        page = browser.new_page()

        url = (
            f"https://www.dg-edge.com/players/{PSN}"
        )

        print(f"Otwieram: {url}")

        page.goto(
            url,
            wait_until="networkidle",
            timeout=60000
        )

        # Czekamy na dodatkowe dane
        page.wait_for_timeout(5000)

        # Pobieramy cały tekst strony
        body_text = page.locator(
            "body"
        ).inner_text()

        # Zapisujemy do pliku
        with open(
            "debug_tomasz.txt",
            "w",
            encoding="utf-8"
        ) as file:

            file.write(body_text)

        print("")
        print(
            "Zapisano debug_tomasz.txt"
        )

        print("")
        print(
            "Długość tekstu:",
            len(body_text)
        )

        print("")

        if "Events results" in body_text:
            print(
                "✓ ZNALEZIONO: Events results"
            )
        else:
            print(
                "✗ BRAK: Events results"
            )

        if "GLOBAL" in body_text.upper():
            print(
                "✓ ZNALEZIONO: GLOBAL"
            )
        else:
            print(
                "✗ BRAK: GLOBAL"
            )

        if "COUNTRY" in body_text.upper():
            print(
                "✓ ZNALEZIONO: COUNTRY"
            )
        else:
            print(
                "✗ BRAK: COUNTRY"
            )

        if "Score Impact" in body_text:
            print(
                "✓ ZNALEZIONO: Score Impact"
            )
        else:
            print(
                "✗ BRAK: Score Impact"
            )

        browser.close()

    print("")
    print("========== KONIEC TESTU ==========")


if __name__ == "__main__":
    main()
