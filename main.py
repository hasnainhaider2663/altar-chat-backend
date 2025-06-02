import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from app.api import chat
from app.api.admin import admin
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        logging.info("Backend application starting up...")
    except Exception as e:
        logging.critical(
            f"FATAL: Could not initialize RAG service or connect to DB on startup: {e}"
        )
        raise
    yield
    logging.info("Backend application shutting down.")


app = FastAPI(
    title="Altar.io Chatbot Backend",
    description="API for Altar.io's AI chatbot, powered by Langchain, PostgreSQL, and Gemini.",
    version="1.0.0",
    lifespan=lifespan,debug=True,  
    
)

origins = [
    "http://localhost:3000",  # frontend (if running on 3000)
    "http://localhost:8000",  # Swagger UI
    "https://v0-next-js-frontend-development-taupe.vercel.app",  # production frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api", tags=["Customer Chat"])
app.include_router(admin.router, prefix="/api/admin", tags=["Customer Chat"])


@app.get("/")
async def root():

    return {"message": "Altar.io Chatbot Backend is running!"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Default to 8000 if not set
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)