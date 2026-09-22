from __future__ import annotations

import os
from pathlib import Path

def main() -> None:
    enabled = os.getenv("TRAIN_LORA", "0") == "1"
    base = os.getenv("TRAIN_BASE_MODEL", "").strip()
    out = Path(os.getenv("LORA_OUTPUT_DIR", "training/output"))
    out.mkdir(parents=True, exist_ok=True)

    if not enabled:
        print("TRAIN_LORA=0; skipping optional LoRA training.")
        return

    if not base:
        raise SystemExit("TRAIN_BASE_MODEL is required when TRAIN_LORA=1.")

    raise SystemExit(
        "LoRA training is intentionally a deployment-specific hook. "
        "Configure a compatible Transformers checkpoint and GPU trainer here; "
        "the supplied GGUF is an inference artifact, not a directly fine-tunable Transformers checkpoint."
    )

if __name__ == "__main__":
    main()
