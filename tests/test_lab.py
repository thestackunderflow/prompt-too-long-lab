"""Offline tests for the prompt-too-long lab. Run: ./run.sh test"""
import json, os, glob
import pytest
from lab import session, fixes, cost

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVID = os.path.join(HERE, 'evidence')


# ---- the simulated session ------------------------------------------------------------------------------
def test_session_is_deterministic():
    assert session.build(5) == session.build(5)


def test_each_turn_is_a_tool_use_then_its_result():
    s = session.build(3)
    msgs = s['messages']
    assert msgs[0]['role'] == 'user'
    # after the task message: (assistant tool_use, user tool_result) pairs; the request ends on a user turn
    pairs = msgs[1:]
    assert len(pairs) == 6
    for a, u in zip(pairs[::2], pairs[1::2]):
        assert a['role'] == 'assistant' and a['content'][0]['type'] == 'tool_use'
        assert u['role'] == 'user' and u['content'][0]['type'] == 'tool_result'
        assert u['content'][0]['tool_use_id'] == a['content'][0]['id']
    assert msgs[-1]['role'] == 'user'


def test_roles_alternate():
    msgs = session.build(4)['messages']
    assert all(a['role'] != b['role'] for a, b in zip(msgs, msgs[1:]))


def test_session_has_six_tools_and_a_system_prompt():
    s = session.build(1)
    assert len(s['tools']) == 6
    assert len(s['system']) > 200


def test_tool_results_are_real_files_and_grow_the_session():
    small, big = session.build(2), session.build(6)
    assert len(json.dumps(big)) > len(json.dumps(small))
    first = session.build(1)['messages'][2]['content'][0]['content']
    assert isinstance(first, str)
    assert 'def ' in first or 'class ' in first      # real Python source, not filler


# ---- fixes ----------------------------------------------------------------------------------------------
def test_trim_keeps_last_k_tool_results_and_marks_the_rest():
    s = session.build(6)
    t = fixes.trim_tool_results(s, keep=2)
    results = [b for m in t['messages'] if m['role'] == 'user' and isinstance(m['content'], list)
               for b in m['content'] if b['type'] == 'tool_result']
    assert len(results) == 6
    kept = [r for r in results if r['content'] != fixes.CLEARED]
    assert len(kept) == 2 and results[-1]['content'] != fixes.CLEARED
    assert len(json.dumps(t)) < len(json.dumps(s))


def test_trim_does_not_mutate_the_input():
    s = session.build(4)
    before = json.dumps(s)
    fixes.trim_tool_results(s, keep=1)
    assert json.dumps(s) == before


def test_summarise_splices_one_summary_before_the_last_k_turns():
    s = session.build(6)
    out = fixes.splice_summary(s, 'SUMMARY TEXT', keep_turns=2)
    msgs = out['messages']
    assert msgs[0]['role'] == 'user' and 'SUMMARY TEXT' in json.dumps(msgs[0])
    assert all(a['role'] != b['role'] for a, b in zip(msgs, msgs[1:]))
    uses = [b for m in msgs if m['role'] == 'assistant' for b in m['content'] if b['type'] == 'tool_use']
    assert len(uses) == 2


# ---- cost arithmetic ------------------------------------------------------------------------------------
def test_cache_read_is_cheaper_but_counts_the_same_tokens():
    p = cost.PRICES['claude-haiku-4-5']
    plain = cost.input_cost('claude-haiku-4-5', fresh=100_000)
    cached = cost.input_cost('claude-haiku-4-5', fresh=0, cache_read=100_000)
    assert cached == pytest.approx(plain * p['cache_read_mult'])
    assert cost.window_tokens(fresh=0, cache_read=100_000) == cost.window_tokens(fresh=100_000)


def test_spend_guard_refuses_over_cap():
    with pytest.raises(SystemExit):
        cost.guard(estimate_usd=10.5, cap_usd=10)
    cost.guard(estimate_usd=0.5, cap_usd=10)


# ---- evidence shape (only when a run has produced it) ---------------------------------------------------
@pytest.mark.skipif(not glob.glob(os.path.join(EVID, 'turns-*.json')), reason='no measure run yet')
def test_turn_counts_rise_and_parts_add_up():
    for f in glob.glob(os.path.join(EVID, 'turns-*.json')):
        d = json.load(open(f))
        totals = [t['total'] for t in d['turns']]
        assert totals == sorted(totals) and totals[-1] > totals[0]
        for t in d['turns']:
            assert t['tools'] + t['system'] + t['history'] == t['total']


@pytest.mark.skipif(not glob.glob(os.path.join(EVID, 'error-*.json')), reason='no reproduce run yet')
def test_error_evidence_is_the_400():
    for f in glob.glob(os.path.join(EVID, 'error-*.json')):
        d = json.load(open(f))
        assert d['status_code'] == 400
        assert d['body']['error']['type'] == 'invalid_request_error'
        assert 'prompt is too long' in d['body']['error']['message']
