"""Tests for the comparison maths. No model required.

Run: python tests/test_compare.py
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_src"))

from compare import compare_groups, compare_variants
from evaluation import Word


def _words(losses):
    """Fake an evaluated text from a list of per-token losses."""
    return [Word(text=f"w{i}", start=i, end=i + 1, loss_sum=v, n_tokens=1,
                 parts=((f"w{i}", v),))
            for i, v in enumerate(losses)]


def test_factorial_detects_a_planted_interaction():
    """The three-way interaction is the question this design exists to answer,
    so a planted one has to be found and an absent one has to stay absent."""
    from compare import compare_factorial

    def build(extra_when_all_three):
        obs = []
        for item in range(12):
            for a in (0, 1):
                for b in (0, 1):
                    for c in (0, 1):
                        obs.append({
                            "item": f"item{item}",
                            "mean_loss": (3.0 + 0.1 * item      # per-passage offset
                                          + 0.5 * a + 0.6 * b + 0.4 * c
                                          + extra_when_all_three * (a and b and c)),
                            "incomplete": a, "nonrepeating": b, "short": c})
        return obs

    flat = compare_factorial(build(0.0))
    assert abs(flat["three_way_interaction"]["coef"]) < 1e-6
    assert flat["three_way_interaction"]["reading"].startswith("additive")
    for name, expected in [("incomplete", 0.5), ("nonrepeating", 0.6), ("short", 0.4)]:
        assert abs(flat["effects"][name]["coef"] - expected) < 1e-6, name

    planted = compare_factorial(build(1.5))
    assert abs(planted["three_way_interaction"]["coef"] - 1.5) < 1e-6
    assert planted["three_way_interaction"]["reading"].startswith("superadditive")

    print("ok  factorial: recovers main effects, finds a planted three-way "
          "interaction, reports none when there is none")


def test_cycles_track_rank_not_raw_score():
    """A word's band is recomputed inside each cycle, so an unchanged raw loss value
    can be top-decile in one version and ordinary in the next."""
    from compare import compare_cycles

    def version(losses):
        return [Word(text=w, start=i, end=i + 1, loss_sum=s, n_tokens=1,
                     parts=((w, s),))
                for i, (w, s) in enumerate(losses)]

    result = compare_cycles({
        "cycle0": version([("anchor", 9.0)] + [(f"x{i}", 1.0) for i in range(19)]),
        "cycle1": version([("anchor", 9.0)] + [(f"y{i}", 20.0) for i in range(19)]),
    })

    assert "anchor" in result["top_decile_by_cycle"]["cycle0"]
    assert "anchor" not in result["top_decile_by_cycle"]["cycle1"]

    anchor = next(r for r in result["carried_words"] if r["word"] == "anchor")
    assert anchor["top_decile_in"] == ["cycle0"]
    assert anchor["stayed_top_decile"] is False
    print("ok  cycles: an unchanged loss value changes band when the passage changes")


def test_variants_delta_is_relative_to_control():
    rows = compare_variants({
        "control": _words([2.0, 2.0]),
        "louder": _words([3.0, 3.0]),
    })
    by_name = {r["condition"]: r for r in rows}
    assert by_name["control"]["delta_from_control"] == 0.0
    assert by_name["louder"]["delta_from_control"] == 1.0
    print("ok  variants: delta measured from control")


def test_mean_loss_is_token_weighted():
    from evaluation import mean_loss
    # one 1-token word at 1.0, one 3-token word summing to 9.0
    words = [Word("a", 0, 1, 1.0, 1), Word("bbb", 2, 5, 9.0, 3)]
    # token-weighted: 10.0 / 4 tokens = 2.5  (word-weighted would give 5.0)
    assert abs(mean_loss(words) - 2.5) < 1e-9
    print("ok  mean_loss: weighted by tokens, not words")


def test_length_control_recovers_the_true_group_effect():
    """The confound this protocol exists to flag.

    Group B is genuinely 0.40 nats cheaper, but B's passages are also longer,
    and longer passages receive lower mean loss for reasons unrelated to
    the group. The raw difference therefore overstates the effect; the
    length-controlled estimate should land near the truth.
    """
    rng = np.random.default_rng(0)
    true_effect, length_slope = -0.40, -0.90

    def build(base, low, high):
        return [(base + length_slope * np.log(n / 60) + rng.normal(0, 0.10), n)
                for n in rng.integers(low, high, 40)]

    result = compare_groups({"A": build(3.4, 40, 80),
                             "B": build(3.4 + true_effect, 80, 160)},
                            reference="A")

    raw_gap = result["raw_mean"]["B"] - result["raw_mean"]["A"]
    adjusted = result["effects_vs_reference"]["B"]["coef"]

    assert abs(adjusted - true_effect) < 0.10, adjusted
    assert abs(raw_gap) > abs(true_effect) + 0.20, raw_gap
    assert abs(result["log_n_tokens"]["coef"] - length_slope) < 0.15

    print(f"ok  length control: raw gap {raw_gap:+.3f} -> "
          f"adjusted {adjusted:+.3f} (true {true_effect:+.2f})")


def test_adjusted_means_differ_by_the_fitted_effect():
    rng = np.random.default_rng(1)
    groups = {g: [(3.0 + rng.normal(0, 0.1), int(n))
                  for n in rng.integers(50, 120, 30)] for g in ("A", "B")}
    r = compare_groups(groups, reference="A")
    gap = r["adjusted_mean"]["B"] - r["adjusted_mean"]["A"]
    assert abs(gap - r["effects_vs_reference"]["B"]["coef"]) < 1e-3
    print("ok  adjusted means: differ by exactly the fitted group coefficient")


if __name__ == "__main__":
    test_factorial_detects_a_planted_interaction()
    test_cycles_track_rank_not_raw_score()
    test_variants_delta_is_relative_to_control()
    test_mean_loss_is_token_weighted()
    test_length_control_recovers_the_true_group_effect()
    test_adjusted_means_differ_by_the_fitted_effect()
    print("\nall passed")
