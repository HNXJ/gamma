import pytest
import gamma
from gamma.llm.errors import UnsupportedOperationError


def test_import_and_exports():
    assert hasattr(gamma, "allm")
    assert hasattr(gamma, "llm")


def test_active_llm_status_and_lowrank():
    act = gamma.allm(model="test-model", interface="test-iface")
    status = act.status()
    assert status["kind"] == "active"
    assert status["model"] == "test-model"
    assert status["interface"] == "test-iface"
    # low‑rank stubs
    lora_res = act.lora(rank=4)
    assert lora_res["method"] == "lora"
    assert lora_res["training_executed"] is False
    dora_res = act.dora(rank=4)
    assert dora_res["method"] == "dora"
    assert dora_res["config"]["use_dora"] is True
    sft_res = act.sft(dataset="data.jsonl")
    assert sft_res["method"] == "sft"
    assert sft_res["training_executed"] is False


def test_remote_llm_status_and_unsupported():
    rem = gamma.llm(url="http://localhost:8000/v1", api_key="secret", model="gpt")
    status = rem.status()
    assert status["kind"] == "remote"
    assert status["url"] == "http://localhost:8000/v1"
    # api_key should be redacted
    assert status["api_key"] == "REDACTED"
    # unsupported low‑rank operations raise
    for fn in (rem.lora, rem.dora, rem.sft):
        with pytest.raises(UnsupportedOperationError):
            fn()
