from pydantic import BaseModel, HttpUrl
from typing import List

class CrawlRequest(BaseModel):
    urls: List[HttpUrl]