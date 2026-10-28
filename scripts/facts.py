"""Shared fact labels used on every page, so the same thing is worded the same way everywhere."""
import re

def is_membership(c):
    return bool(re.search(r'membership|needs', c.get('feeNote') or '', re.I))

def card_cost(c, counted=False):
    """'$60/yr Gold membership (not a card fee)' vs '$95 annual fee' vs 'No annual fee'."""
    f = c.get('fee') or 0
    if not f: return 'No annual fee'
    if is_membership(c):
        m = re.search(r'needs ([A-Z][\w ]*?) at', c.get('feeNote') or '')
        return f'${f:,}/yr {m.group(1) if m else ""} membership (not a card fee)'.replace('  ', ' ') + (', counted' if counted else '')
    return f'${f:,} annual fee' + (', counted' if counted else '')
