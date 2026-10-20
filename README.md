# prompt-too-long lab

Companion lab for the video on the Claude API error **400 `invalid_request_error`: "prompt is too long"**:
why long multi-turn and agent sessions hit it, and three fixes, measured.

Everything runs in Docker. Nothing is installed on the host.

## What it shows

1. **The box fills turn by turn.** A deterministic, simulated coding-agent session (a system prompt, 6 tool
   definitions, then turns where the agent reads real source files from the Python standard library inside the
   container) is measured with the free token counting endpoint after every turn, for each model in the run.
   Each count is split into: tool definitions, system prompt, and conversation history.
2. **Where the wall is.** The context window of each model is read live from the Models API
   (`max_input_tokens`), not typed in by hand.
3. **The error itself** (paid step, off by default): the session is grown past the smallest window and sent to
   the Messages API. The status code, error type, message and request id are saved exactly as returned.
4. **Fixes, measured:**
   - *Trim old tool results*: keep the last K tool results, replace older ones with a short marker (the same
     idea as the API's tool-result clearing). Measured with token counting (free).
   - *Summarise*: Claude Code's `/compact` on a real session, measured with `/context` before and after.
   - *Pack lighter*: `/context` with a big CLAUDE.md and with an MCP server attached.
   - *Prompt caching*: shown with arithmetic from the measured counts and the published prices. Caching changes what the tokens cost; the docs say
     cached prefixes **still occupy the context window**, so it is not a fix for the error.

## Run

```
./run.sh test                   # unit tests, offline
./run.sh measure                # free: Models API + token counting -> evidence/
./run.sh freefixes              # free: trimming measured, caching arithmetic -> evidence/
RUN_PAID=1 ./run.sh reproduce   # paid (~$0.20, Haiku 4.5 only): the 400 and a 200 control
./run.sh cc-overflow            # Claude Code 2.1.302: one piped prompt over 200K (refused before sending, $0)
./run.sh cc-context             # Claude Code /context in 4 setups (local command, $0)
RUN_PAID=1 ./run.sh cc-compact  # paid (~$0.32, Haiku 4.5): real session, /context, /compact, /context
```

Claude Code runs inside the container (pinned 2.1.302, signs in with ANTHROPIC_API_KEY, no user settings,
`--strict-mcp-config`). Real model calls use Haiku 4.5 only; Opus is measured with token counting only.

The API key is read from the environment variable `ANTHROPIC_API_KEY` (passed into the container by `run.sh`,
never written to disk by the lab). Spend cap for the paid steps: $10 (`lab/cost.py` stops a run whose estimate
is higher).

## Files

- `lab/session.py` builds the simulated session (pure, deterministic).
- `lab/fixes.py` trimming and summary-splicing (pure).
- `lab/cost.py` price table (from the Claude pricing page, read 19 Oct 2026) and arithmetic.
- `lab/scrub.py` runs after every `run.sh` step: host paths in the evidence become `<lab>`/`<home>`, API keys and account fields are removed.
- `lab/measure.py`, `lab/free_fixes.py`, `lab/reproduce.py` talk to the API and write `evidence/*.json`.
- `claude-run/*.sh` run Claude Code inside the container and write `evidence/claude-code/`.
- `tests/` unit tests (no network) plus shape checks on the evidence files when they exist.

## License

Apache-2.0, see `LICENSE`.
