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


def absorbing_order(a, d):
    """(0,d), ..., (0,1), (1,0), ..., (a,0): defender's best outcome -> attacker's best."""
    return [(0, k) for k in range(d, 0, -1)] + [(k, 0) for k in range(1, a + 1)]


def summarize(a, d):
    chains = combinations(a, d)
    counts, probs = {}, {}
    for rec in chains.values():
        end = rec["states"][-1]
        counts[end] = counts.get(end, 0) + 1
        probs[end] = probs.get(end, Fr(0)) + rec["prob"]
    states = [s for s in absorbing_order(a, d) if s in counts]
    return {
        "i": a,
        "j": d,
        "p_attacker_win": float(sum(p for s, p in probs.items() if s[1] == 0)),
        "num_chains": len(chains),
        "num_absorbing_states": len(states),
        "absorbing_states": [
            {"state": list(s), "num_chains": counts[s], "prob": float(probs[s])}
            for s in states
        ],
    }


def plot_summary(summary, out_path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ink, ink2, grid = "#0b0b0b", "#52514e", "#e4e3df"
    states = summary["absorbing_states"]
    labels = [f"({s['state'][0]},{s['state'][1]})" for s in states]
    x = range(len(states))
    n_def = sum(1 for s in states if s["state"][0] == 0)

    fig, (top, bot) = plt.subplots(2, 1, sharex=True, figsize=(max(8, 0.55 * len(states) + 2), 6), facecolor="#fcfcfb")
    panels = [
        (top, [s["num_chains"] for s in states], "#2a78d6", "Unique chains"),
        (bot, [s["prob"] for s in states], "#eb6834", "Probability"),
    ]
    for ax, ys, color, ylabel in panels:
        ax.set_facecolor("#fcfcfb")
        ax.plot(x, ys, color=color, lw=2, marker="o", ms=8,
                markeredgecolor="#fcfcfb", markeredgewidth=2)
        ax.set_ylabel(ylabel, color=ink2)
        ax.set_ylim(bottom=0)
        ax.grid(axis="y", color=grid, lw=0.8)
        ax.axvline(n_def - 0.5, color=ink2, lw=1, ls="--")
        for spine in ("top", "right", "left"):
            ax.spines[spine].set_visible(False)
        ax.spines["bottom"].set_color(grid)
        ax.tick_params(colors=ink2, length=0)
    ymax = max(s["num_chains"] for s in states) * 1.25
    top.set_ylim(0, ymax)
    top.text(n_def - 0.6, ymax, "defender wins", ha="right", va="top", color=ink2, fontsize=9)
    top.text(n_def - 0.4, ymax, "attacker wins", ha="left", va="top", color=ink2, fontsize=9)
    bot.set_xticks(list(x), labels)
    bot.set_xlabel("Absorbing state (attacker, defender)", color=ink2)
    fig.suptitle(
        f"{summary['i']} attacking vs {summary['j']} defending  |  "
        f"P(attacker wins) = {summary['p_attacker_win']:.3f}  |  {summary['num_chains']} chains",
        color=ink, fontsize=11)
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def main():
    import argparse
    import os

    ap = argparse.ArgumentParser()
    ap.add_argument("attack", type=int)
    ap.add_argument("defend", type=int)
    ap.add_argument("--stats", action=argparse.BooleanOptionalAction, default=True,
                    help="print chains and stats to the CLI (default on)")
    ap.add_argument("--chart", action=argparse.BooleanOptionalAction, default=False,
                    help="save a chart to --outdir (default off)")
    ap.add_argument("--outdir", default="charts")
    ap.add_argument("--fmt", default="pdf", choices=["pdf", "png"])
    args = ap.parse_args()

    if args.stats:
        print_chains(args.attack, args.defend)
    if args.chart:
        os.makedirs(args.outdir, exist_ok=True)
        path = os.path.join(args.outdir, f"battle_{args.attack}v{args.defend}.{args.fmt}")
        plot_summary(summarize(args.attack, args.defend), path)
        print(f"chart -> {path}")


if __name__ == "__main__":
    main()