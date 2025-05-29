import logging
from bs4 import BeautifulSoup
import requests

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


async def simple_crawl_page(url: str) -> dict:
    """Basic web scraping for a single page."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        content_tags = soup.find_all(
            ["p", "h1", "h2", "h3", "li", "div"],
            class_=lambda x: x not in ["header", "footer", "nav", "sidebar"],
        )  # Customize selectors
        content = " ".join(
            [tag.get_text(separator=" ", strip=True) for tag in content_tags]
        )

        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else url

        logging.info(f"Crawled and extracted content from: {url}")
        return {"url": url, "title": title, "content": content}
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error crawling {url}: {e}")
        return {"url": url, "error": str(e), "content": ""}
    except Exception as e:
        logging.error(f"Error parsing content from {url}: {e}")
        return {"url": url, "error": str(e), "content": ""}
