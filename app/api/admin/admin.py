from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from app.database.connection import get_pgvector_store
from app.middleware.auth import get_current_user
import logging
from langchain_core.documents import Document
from app.models.crawl_request import CrawlRequest
from app.services.rag import rag_service
from app.services.crawler.crawler import simple_crawl_page
from langchain_text_splitters import RecursiveCharacterTextSplitter

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

router = APIRouter()


@router.post("/crawl-and-ingest-pages")
async def crawl_and_ingest_pages(
    body: CrawlRequest, current_user: dict = Depends(get_current_user)
):
    """
    Admin endpoint to trigger crawling of multiple URLs and ingest their content.
    """
    invalid_urls = [
        url for url in body.urls if not str(url).find("altar.io")
    ]
    if invalid_urls:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid URLs found. All URLs must be valid Altar.io URLs: {invalid_urls}",
        )

    results = []
    failed_urls = []
    pgvector_store = get_pgvector_store()

    for url in body.urls:
        try:
            # Crawl page
            crawled_page = await simple_crawl_page(str(url))

            # Convert to Document
            doc = Document(
                page_content=crawled_page["content"],
                metadata={
                    "source": crawled_page["url"],
                    "title": crawled_page["title"],
                    "type": "web",
                },
            )

            # Split into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000, chunk_overlap=200
            )
            chunks = text_splitter.split_documents([doc])

            # Store chunks
            pgvector_store.add_documents(chunks)

            results.append(
                {"url": str(url), "status": "success", "chunks": len(chunks)}
            )
            logging.info(f"Successfully processed {url}")

        except Exception as e:
            failed_urls.append({"url": str(url), "error": str(e)})
            logging.error(f"Failed to process {url}: {e}")

    # Prepare response
    response = {
        "successful": results,
        "failed": failed_urls,
        "total_processed": len(results),
        "total_failed": len(failed_urls),
    }

    return JSONResponse(content=response)
