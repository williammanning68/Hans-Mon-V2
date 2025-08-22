#!/usr/bin/env python3
"""Download Hansard transcripts from Tasmanian Parliament search site.

This script uses Playwright to perform a search on the Hansard page and
attempts to download the resulting transcript as a text file. The script is
intended to run inside a GitHub Action where CORS restrictions are not an
issue.

Usage:
    python download_transcript.py "House of Assembly Tuesday 19 August 2025"
"""
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

ROOT = Path(__file__).parent.resolve()
DOWNLOAD_DIR = ROOT / "transcripts"
DOWNLOAD_DIR.mkdir(exist_ok=True)

def sanitise_filename(name: str) -> str:
    """Return a safe filename derived from the search query."""
    safe = re.sub(r"[^a-zA-Z0-9._-]", "_", name)
    return f"{safe}.txt"

def download_transcript(query: str) -> None:
    url = "https://search.parliament.tas.gov.au/adv/hahansard"
    filename = sanitise_filename(query)
    output_path = DOWNLOAD_DIR / filename

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.goto(url)

        # The search input may differ; attempt site-specific and generic selectors.
        selectors = [
            "#full-query",
            "input[name='q[full-query]']",
            "input[name='q-full-query']",
            "input[name='q']",
            "input[name='Query']",
            "input[type='search']",
            "#search",
        ]
        for selector in selectors:
            try:
                page.wait_for_selector(selector, timeout=10000)
                page.fill(selector, query)
                break
            except PlaywrightTimeoutError:
                continue
        else:
            raise RuntimeError("Search input not found; update selectors")

        # Submit the search.
        page.keyboard.press("Enter")

        # Wait for results and attempt to find a TXT download link.
        link = page.locator("a:has-text('TXT')").first
        link.wait_for(timeout=15000)

        with page.expect_download() as download_info:
            link.click()
        download = download_info.value
        download.save_as(output_path)
        print(f"Saved to {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: download_transcript.py <search query>")
        sys.exit(1)
    download_transcript(sys.argv[1])
