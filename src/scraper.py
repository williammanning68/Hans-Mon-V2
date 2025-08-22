import requests
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin, urlparse

BASE_URL = "https://hansard.parliament.uk/search/Contributions"

def fetch_txt_for_date(date: str) -> None:
    """Download all Hansard text files for a given date.

    Parameters
    ----------
    date : str
        Date in ``YYYY-MM-DD`` format.
    """
    params = {"startDate": date, "endDate": date}
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    txt_links = {
        urljoin(BASE_URL, a["href"])
        for a in soup.find_all("a", href=lambda h: h and ".txt" in h)
    }

    output_dir = Path("data") / date
    output_dir.mkdir(parents=True, exist_ok=True)

    for link in txt_links:
        filename = Path(urlparse(link).path).name or "download.txt"
        filepath = output_dir / filename
        if filepath.exists():
            continue
        file_resp = requests.get(link)
        file_resp.raise_for_status()
        filepath.write_bytes(file_resp.content)
