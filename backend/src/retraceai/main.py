import logging

from fastapi import FastAPI
from pydantic import BaseModel

from retraceai.api.health import router as health_router
from retraceai.api.search import router as search_router
from retraceai.api.sessions import router as sessions_router
from retraceai.config import get_settings
from retraceai.db import get_db_client
from retraceai.gemini import get_generative_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("retraceai")

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)

app.include_router(health_router)
app.include_router(search_router)
app.include_router(sessions_router)

db_client = get_db_client()
if db_client is None:
    logger.warning("MONGODB_URI not set; skipping database connection")
else:
    logger.info("Connected to MongoDB: %s", db_client.server_info())


class Prompt(BaseModel):
    prompt: str


@app.get("/")
def root() -> dict[str, str]:
    return {"message": f"Welcome to {settings.app_name}"}


@app.post("/generate")
def generate(data: Prompt) -> dict[str, str]:
    model = get_generative_model()
    response = model.generate_content(data.prompt)
    return {"response": response.text}
