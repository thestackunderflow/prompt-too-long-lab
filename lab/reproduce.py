"""PAID step (RUN_PAID=1), Haiku 4.5 only: send the simulated session at the last turn under the 200K window
(control, expected to succeed) and at the first turn over it (expected 400). Saves status, body, request id and
usage exactly as returned. Never run near the limit on Opus (plan decision, 19 Oct)."""
import json, os, time
import anthropic
from lab import session, cost
from lab.measure import client, EVID

MODEL = 'claude-haiku-4-5'


def main():
    if os.environ.get('RUN_PAID') != '1':
        raise SystemExit('paid step: set RUN_PAID=1')
    d = json.load(open(f'{EVID}/turns-{MODEL}.json'))
    over, under = d['turns'][-1], d['turns'][-2]
    # worst case if both were accepted and billed in full
    cost.guard(cost.input_cost(MODEL, fresh=over['total'] + under['total']) + 2 * 16 * 5 / 1e6)
    files = session.source_files()
    for label, t in (('under', under), ('over', over)):
        s = session.build(t['turn'], files)
        stamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        rec = {'label': label, 'model': MODEL, 'turn': t['turn'], 'counted_tokens': t['total'],
               'window': d['window'], 'sent_at': stamp, 'sdk': anthropic.__version__}
        try:
            raw = client.messages.with_raw_response.create(model=MODEL, max_tokens=16, **s)
            m = raw.parse()
            rec.update(status_code=raw.status_code, request_id=raw.headers.get('request-id'),
                       usage=m.usage.model_dump(), stop_reason=m.stop_reason)
        except anthropic.APIStatusError as e:
            rec.update(status_code=e.status_code, body=e.body, request_id=e.response.headers.get('request-id'))
        print(json.dumps(rec)[:600])
        name = 'error' if rec['status_code'] >= 400 else 'ok'
        json.dump(rec, open(f'{EVID}/{name}-{MODEL}-turn{t["turn"]}.json', 'w'), indent=1)


if __name__ == '__main__':
    main()
