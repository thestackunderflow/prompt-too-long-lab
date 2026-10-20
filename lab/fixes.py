"""Two ways to shrink a session before the next request. Pure: inputs are never modified."""
import copy

CLEARED = '[old tool result cleared to save context]'


def trim_tool_results(sess, keep):
    """Keep the last `keep` tool results; replace older ones with a short marker (like tool-result clearing)."""
    s = copy.deepcopy(sess)
    results = [b for m in s['messages'] if m['role'] == 'user' and isinstance(m['content'], list)
               for b in m['content'] if b['type'] == 'tool_result']
    for b in results[:max(0, len(results) - keep)]:
        b['content'] = CLEARED
    return s


def splice_summary(sess, summary, keep_turns):
    """Replace the task and every turn before the last `keep_turns` with one user message holding the summary."""
    s = copy.deepcopy(sess)
    turns = s['messages'][1:]
    tail = turns[len(turns) - 2 * keep_turns:] if keep_turns else []
    head = {'role': 'user', 'content': f"{s['messages'][0]['content']}\n\nSummary of the work so far:\n{summary}"}
    # tail starts with an assistant turn, so roles still alternate
    s['messages'] = [head] + tail
    return s
