"""FREE step: read each model's context window from the Models API, then count the simulated session's tokens
after every turn until it passes that window. Writes evidence/models.json and evidence/turns-<model>.json."""
import json, os, time
import anthropic
from lab import session

MODELS = ['claude-haiku-4-5', 'claude-haiku-5-5', 'claude-opus-5-5']
EVID = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'evidence')
client = anthropic.Anthropic()


def count(model, s):
    """count_tokens, or the error the endpoint returns, verbatim."""
    try:
        return client.messages.count_tokens(model=model, **s).input_tokens, None
    except anthropic.APIStatusError as e:
        return None, {'status_code': e.status_code, 'body': e.body,
                      'request_id': e.response.headers.get('request-id')}


def main():
    os.makedirs(EVID, exist_ok=True)
    stamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    windows = {}
    for m in MODELS:
        info = client.models.retrieve(m)
        windows[m] = info.max_input_tokens
        print(m, 'max_input_tokens', info.max_input_tokens, 'max_tokens', info.max_tokens)
    json.dump({'retrieved_at': stamp, 'sdk': anthropic.__version__,
               'models': {m: {'max_input_tokens': windows[m]} for m in MODELS}},
              open(f'{EVID}/models.json', 'w'), indent=1)

    files = session.source_files()
    task_only = {'messages': [{'role': 'user', 'content': session.TASK}]}
    for m in MODELS:
        base, _ = count(m, task_only)
        with_tools, _ = count(m, {**task_only, 'tools': session.TOOLS})
        with_sys, _ = count(m, {**task_only, 'system': session.SYSTEM})
        tools_t, sys_t = with_tools - base, with_sys - base
        turns, over = [], None
        n = 0
        while True:
            n += 1
            s = session.build(n, files)
            total, err = count(m, s)
            if err:
                over = {'turn': n, 'chars': len(json.dumps(s)), **err}
                print(m, 'turn', n, 'count_tokens error', err['status_code'])
                break
            turns.append({'turn': n, 'file': os.path.relpath(files[(n - 1) % len(files)], session.STDLIB),
                          'total': total, 'tools': tools_t, 'system': sys_t, 'history': total - tools_t - sys_t})
            print(m, 'turn', n, total)
            if total > windows[m]:
                break
        json.dump({'model': m, 'counted_at': stamp, 'window': windows[m], 'tools_count': len(session.TOOLS),
                   'turns': turns, 'count_tokens_error_after_last_turn': over},
                  open(f'{EVID}/turns-{m}.json', 'w'), indent=1)


if __name__ == '__main__':
    main()
