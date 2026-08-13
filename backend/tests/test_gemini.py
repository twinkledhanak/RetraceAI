import google.auth
import pytest

from retraceai.gemini import get_generative_model


def _has_credentials() -> bool:
    try:
        credentials, _ = google.auth.default()
        return bool(credentials)
    except Exception:
        return False


@pytest.mark.skipif(not _has_credentials(), reason="No Google Cloud credentials found")
def test_gemini_generate_success():
    model = get_generative_model()
    response = model.generate_content("Say SUCCESS if this works.")
    assert "SUCCESS" in response.text
    print(response.text)
