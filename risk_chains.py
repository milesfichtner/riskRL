"""Enumerate every chain from (A, D) to an absorbing state. Probabilities: Osborne (2003) Table 2."""
from fractions import Fraction as Fr

CASE_LABEL = {
    (1, 1): "I",
    (2, 1): "II",
    (3, 1): "III",
    (1, 2): "IV",
    (2, 2): "V",
    (3, 2): "VI",
}

# (att dice, def dice) -> [(att_loss, def_loss, p, symbol)]; pi_ijk: k = defender losses
OUTCOMES = {
    (1, 1): [
        (0, 1, Fr(15, 36),     "pi111"),
        (1, 0, Fr(21, 36),     "pi110"),
    ],
    (2, 1): [
        (0, 1, Fr(125, 216),   "pi211"),
        (1, 0, Fr(91, 216),    "pi210"),
    ],
    (3, 1): [
        (0, 1, Fr(855, 1296),  "pi311"),
        (1, 0, Fr(441, 1296),  "pi310"),
    ],
    (1, 2): [
        (0, 1, Fr(55, 216),    "pi121"),
        (1, 0, Fr(161, 216),   "pi120"),
    ],
    (2, 2): [
        (0, 2, Fr(295, 1296),  "pi222"),
        (1, 1, Fr(420, 1296),  "pi221"),
        (2, 0, Fr(581, 1296),  "pi220"),
    ],
    (3, 2): [
        (0, 2, Fr(2890, 7776), "pi322"),
        (1, 1, Fr(2611, 7776), "pi321"),
        (2, 0, Fr(2275, 7776), "pi320"),
    ],
}

def dice_for(a, d):
    return min(a, 3), min(d, 2)


def is_absorbing(a, d):
    return a == 0 or d == 0


def combinations(a, d, _path=None, _steps=None, _prob=Fr(1), chains=None):
    """Returns chains: tuple(states) -> {states, steps, prob}."""
    if chains is None:
        chains = {}
        _path, _steps = [(a, d)], []

    if is_absorbing(a, d):
        key = tuple(_path)
        if key not in chains:
            chains[key] = {"states": list(_path), "steps": list(_steps), "prob": _prob}
        return chains

    for att_loss, def_loss, p, sym in OUTCOMES[dice_for(a, d)]:
        nxt = (a - att_loss, d - def_loss)
        cum = _prob * p
        _path.append(nxt)
        _steps.append(((a, d), nxt, sym, p, cum))
        combinations(nxt[0], nxt[1], _path, _steps, cum, chains)
        _path.pop()
        _steps.pop()

    return chains


def chain_string(rec):
    parts = [str(rec["states"][0])]
    for _frm, to, sym, p, _cum in rec["steps"]:
        parts.append(f"-[{sym} {float(p):.3f}]-> {to}")
    return " ".join(parts)


def print_chains(a, d, max_print=50):
    chains = combinations(a, d)
    recs = sorted(chains.values(), key=lambda r: r["prob"], reverse=True)

    print(f"\n=== Battle {a} attacking vs {d} defending: {len(recs)} chains ===")
    for rec in recs[:max_print]:
        end = rec["states"][-1]
        winner = "ATT" if end[1] == 0 else "DEF"
        print(f"  {winner}  P={float(rec['prob']):.6f}   {chain_string(rec)}")
    if len(recs) > max_print:
        print(f"  ... {len(recs) - max_print} more chains not shown")

    by_end = {}
    for rec in recs:
        end = rec["states"][-1]
        by_end[end] = by_end.get(end, Fr(0)) + rec["prob"]

    p_att = sum(p for (ea, ed), p in by_end.items() if ed == 0)
    p_def = sum(p for (ea, ed), p in by_end.items() if ea == 0)

    print("  Absorbing-state distribution:")
    for end in sorted(by_end, key=lambda s: (s[1] == 0, s)):
        print(f"    {end}: {float(by_end[end]):.6f}")
    print(f"  P(attacker wins) = {float(p_att):.6f}")
    print(f"  P(defender wins) = {float(p_def):.6f}")
    print(f"  total            = {float(p_att + p_def):.6f}")
    return chains, by_end, p_att


if __name__ == "__main__":
    print_chains(5, 2)
    print_chains(3, 3)