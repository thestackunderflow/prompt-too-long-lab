"""Prices (USD per million tokens) from the Claude pricing page, read 19 Oct 2026, and the
arithmetic used in the video. Cache multipliers from the prompt caching page, same date."""
import sys

PRICES = {
    'claude-haiku-4-5': {'input': 1.00, 'output': 5.00, 'cache_read_mult': 0.10, 'cache_write_5m_mult': 1.25},
    'claude-haiku-5-5': {'input': 0.10, 'output': 0.50, 'cache_read_mult': 0.10, 'cache_write_5m_mult': 1.25,
                         'long_over': 100_000, 'long_input': 0.50},  # prompts over 100K tokens
    'claude-opus-5-5': {'input': 4.00, 'output': 20.00, 'cache_read_mult': 0.05, 'cache_write_5m_mult': 1.25},
}


def input_cost(model, fresh=0, cache_read=0, cache_write=0):
    p = PRICES[model]
    base = p['input']
    if 'long_over' in p and window_tokens(fresh, cache_read, cache_write) > p['long_over']:
        base = p['long_input']
    return (fresh + cache_read * p['cache_read_mult'] + cache_write * p['cache_write_5m_mult']) * base / 1e6


def window_tokens(fresh=0, cache_read=0, cache_write=0):
    """What counts toward the context window: all three (context windows page)."""
    return fresh + cache_read + cache_write


def guard(estimate_usd, cap_usd=10.0):
    if estimate_usd > cap_usd:
        sys.exit(f'refusing: estimated ${estimate_usd:.2f} is over the ${cap_usd:.2f} cap')
