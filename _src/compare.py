"""Compare writing across declared conditions.

The functions in this file support the four forms of comparison used in the
method:
    compare_variants
        Compares a source passage with its declared variants.

    compare_factorial
        Compares three formal changes, separately and in combination, across
        matched passages. It asks what happens when the changes arrive together.

    compare_groups
        Compares groups of passages while accounting for differences in length.

    compare_cycles
        Tracks which visible words keep a similar relative position across
        successive versions of one passage.

## Length and group comparison

Mean per-token loss often falls as a passage becomes longer: later tokens have
more preceding text available to the model. A raw comparison between corpora of
different lengths therefore also reflects their different lengths.

`compare_groups` fits:

    mean_loss ~ group + log(n_tokens)

It then reports each group's predicted mean at one shared token count. Every
passage remains at its original length; the adjustment makes the length
difference visible rather than cutting the writing to fit the comparison.
"""

import numpy as np
from scipy import stats


def _ols(X, y):
    """Least squares. Returns (coefficients, standard errors, t, p, r_squared)."""
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    residuals = y - X @ coef
    dof = len(y) - np.linalg.matrix_rank(X)
    if dof <= 0:
        raise ValueError("not enough observations to fit this model")

    rss = float(residuals @ residuals)
    se = np.sqrt(np.diag((rss / dof) * np.linalg.pinv(X.T @ X)))
    with np.errstate(divide="ignore", invalid="ignore"):
        t = np.divide(coef, se, out=np.zeros_like(coef), where=se > 0)
    p = 2 * stats.t.sf(np.abs(t), dof)

    total = float(((y - y.mean()) ** 2).sum())
    r_squared = 1.0 - rss / total if total else 0.0
    return coef, se, t, p, r_squared


def compare_variants(evaluated):
    """Compare rewritten variants against a control.

    `evaluated` maps condition name -> list of Word. Must contain "control"!!!!.
    """
    from evaluation import mean_loss

    if "control" not in evaluated:
        raise ValueError("compare_variants needs a condition named 'control'")

    baseline = mean_loss(evaluated["control"])
    rows = [{
        "condition": name,
        "mean_loss": round(mean_loss(words), 4),
        "n_tokens": sum(w.n_tokens for w in words),
        "delta_from_control": round(mean_loss(words) - baseline, 4),
    } for name, words in evaluated.items()]

    return sorted(rows, key=lambda r: r["mean_loss"])


def compare_factorial(observations, factors=("incomplete", "nonrepeating", "short")):
    """Compare three declared changes across matched passage versions.

    `observations` contains one entry for each version:

        item          source passage ID
        <factor>      0 or 1 for each declared change
        mean_loss     measured mean loss

    The analysis compares each change on its own, each pair of changes, and all
    three together. It keeps the source passage constant, so the comparison
    follows what changed between its versions (and not against the other passages).

    The main question concerns the three changes together:

        near zero      their effects are additive
        positive       together, they produce higher loss than expected
        negative       together, they produce lower loss than expected
    """
    if len(factors) != 3:
        raise ValueError("this design takes exactly three factors")

    a, b, c = factors
    items = sorted({o["item"] for o in observations})
    if len(items) < 2:
        raise ValueError("need at least two source passages")

    y = np.array([o["mean_loss"] for o in observations], dtype=float)
    A = np.array([o[a] for o in observations], dtype=float)
    B = np.array([o[b] for o in observations], dtype=float)
    C = np.array([o[c] for o in observations], dtype=float)

    terms = {
        a: A, b: B, c: C,
        f"{a}:{b}": A * B, f"{a}:{c}": A * C, f"{b}:{c}": B * C,
        f"{a}:{b}:{c}": A * B * C,
    }

    # One dummy per source passage except the first, which the intercept absorbs.
    item_dummies = [np.array([1.0 if o["item"] == it else 0.0 for o in observations])
                    for it in items[1:]]

    columns = [np.ones(len(y))] + list(terms.values()) + item_dummies
    coef, se, t, p, r_squared = _ols(np.column_stack(columns), y)

    three_way = f"{a}:{b}:{c}"
    idx = list(terms).index(three_way) + 1
    if p[idx] >= 0.05:
        reading = "additive: the three costs add up; no extra effect from combining them"
    elif coef[idx] > 0:
        reading = "superadditive: combining the three costs more than the sum of their parts"
    else:
        reading = "subadditive: combining the three costs less than the sum of their parts"

    cells = {}
    for o in observations:
        key = tuple(int(o[f]) for f in factors)
        cells.setdefault(key, []).append(o["mean_loss"])

    return {
        "factors": list(factors),
        "n_observations": len(y),
        "n_items": len(items),
        "r_squared": round(r_squared, 4),
        "effects": {name: {"coef": round(float(coef[i + 1]), 4),
                           "se": round(float(se[i + 1]), 4),
                           "t": round(float(t[i + 1]), 3),
                           "p": round(float(p[i + 1]), 4)}
                    for i, name in enumerate(terms)},
        "three_way_interaction": {
            "term": three_way,
            "coef": round(float(coef[idx]), 4),
            "p": round(float(p[idx]), 4),
            "reading": reading,
        },
        "cell_means": {
            "+".join(f for f, on in zip(factors, key) if on) or "control":
                {"mean": round(float(np.mean(v)), 4), "n": len(v)}
            for key, v in sorted(cells.items())
        },
    }


def compare_groups(groups, reference=None):
    """Compare corpora on mean loss, raw and adjusted for passage length.

    `groups` maps group name -> list of (mean_loss, n_tokens), one pair per
    passage. `reference` names the baseline group; defaults to the first.
    """
    names = list(groups)
    reference = reference or names[0]
    if reference not in groups:
        raise ValueError(f"reference group {reference!r} is not in the data")
    others = [n for n in names if n != reference]

    y, membership, log_n = [], [], []
    for name in names:
        for loss, n_tokens in groups[name]:
            y.append(loss)
            membership.append(name)
            log_n.append(np.log(n_tokens))

    y = np.array(y, dtype=float)
    log_n = np.array(log_n, dtype=float)

    dummies = [np.array([1.0 if m == g else 0.0 for m in membership]) for g in others]
    X = np.column_stack([np.ones(len(y))] + dummies + [log_n])
    coef, se, t, p, r_squared = _ols(X, y)
    *_, raw_r_squared = _ols(X[:, :-1], y)    

    common_n = float(np.exp(log_n.mean()))
    intercept, log_coef = coef[0], coef[-1]

    adjusted = {reference: intercept + log_coef * np.log(common_n)}
    for j, g in enumerate(others, start=1):
        adjusted[g] = intercept + coef[j] + log_coef * np.log(common_n)

    return {
        "reference_group": reference,
        "n_passages": {n: len(groups[n]) for n in names},
        "raw_mean": {n: round(float(np.mean([row[0] for row in groups[n]])), 4)
                     for n in names},
        "mean_n_tokens": {n: round(float(np.mean([row[1] for row in groups[n]])), 1)
                          for n in names},
        "effects_vs_reference": {
            g: {"coef": round(float(coef[j]), 4), "se": round(float(se[j]), 4),
                "t": round(float(t[j]), 3), "p": round(float(p[j]), 4)}
            for j, g in enumerate(others, start=1)
        },
        "log_n_tokens": {"coef": round(float(log_coef), 4),
                         "se": round(float(se[-1]), 4),
                         "p": round(float(p[-1]), 4)},
        "r_squared_without_length": round(raw_r_squared, 4),
        "r_squared_with_length": round(r_squared, 4),
        "adjusted_at_n_tokens": round(common_n, 1),
        "adjusted_mean": {g: round(float(v), 4) for g, v in adjusted.items()},
    }


def compare_cycles(evaluated_by_cycle):
    """Track a word's percentile position across revisions.

    `evaluated_by_cycle` maps each cycle label to its list of words, in writing
    order.

    Words are matched by their visible form: lowercased and stripped of
    punctuation. This links `hers` in Cycle 0 with `hers` in Cycle 2 because
    the letters match. It does not claim that the word does the same work in
    each sentence. When a word appears more than once in one cycle, the
    occurrence with the highest loss is kept.

    Percentile bands are recalculated for every version. A word that remains in
    the upper decile holds that relative position within each passage; its loss
    value may still change.
    """
    from heatmap import top_decile

    cycles = list(evaluated_by_cycle)
    per_cycle = {}

    for cycle in cycles:
        words = evaluated_by_cycle[cycle]
        losses = np.array([w.loss_sum for w in words]) if words else np.array([])
        _, high_cut = top_decile(words)

        best = {}
        for w in words:
            key = w.text.strip(" .,:;!?—–-'\"’“”").lower()
            if not key:
                continue
            percentile = float((losses < w.loss_sum).mean() * 100) if len(losses) else 0.0
            record = {"loss": round(w.loss_sum, 4),
                      "percentile": round(percentile, 1),
                      "in_top_decile": bool(w.loss_sum >= high_cut)}
            if key not in best or record["loss"] > best[key]["loss"]:
                best[key] = record
        per_cycle[cycle] = best

    every_word = sorted({k for c in per_cycle.values() for k in c})
    rows = []
    for word in every_word:
        appearances = {c: per_cycle[c][word] for c in cycles if word in per_cycle[c]}
        if len(appearances) < 2:
            continue        
        rows.append({
            "word": word,
            "cycles_present": list(appearances),
            "percentile": {c: v["percentile"] for c, v in appearances.items()},
            "top_decile_in": [c for c, v in appearances.items() if v["in_top_decile"]],
            "stayed_top_decile": all(v["in_top_decile"] for v in appearances.values()),
        })

    return {
        "cycles": cycles,
        "top_decile_by_cycle": {
            c: sorted((w for w, v in per_cycle[c].items() if v["in_top_decile"]),
                      key=lambda w: -per_cycle[c][w]["loss"])
            for c in cycles
        },
        "carried_words": sorted(rows, key=lambda r: -len(r["top_decile_in"])),
    }
