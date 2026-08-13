from functools import lru_cache

from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel

from retraceai.config import get_settings


@lru_cache
def get_generative_model() -> GenerativeModel:
    settings = get_settings()
    aiplatform.init(project=settings.gcp_project, location=settings.gcp_location)
    return GenerativeModel(settings.gemini_model)
