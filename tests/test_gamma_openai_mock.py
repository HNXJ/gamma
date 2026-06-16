import pytest
from gamma.llm.backends.openai_mock import OpenAIMockLLM
from gamma.llm.errors import UnsupportedOperationError

def test_openai_mock_basic_flow():
    client = OpenAIMockLLM(url="http://mock-openai", api_key="secret")
    # send a prompt
    resp = client.send("Hello")
    assert resp["id"] == "mock-id"
    # read returns deterministic placeholder based on last prompt
    read_resp = client.read()
    assert read_resp["response"] == "mocked response for: Hello"
    # status redacts api_key
    status = client.status()
    assert status["url"] == "http://mock-openai"
    assert status["api_key"] == "REDACTED"

def test_openai_mock_lowrank_unsupported():
    client = OpenAIMockLLM(url="http://mock", api_key="key")
    with pytest.raises(UnsupportedOperationError):
        client.lora(content="x", rank=4)
    with pytest.raises(UnsupportedOperationError):
        client.dora(content="x", rank=4)
    with pytest.raises(UnsupportedOperationError):
        client.sft(dataset="data")
