from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from app.middleware.auth import get_current_user
import logging

from app.services.crawler import simple_crawl_page

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

router = APIRouter()


@router.post("/crawl-and-ingest-single-page")
async def crawl_and_ingest_single_page(
    body: dict, current_user: dict = Depends(get_current_user)
):
    """
    Admin endpoint to trigger a simple crawl of a single URL and ingest its content.
    """
    if "url" not in body:
        raise HTTPException(status_code=400, detail="URL is required in request body")

    url = body["url"]
    if not url.startswith("https://altar.io"):
        raise HTTPException(
            status_code=400, detail="Invalid URL. Must start be a valid Altar.io URL."
        )

    try:
        result = await simple_crawl_page(url)
        print(result)
        return JSONResponse(
            content={"message": f"Successfully crawled and ingested content from {url}"}
        )
    except Exception as e:
        logging.error(f"Error during crawl and ingest: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to crawl and ingest {url}: {e}"
        )
