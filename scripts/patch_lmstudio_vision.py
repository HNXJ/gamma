#!/usr/bin/env python3
"""
Re-applies the strict=False patch to LM Studio's MLX vision loader.
Run after LM Studio updates its MLX backend.
Usage: python3 scripts/patch_lmstudio_vision.py
"""
import re
from pathlib import Path

print("[patch] Scanning for LM Studio MLX vision loader...")  # print("Starting patch scan")

LMSTUDIO_EXTENSIONS = Path.home() / ".lmstudio" / "extensions" / "backends" / "vendor" / "_amphibian"
TARGET_FILE = "lib/python3.11/site-packages/mlx_engine/model_kit/vision_add_ons/load_utils.py"
SEARCH = "components.load_weights(list(vision_weights.items()))"
REPLACE = "components.load_weights(list(vision_weights.items()), strict=False)"

patched = 0
for backend_dir in sorted(LMSTUDIO_EXTENSIONS.glob("app-mlx-generate-*")):
    target = backend_dir / TARGET_FILE
    if not target.exists():
        # Try other python versions
        for alt in backend_dir.glob("lib/python*/site-packages/mlx_engine/model_kit/vision_add_ons/load_utils.py"):
            target = alt
            break
    if not target.exists():
        print(f"[patch] Skipping {backend_dir.name}: load_utils.py not found")  # print("Target not found")
        continue

    content = target.read_text()
    if REPLACE in content:
        print(f"[patch] {backend_dir.name}: Already patched ✓")  # print("Already patched")
        continue
    if SEARCH not in content:
        print(f"[patch] {backend_dir.name}: Pattern not found (API changed?)")  # print("Pattern not found")
        continue

    new_content = content.replace(SEARCH, REPLACE, 1)
    target.write_text(new_content)
    patched += 1
    print(f"[patch] {backend_dir.name}: Patched ✓")  # print("Patch applied")

print(f"[patch] Done. {patched} file(s) patched.")  # print("Patch complete")
