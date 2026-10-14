"""Requests from the Gemini agents to the human operator, kept in research/agent/HUMAN_ACTIONS.md.

The agents can read/write repo files, install packages, download models and run experiments. When
something outside that reach would help (a gated-model approval, a new secret, more GPU time, a
problem with the benchmark labels or evaluation), they add a request here instead of working around
it. Nothing in the file is applied automatically: the human
reviews each request and marks it ``[x]`` (done) or ``[-]`` (rejected), optionally appending
``Reply: ...`` to the line. Open and recently answered requests are shown to the planner, and a
request whose action is already listed (in any state) is not added again.
"""
import os
import re
from datetime import date

HEADER = """# Requests for the human operator

Written by the Gemini agents (`research/colab/agent_campaign.ipynb`) when something outside their
reach would help, e.g. a gated-model approval, a secret, more GPU time, or a concern about the
benchmark labels or evaluation. Nothing here is applied automatically: check each request yourself
before acting on it.

When handled, change `[ ]` to `[x]` (done) or `[-]` (rejected) and optionally append `Reply: ...`
to the line. Open and recently answered requests are shown to the planner.
"""
_LINE = re.compile(r"^- \[(.)\] \*\*(.+?)\*\*(.*)$")
_STATUS = {' ': 'open', 'x': 'done', 'X': 'done', '-': 'rejected'}
MAX_PER_CALL = 3
MAX_LEN = 300


def _clean(text):
    return " ".join(str(text or "").split())[:MAX_LEN]


def _key(action):
    return re.sub(r"\W+", " ", action.lower()).strip()


def read_requests(path):
    """[{status: open|done|rejected, action, rest}] in file order."""
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [{'status': _STATUS.get(m.group(1), 'open'), 'action': m.group(2), 'rest': m.group(3).strip()}
                for m in (_LINE.match(line.rstrip("\n")) for line in f) if m]


def add_requests(path, requests, source, iteration):
    """Appends valid new requests ({"action", "why", "blocking"}); returns the actions added."""
    if not isinstance(requests, list):
        return []
    known = {_key(r['action']) for r in read_requests(path)}
    lines, added = [], []
    for req in requests[:MAX_PER_CALL]:
        if not isinstance(req, dict) or not _clean(req.get('action')):
            continue
        action, why = _clean(req['action']).replace("**", ""), _clean(req.get('why'))
        if _key(action) in known:
            continue
        known.add(_key(action))
        blocking = ", blocking" if req.get('blocking') else ""
        lines.append(f"- [ ] **{action}** — {why} _({source}, iteration {iteration}, {date.today().isoformat()}{blocking})_\n")
        added.append(action)
    if lines:
        new_file = not os.path.exists(path)
        with open(path, "a", encoding="utf-8") as f:
            if new_file:
                f.write(HEADER + "\n")
            f.writelines(lines)
    return added


def format_for_prompt(path, max_answered=10):
    """Open requests plus the most recently answered ones, as lines for an agent prompt."""
    requests = read_requests(path)
    open_ = [r for r in requests if r['status'] == 'open']
    answered = [r for r in requests if r['status'] != 'open'][-max_answered:]
    lines = [f"- [{r['status']}] {r['action']} {r['rest']}" for r in open_ + answered]
    return "\n".join(lines) or "(none)"
