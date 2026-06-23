from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from src.api.routes.chat_routes import router as chat_router
from src.api.routes.document_routes import router as documents_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Chat with PDF",
    description="RAG-based Q&A over multi-format documents with full source traceability.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents_router)
app.include_router(chat_router)

@app.get("/")
async def greetings():
    return "hello world"

@app.get("/health")
async def health():
    return {"status": "ok"}