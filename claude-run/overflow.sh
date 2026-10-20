#!/usr/bin/env bash
# Inside the lab container: one Claude Code prompt whose piped input is bigger than Haiku 4.5's 200K window.
# The input is real standard-library source (the same files and order as the session in lab/session.py).
set -uo pipefail
mkdir -p /work && cd /work && git init -q
python -c "
from lab import session
fs = session.source_files()[:20]
print('\n\n'.join('# FILE ' + f + '\n' + open(f, encoding='utf8').read() for f in fs))" > /tmp/input.txt
wc -c /tmp/input.txt >&2
claude --version >&2
date -u +%FT%TZ >&2
claude -p "Which of these Python modules is the longest? Answer with the file name only." \
  --model claude-haiku-4-5 --tools "" --setting-sources project,local --permission-mode dontAsk \
  --max-budget-usd 0.50 --output-format stream-json --verbose < /tmp/input.txt
echo "exit=$?" >&2
