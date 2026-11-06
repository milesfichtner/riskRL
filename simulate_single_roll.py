"""Risk single-roll outcome maps for every legal dice matchup.

For each (attacker dice, defender dice) scenario, randomly rolls until every
one of the 6^(a+d) ordered outcomes has been seen at least once (coupon-
collector stop condition). Each unique outcome is classified once by the
number of attacker wins.

Indices: dice[0:a] = attacker, dice[a:a+d] = defender. Defender wins ties.
"""
import random
from collections import Counter

FACES = range(1, 7)
SCENARIOS = [(3, 2), (2, 2), (3, 1), (2, 1), (1,2), (1,1)]


def attacker_wins(dice, num_attacker_dice, num_defender_dice):
    a = sorted(dice[:num_attacker_dice], reverse=True)
    d = sorted(dice[num_attacker_dice:num_attacker_dice + num_defender_dice], reverse=True)
    n = min(num_attacker_dice, num_defender_dice)  # number of comparisons
    return sum(a[i] > d[i] for i in range(n))      # strict >: ties go to defender


def run_attack_sampling(num_attacker_dice, num_defender_dice, rng):
    k = num_attacker_dice + num_defender_dice
    total = 6 ** k
    outcome_map = {}  # raw ordered k-tuple -> attacker wins
    rolls = 0

    # separately could just loop through all 77776 combinations. Don't need to do random selection. 
    # although it does help for interesting stats. Which events are picked most often? Despite each being collectively exhaustive 
    # & mutually exclusive, and the total sample space being equally distributed probabilities
    while len(outcome_map) < total:
        dice = tuple(rng.choice(FACES) for _ in range(k))
        rolls += 1
        if dice not in outcome_map:
            outcome_map[dice] = attacker_wins(dice, num_attacker_dice, num_defender_dice)

    counts = Counter(outcome_map.values())
    n = min(num_attacker_dice, num_defender_dice)
    probs = {w: counts[w] / total for w in range(n + 1)}
    return outcome_map, counts, probs, rolls, total


# simpler method than the coupon-collectors problem to acheive the same results. 
# I still want to look further into combinatorics behind this and modeling it out with probability theory but I am tired rn
def decode(i, k):
    """Map integer i in [0, 6^k) to a k-tuple of dice faces 1..6 (base-6 digits)."""
    dice = []
    for _ in range(k):
        i, r = divmod(i, 6)
        dice.append(r + 1)
    return tuple(dice)

def run_attack_all_combinations(num_attacker_dice, num_defender_dice):
    """Exhaustively enumerate all 6^(a+d) outcomes and bin by
    (attacker troops lost, defender troops lost)."""
    k = num_attacker_dice + num_defender_dice
    total = 6 ** k
    n = min(num_attacker_dice, num_defender_dice)  # troops lost per roll
    bins = Counter()
 
    for i in range(total):
        wins = attacker_wins(decode(i, k), num_attacker_dice, num_defender_dice)
        bins[(n - wins, wins)] += 1  # (attacker lost, defender lost)
 
    return {loss: (bins[loss], total) for loss in sorted(bins)}


        

def main(seed=None):
    rng = random.Random(seed)
    results = {}
    for a, d in SCENARIOS:
        outcome_map, counts, probs, rolls, total = run_attack_sampling(a, d, rng)

        results[(a, d)] = probs
        print(f"\n{a} attacker vs {d} defender  ({total} outcomes, {rolls} rolls to cover)")
        for w, p in probs.items():
            print(f"  P(attacker wins {w}) = {counts[w]}/{total} = {p:.4f}")
        print(f"  Sum check: {sum(counts.values())} == {total}")
    return results



if __name__ == "__main__":
    main()