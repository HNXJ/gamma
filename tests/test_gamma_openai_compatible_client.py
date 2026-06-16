'''Tests for the OpenAI‑compatible client implementation.

The test mocks `urllib.request.urlopen` to avoid real network traffic and verifies
that the client builds the correct request payload, parses the JSON response,
records history, and returns the expected data.
'''

import json
from pathlib import Path
import pytest
from gamma.llm.backends.openai_compatible import OpenAICompatibleClient

@pytest.fixture()
def mock_response():
    """A simple JSON response mimicking an OpenAI chat completion reply."""
    return {"id": "test", "choices": [{"message": {"role": "assistant", "content": "Hello"}}]}

def test_send_success(monkeypatch, tmp_path, mock_response):
    class DummyResponse:
        def __init__(self, data: bytes):
            self._data = data
        def read(self):
            return self._data
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            pass
    def fake_urlopen(req, timeout=None):
        return DummyResponse(json.dumps(mock_response).encode())
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = OpenAICompatibleClient(
        url="http://mock-server/v1",
        api_key="test-key",
        model="gpt-test",
        transcript_dir=tmp_path,
    )
    result = client.send(prompt="Hello", temperature=0.0, max_tokens=5)
    assert result == mock_response
    history = client.read()
    assert len(history) == 1
    entry = history[0]
    assert entry["model"] == "gpt-test"
    transcript_files = list(Path(tmp_path).glob("transcript_*.json"))
    assert len(transcript_files) == 1
    with transcript_files[0].open() as f:
        saved = json.load(f)
    assert saved["response"] == mock_response

def test_status_redacts_api_key(monkeypatch):
    client = OpenAICompatibleClient(url="http://example", api_key="secret")
    status = client.status()
    assert status["api_key"] == "REDACTED"
    assert status["url"] == "http://example"
