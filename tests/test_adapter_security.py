import pytest
import os
from src.sde_engine.adapter import ExecutionAdapter

def test_adapter_fails_closed_when_key_missing(tmp_path):
    proposals_dir = tmp_path / "proposals"
    proposals_dir.mkdir()
    
    with pytest.raises(FileNotFoundError, match="Required attestation secret not found"):
        ExecutionAdapter(proposals_dir)

def test_adapter_works_when_key_present(tmp_path):
    proposals_dir = tmp_path / "proposals"
    proposals_dir.mkdir()
    secret_path = tmp_path / "bridge_authority_v2.key"
    secret_path.write_text("test-secret-123")
    
    adapter = ExecutionAdapter(proposals_dir)
    assert adapter._secret == "test-secret-123"
