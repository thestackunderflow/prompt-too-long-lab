"""FREE step: measure the trimming fix with token counting, and compute the caching arithmetic from the measured
per-turn counts and the published prices. Writes evidence/fix-trim.json and evidence/cost-calc.json."""
import json, os
from lab import session, fixes, cost
from lab.measure import client, count, EVID


def main():
    files = session.source_files()
    out = {}
    for m in ['claude-haiku-4-5', 'claude-opus-5-5']:
        d = json.load(open(f'{EVID}/turns-{m}.json'))
        n = d['turns'][-1]['turn']                      # the first turn past the window
        full = session.build(n, files)
        rows = []
        for keep in (10, 5, 3, 1):
            t, err = count(m, fixes.trim_tool_results(full, keep))
            rows.append({'keep_last': keep, 'tokens': t, 'error': err})
            print(m, 'turn', n, 'keep', keep, t)
        out[m] = {'turn': n, 'untrimmed': d['turns'][-1]['total'], 'window': d['window'], 'trimmed': rows}
    json.dump(out, open(f'{EVID}/fix-trim.json', 'w'), indent=1)

    # caching arithmetic: an agent re-sends the whole history every turn. Without caching every input token is
    # billed at the base price; with caching the previous turn's prefix is a cache read and the new part a write.
    calc = {}
    for m in ['claude-haiku-4-5', 'claude-opus-5-5']:
        turns = json.load(open(f'{EVID}/turns-{m}.json'))['turns']
        window = json.load(open(f'{EVID}/turns-{m}.json'))['window']
        turns = [t for t in turns if t['total'] <= window]
        plain = sum(cost.input_cost(m, fresh=t['total']) for t in turns)
        cached, prev = 0.0, 0
        for t in turns:
            cached += cost.input_cost(m, cache_read=prev, cache_write=t['total'] - prev)
            prev = t['total']
        calc[m] = {'turns': len(turns), 'last_total': turns[-1]['total'], 'input_cost_no_cache_usd': round(plain, 4),
                   'input_cost_with_cache_usd': round(cached, 4),
                   'window_tokens_last_turn_either_way': turns[-1]['total'],
                   'note': 'calculation from measured counts and published prices; output tokens excluded'}
        print(m, calc[m])
    json.dump(calc, open(f'{EVID}/cost-calc.json', 'w'), indent=1)


if __name__ == '__main__':
    main()
