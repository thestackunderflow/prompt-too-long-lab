#!/usr/bin/env bash
# ./run.sh test|measure|freefixes|reproduce|cc-overflow|cc-context|cc-compact   (paid: reproduce, cc-compact; need RUN_PAID=1)
set -euo pipefail
cd "$(dirname "$0")"
docker build -q -t prompt-too-long-lab . >/dev/null
# Evidence is published: after every run, host paths become <lab>/<home> and keys/account fields are removed (lab/scrub.py).
scrub() { MSYS_NO_PATHCONV=1 docker run --rm -v "$(pwd -W 2>/dev/null || pwd)/evidence:/lab/evidence" prompt-too-long-lab python -m lab.scrub evidence; }
case "${1:-test}" in
  test)      docker run --rm prompt-too-long-lab python -m pytest -q tests ;;
  measure)   cmd="python -m lab.measure" ;;
  reproduce) cmd="python -m lab.reproduce" ;;
  freefixes) cmd="python -m lab.free_fixes" ;;
  cc-overflow|cc-context|cc-compact)
    [ "$1" = cc-compact ] && [ "${RUN_PAID:-0}" != 1 ] && { echo "paid step: set RUN_PAID=1"; exit 2; }
    script=${1#cc-}; [ "$script" = context ] && script=context-fixes
    : "${ANTHROPIC_API_KEY:?set ANTHROPIC_API_KEY}"
    mkdir -p evidence/claude-code
    out=evidence/claude-code; [ "$1" = cc-overflow ] && out=/dev/null
    if [ "$1" = cc-overflow ]; then
      MSYS_NO_PATHCONV=1 docker run --rm -e ANTHROPIC_API_KEY -v "$(pwd -W 2>/dev/null || pwd)/claude-run:/run:ro" prompt-too-long-lab         bash /run/overflow.sh > evidence/claude-code/overflow-haiku45.jsonl 2> evidence/claude-code/overflow-haiku45.stderr
    else
      MSYS_NO_PATHCONV=1 docker run --rm -e ANTHROPIC_API_KEY -v "$(pwd -W 2>/dev/null || pwd)/claude-run:/run:ro"         -v "$(pwd -W 2>/dev/null || pwd)/evidence/claude-code:/out" prompt-too-long-lab bash /run/$script.sh
    fi
    scrub
    exit 0 ;;
  *) echo "usage: see the first line"; exit 2 ;;
esac
if [ "${1:-test}" != test ]; then
  : "${ANTHROPIC_API_KEY:?set ANTHROPIC_API_KEY}"
  MSYS_NO_PATHCONV=1 docker run --rm -e ANTHROPIC_API_KEY -e RUN_PAID="${RUN_PAID:-0}" \
    -v "$(pwd -W 2>/dev/null || pwd)/evidence:/lab/evidence" prompt-too-long-lab $cmd
  scrub
  MSYS_NO_PATHCONV=1 docker run --rm -v "$(pwd -W 2>/dev/null || pwd)/evidence:/lab/evidence" prompt-too-long-lab python -m pytest -q tests
fi
