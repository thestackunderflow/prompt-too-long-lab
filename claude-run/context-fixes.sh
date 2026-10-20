#!/usr/bin/env bash
# Inside the lab container, FREE: Claude Code's /context in four setups (no model call: /context is local).
#   bare | +1 MCP server (git) | +big CLAUDE.md | both
set -uo pipefail
OUT=/out; mkdir -p $OUT
claude --version > $OUT/version.txt; date -u +%FT%TZ >> $OUT/version.txt
cat > /tmp/mcp-git.json <<JSON
{ "mcpServers": { "git": { "command": "/opt/mcpgit/bin/mcp-server-git", "args": ["--repository", "/work"] } } }
JSON
cat > /tmp/mcp-none.json <<JSON
{ "mcpServers": {} }
JSON
run() {  # $1 name, $2 mcp config, $3 claude.md source or ""
  rm -rf /work && mkdir -p /work && cd /work && git init -q && git -c user.name=lab -c user.email=lab@example.invalid commit -q --allow-empty -m init
  [ -n "$3" ] && cp "$3" CLAUDE.md
  claude -p "/context" --model claude-haiku-4-5 --setting-sources project,local \
    --mcp-config "$2" --strict-mcp-config --permission-mode dontAsk --max-budget-usd 0.01 \
    --output-format stream-json --verbose < /dev/null > $OUT/context-$1.jsonl 2> $OUT/context-$1.stderr
}
# A long project-notes file: the standard library's argparse.py (about 100 KB) stands in for an oversized CLAUDE.md.
BIG=/usr/local/lib/python3.12/argparse.py
run bare /tmp/mcp-none.json ""
run mcp /tmp/mcp-git.json ""
run claudemd /tmp/mcp-none.json $BIG
run both /tmp/mcp-git.json $BIG
