#!/usr/bin/env bash
# Inside the lab container, PAID (Haiku 4.5 only, capped): a real Claude Code session that reads six real files,
# then /context, /compact, /context, all on the same session. Measures what /compact frees.
set -uo pipefail
OUT=/out; mkdir -p $OUT /work && cd /work && git init -q
FILES=$(python -c "from lab import session; print(' '.join(session.source_files()[:6]))")
SID=$(python -c 'import uuid; print(uuid.uuid4())'); echo "$SID" > $OUT/compact-session-id.txt
C="claude --model claude-haiku-4-5 --setting-sources project,local --strict-mcp-config --permission-mode dontAsk --output-format stream-json --verbose"
$C -p "Use the Read tool to read each of these files in full, one at a time, in this order: $FILES. After reading all six, reply with only the word: done." \
   --session-id "$SID" --tools Read --allowedTools Read --max-budget-usd 1.00 < /dev/null > $OUT/compact-1-read.jsonl 2> $OUT/compact-1-read.stderr
$C -p "/context" --resume "$SID" --max-budget-usd 0.01 < /dev/null > $OUT/compact-2-context-before.jsonl 2>&1
$C -p "/compact" --resume "$SID" --max-budget-usd 0.50 < /dev/null > $OUT/compact-3-compact.jsonl 2>&1
$C -p "/context" --resume "$SID" --max-budget-usd 0.01 < /dev/null > $OUT/compact-4-context-after.jsonl 2>&1
echo ok
