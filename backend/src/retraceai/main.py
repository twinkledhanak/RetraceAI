from fastapi import FastAPI
from pymongo import MongoClient

from retraceai.api.health import router as health_router
from retraceai.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)

app.include_router(health_router)

db_client: MongoClient | None = None
if settings.mongodb_uri:
    db_client = MongoClient(settings.mongodb_uri.get_secret_value())
    print("Connected to MongoDB:", db_client.server_info())
else:
    print("MONGODB_URI not set; skipping database connection")


@app.get("/")
def root() -> dict[str, str]:
    return {"message": f"Welcome to {settings.app_name}"}
