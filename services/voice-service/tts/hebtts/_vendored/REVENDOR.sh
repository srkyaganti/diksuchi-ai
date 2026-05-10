#!/usr/bin/env bash
# Refresh the vendored slp-rl/HebTTS tree.
#
# Usage:
#   ./REVENDOR.sh <path-to-fresh-HebTTS-checkout>
#
# After running, re-apply the local patches called out in VENDOR_NOTICE.md
# (currently only valle/data/__init__.py).

set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <path-to-HebTTS-checkout>" >&2
  exit 2
fi

SRC="$1"
DST="$(cd "$(dirname "$0")" && pwd)"

cp -r "$SRC"/valle "$DST"/
cp -r "$SRC"/tokenizer "$DST"/
cp -r "$SRC"/speakers "$DST"/
cp "$SRC"/utils.py "$DST"/

rm -f "$DST"/valle/bin/{trainer,add_tokens,display_manifest_statistics,tokenizer,infer}.py
# Keep input_strategies.py — it's imported by valle/models/valle.py.
rm -f "$DST"/valle/data/{datamodule,dataset,fbank}.py
rm -rf "$DST"/valle/tests

echo "Re-apply patches listed in VENDOR_NOTICE.md before committing." >&2
