import json
import logging
from functools import lru_cache

from google.cloud import aiplatform
from vertexai.generative_models import GenerationConfig, GenerativeModel
from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel

from retraceai.config import get_settings

logger = logging.getLogger("retraceai")

SEARCH_DECISION_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "needs_vector_search": {"type": "boolean"},
        "reason": {"type": "string"},
    },
    "required": ["needs_vector_search", "reason"],
}


@lru_cache
def get_generative_model() -> GenerativeModel:
    settings = get_settings()
    aiplatform.init(project=settings.gcp_project, location=settings.gcp_location)
    return GenerativeModel(settings.gemini_model)


@lru_cache
def get_embedding_model() -> TextEmbeddingModel:
    settings = get_settings()
    aiplatform.init(project=settings.gcp_project, location=settings.gcp_location)
    return TextEmbeddingModel.from_pretrained(settings.embedding_model)


def embed_text(text: str) -> list[float]:
    model = get_embedding_model()
    embedding = model.get_embeddings([TextEmbeddingInput(text, task_type="RETRIEVAL_QUERY")])[0]
    return list(embedding.values)


def parse_search_decision(text: str) -> tuple[bool, str]:
    try:
        data = json.loads(text)
        return bool(data.get("needs_vector_search", True)), str(data.get("reason", ""))
    except (json.JSONDecodeError, AttributeError, TypeError):
        return True, "unparseable model output; defaulting to search"


def needs_vector_search(query: str) -> tuple[bool, str]:
    model = get_generative_model()
    logger.info("  Gemini: generating search decision (model=%s)...", get_settings().gemini_model)
    prompt = (
        "Your job is to decide whether answering the user's question requires searching "
        "a knowledge base of software upgrade paths (notes on how previous upgrades were "
        "done, e.g. 'how do I upgrade Python?'). Answer YES if the question asks how to "
        "perform an upgrade, migration, or troubleshooting step, or otherwise would benefit "
        "from the knowledge base. Answer NO for general facts or small talk. "
        'Respond in JSON with "needs_vector_search" (boolean) and "reason" (string).\n'
        f'Question: "{query}"'
    )
    response = model.generate_content(
        prompt,
        generation_config=GenerationConfig(
            response_mime_type="application/json",
            response_schema=SEARCH_DECISION_SCHEMA,
        ),
    )
    decision, reason = parse_search_decision(response.text)
    logger.info("  Gemini: decision received -> needs_vector_search=%s", decision)
    return decision, reason
