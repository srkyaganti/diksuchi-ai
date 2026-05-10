# Vendored from slp-rl/HebTTS

Source: https://github.com/slp-rl/HebTTS
Commit: `4cfc2b2a6b0127c575661dc938d3a43a75b265c5` (2025-06-13)
Paper: https://arxiv.org/abs/2407.12206 (Roth, Turetzky, Adi — Interspeech 2024)

## What's vendored
- `valle/` — model + inference code (VALL-E AR + NAR, AlephBert tokenizer, encodec audio tokenizer)
- `tokenizer/` — `vocab.txt`, `unique_words_tokens_all.k2symbols`
- `speakers/` — three reference WAV clips (`osim`, `geek`, `shaul`) + `speakers.yaml`
- `utils.py` — `AttributeDict`

## What's removed
Inference does not need the training data pipeline. We deleted:
- `valle/bin/{trainer,add_tokens,display_manifest_statistics,tokenizer,infer}.py`
- `valle/data/{datamodule,dataset,fbank}.py`
- `valle/tests/`

`valle/data/input_strategies.py` is kept verbatim — `valle/models/valle.py`
imports `PromptedFeatures` from it at module load.

## Local patches
- `valle/data/__init__.py` no longer does `from .datamodule import *`
  (datamodule was removed; it pulled in lhotse training dataloaders).

Everything else is byte-identical to upstream. Re-vendor by running the
copy-and-prune script in `tts/hebtts/_vendored/REVENDOR.sh` (or repeating
the commands in this file by hand) against a fresh checkout.

## License

Upstream license is in the original repository. Audit before redistribution.
