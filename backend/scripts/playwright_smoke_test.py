"""Playwright smoke test — verifies Chromium launches correctly.

Usage:
    python backend/scripts/playwright_smoke_test.py

This opens https://example.com in a visible browser, prints the page title,
waits 3 seconds, then closes.  It does NOT visit Instagram.
"""
import asyncio
import sys


async def main() -> None:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("FAIL — playwright is not installed.  Run:")
        print("  pip install -r requirements.txt")
        print("  playwright install chromium")
        sys.exit(1)

    print("Launching Chromium (visible) …")
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://example.com", wait_until="domcontentloaded")
        title = await page.title()
        print(f"Page title: {title}")
        await asyncio.sleep(3)
        await browser.close()

    if "Example" in title:
        print("PASS — Chromium launched and loaded example.com successfully.")
        sys.exit(0)
    else:
        print(f"FAIL — unexpected title: {title}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
