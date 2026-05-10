"""Pre-fetch all models needed by voice-service.

Run this once on a machine WITH internet access to populate caches.
After it finishes, the deployment can run with HF_HUB_OFFLINE=1 and never
touch the HuggingFace Hub.

HuggingFace cache lives under HF_HUB_CACHE (or HF_HOME/hub, default
~/.cache/huggingface/hub). The HebTTS checkpoint is downloaded from
Google Drive (it is not a HuggingFace model) into HEBTTS_CHECKPOINT_PATH
(default ~/.cache/hebtts/checkpoint.pt). Ship those paths — or mount them
as volumes — to the offline target.

Models fetched:
  1. STT_MODEL_REPO         — full repo (CTranslate2 + tokenizer)
  2. TTS_MODEL_NAME         — full repo (~2 GB Parler-TTS checkpoint)
  3. TEXT_ENCODER_REPO      — tokenizer files only; description encoder
                              weights are bundled inside the parent
                              checkpoint, so we only need its tokenizer.
  4. HebTTS checkpoint      — single ~1.5 GB .pt from Google Drive (file id
                              from the upstream README).
"""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

load_dotenv()

# A prefetch run cannot itself be in offline mode — unset the flag if a
# stale env value would block downloads.
os.environ.pop("HF_HUB_OFFLINE", None)

from huggingface_hub import snapshot_download  # noqa: E402

STT_MODEL_REPO = os.getenv("STT_MODEL_REPO", "Systran/faster-whisper-large-v3")
TTS_MODEL_NAME = os.getenv("TTS_MODEL_NAME", "ai4bharat/indic-parler-tts")
TEXT_ENCODER_REPO = os.getenv("TTS_TEXT_ENCODER_REPO", "google/flan-t5-large")

# HebTTS publishes its checkpoint as a single .pt on Google Drive (see
# slp-rl/HebTTS README). It is not a HuggingFace repo.
HEBTTS_DRIVE_FILE_ID = os.getenv(
    "HEBTTS_DRIVE_FILE_ID", "11NoOJzMLRX9q1C_Q4sX0w2b9miiDjGrv"
)
HEBTTS_CHECKPOINT_PATH = os.getenv(
    "HEBTTS_CHECKPOINT_PATH",
    str(os.path.expanduser("~/.cache/hebtts/checkpoint.pt")),
)

# Only the tokenizer files are needed from the text encoder — the actual
# encoder weights live inside the Parler-TTS checkpoint.
TEXT_ENCODER_TOKENIZER_PATTERNS = [
    "tokenizer.json",
    "tokenizer_config.json",
    "spiece.model",
    "special_tokens_map.json",
    "config.json",
]


def _download(repo_id: str, **kwargs) -> str:
    print(f"→ {repo_id}")
    path = snapshot_download(repo_id=repo_id, **kwargs)
    print(f"  ✓ cached at {path}\n")
    return path


def _download_hebtts_checkpoint(file_id: str, dest: str) -> None:
    print(f"→ HebTTS checkpoint (Drive file {file_id})")
    if os.path.exists(dest):
        print(f"  ✓ already present at {dest}\n")
        return

    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)

    try:
        import gdown
    except ImportError as exc:
        raise RuntimeError(
            "gdown is required to fetch the HebTTS checkpoint from Drive; "
            "pip install gdown"
        ) from exc

    gdown.download(id=file_id, output=dest, quiet=False)
    print(f"  ✓ saved to {dest}\n")


def main() -> int:
    print("Pre-fetching voice-service models for offline deployment\n")
    print(f"  Cache: {os.getenv('HF_HUB_CACHE') or os.getenv('HF_HOME') or '~/.cache/huggingface'}\n")

    try:
        _download(STT_MODEL_REPO)
        _download(TTS_MODEL_NAME)
        _download(TEXT_ENCODER_REPO, allow_patterns=TEXT_ENCODER_TOKENIZER_PATTERNS)
        _download_hebtts_checkpoint(HEBTTS_DRIVE_FILE_ID, HEBTTS_CHECKPOINT_PATH)
    except Exception as exc:
        print(f"✗ Prefetch failed: {exc}", file=sys.stderr)
        return 1

    print("✓ All models cached. Set HF_HUB_OFFLINE=1 in the deployment env.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
