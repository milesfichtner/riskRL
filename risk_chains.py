"""Risk battle as an absorbing Markov chain: enumerate every chain (path)
from (A, D) to an absorbing state, with its exact probability.

Probabilities are Osborne (2003) Table 2 — exact enumeration, not Tan's
independence approximation. Stored as Fractions so chain products are exact.

State: (a, d) = attacking armies in the battle, defending armies.
Absorbing: a == 0 (defender wins) or d == 0 (attacker wins).
"""
from fractions import Fraction as Fr

# ---------------------------------------------------------------------------
# Static data
# ---------------------------------------------------------------------------

# (attacker dice, defender dice) -> Tan's case label
CASE_LABEL = {
    (1, 1): "I",
    (2, 1): "II",
    (3, 1): "III",
    (1, 2): "IV",
    (2, 2): "V",
    (3, 2): "VI",
}

# The 14 distinct transition probabilities.
# (attacker dice, defender dice) -> list of outcomes
#   (attacker_loss, defender_loss, probability, symbol)
# symbol pi_ijk: i attacker dice, j defender dice, k defender losses.
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

# Tan (1997) Table 3 values, for comparison only (contain the independence error).
TAN_VALUES = {
    "pi111": 0.417, "pi110": 0.583,
    "pi211": 0.578, "pi210": 0.422,
    "pi311": 0.659, "pi310": 0.341,
    "pi121": 0.254, "pi120": 0.746,
    "pi222": 0.152, "pi221": 0.475, "pi220": 0.373,
    "pi322": 0.259, "pi321": 0.504, "pi320": 0.237,
}

# Sanity: each case's outcomes sum to exactly 1.
for _key, _outs in OUTCOMES.items():
    assert sum(p for *_, p, _s in _outs) == 1, _key


def dice_for(a, d):
    """Dice rolled given armies (defender rolls max: rational-defender assumption)."""
    return min(a, 3), min(d, 2)


def is_absorbing(a, d):
    return a == 0 or d == 0


# ---------------------------------------------------------------------------
# Recursive chain enumeration (branch and bound)
# ---------------------------------------------------------------------------

def combinations(a, d, min_prob=Fr(0), _path=None, _steps=None, _prob=Fr(1),
                 chains=None, pruned=None):
    """Depth-first enumeration of every chain from (a, d) to absorption.

    Branch: each roll splits into 2 or 3 outcomes (OUTCOMES table).
    Bound:  a branch whose cumulative probability drops below min_prob is cut;
            its probability mass is added to pruned[0] so nothing is lost silently.

    Returns (chains, pruned_mass). chains maps a tuple of states -> record:
        {"states": [...], "steps": [(from, to, symbol, p, cumulative)], "prob": Fraction}
    """
    if chains is None:
        chains, pruned = {}, [Fr(0)]
        _path, _steps = [(a, d)], []

    # Absorbing state: record the finished chain.
    if is_absorbing(a, d):
        key = tuple(_path)
        if key not in chains:
            chains[key] = {"states": list(_path), "steps": list(_steps), "prob": _prob}
        return chains, pruned[0]

    # Bound.
    if _prob < min_prob:
        pruned[0] += _prob
        return chains, pruned[0]

    # Branch on each outcome of this roll.
    for att_loss, def_loss, p, sym in OUTCOMES[dice_for(a, d)]:
        nxt = (a - att_loss, d - def_loss)
        cum = _prob * p
        _path.append(nxt)
        _steps.append(((a, d), nxt, sym, p, cum))
        combinations(nxt[0], nxt[1], min_prob, _path, _steps, cum, chains, pruned)
        _path.pop()
        _steps.pop()

    return chains, pruned[0]


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def chain_string(rec):
    parts = [str(rec["states"][0])]
    for _frm, to, sym, p, _cum in rec["steps"]:
        parts.append(f"-[{sym} {float(p):.3f}]-> {to}")
    return " ".join(parts)


def print_chains(a, d, min_prob=Fr(0), max_print=50):
    chains, pruned = combinations(a, d, min_prob)
    recs = sorted(chains.values(), key=lambda r: r["prob"], reverse=True)

    print(f"\n=== Battle {a} attacking vs {d} defending: {len(recs)} chains ===")
    for rec in recs[:max_print]:
        end = rec["states"][-1]
        winner = "ATT" if end[1] == 0 else "DEF"
        print(f"  {winner}  P={float(rec['prob']):.6f}   {chain_string(rec)}")
    if len(recs) > max_print:
        print(f"  ... {len(recs) - max_print} more chains not shown")

    # Aggregate: sum chain probabilities by absorbing state.
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
    print(f"  pruned mass      = {float(pruned):.6f}")
    print(f"  total            = {float(p_att + p_def + pruned):.6f}")
    return chains, by_end, p_att


if __name__ == "__main__":
    print_chains(5, 2)
    print_chains(3, 3)