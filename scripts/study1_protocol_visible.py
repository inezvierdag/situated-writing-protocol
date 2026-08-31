"""Study 1 — What the Protocol Makes Visible.

Compares passages written under the Writing Protocol with comparison texts
under the same model configuration.

If the Protocol-derived passages are not distinguished from the comparison
texts, there is little reason to pursue their textual arrangements further.
If they are, the difference marks the corpus as a site for closer work.

    python3 scripts/study1_protocol_visible.py my_work/study1 --reference protocol_derived

The command expects one folder per text condition, each containing plain-text
passages:

    <root>/protocol_derived/*.txt
    <root>/plain_prose/*.txt
    <root>/model_generated/*.txt

To produce the model-generated condition, use make_controls.py.
"""

import sys
from pathlib import Path

# The shared modules live in _src/, one level up. Adding them to the path
# lets this script be run from anywhere, not only the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_src"))

import common
from compare import compare_groups
from evaluation import evaluate_text, mean_loss


def main():
    p = common.parser(__doc__)
    p.add_argument("corpus_dir", help="folder of <condition>/*.txt")
    p.add_argument("--reference", help="baseline condition (default: first)")
    p.add_argument("-o", "--out", help="write JSON here")
    args = p.parse_args()

    common.banner(1, "What the Protocol Makes Visible",
                  "Protocol-derived, plain-prose, and model-generated controls")

    folders = common.subfolders(
        args.corpus_dir, "condition",
        f"{args.corpus_dir}/<condition>/*.txt — one folder per text condition,\n"
        f"       not loose .txt files.")
    if len(folders) < 2:
        sys.exit(f"error: need at least two condition folders to compare; "
                 f"found {len(folders)}")

    model = common.open_model(args)
    groups, lengths = {}, {}
    for d in folders:
        entries = []
        for _, text in common.read_texts(d):
            words = evaluate_text(model, text)
            entries.append((mean_loss(words), sum(w.n_tokens for w in words)))
        groups[d.name] = entries
        lengths[d.name] = [n for _, n in entries]

    reference = args.reference or folders[0].name
    if reference not in groups:
        sys.exit(f"error: --reference {reference!r} is not one of: "
                 f"{', '.join(groups)}")
    result = compare_groups(groups, reference=reference)

    print(f"  {'text condition':<26}{'n':>4}{'mean loss':>12}{'tokens':>16}")
    for name in groups:
        lo, hi = min(lengths[name]), max(lengths[name])
        print(f"  {name:<26}{result['n_passages'][name]:>4}"
              f"{result['raw_mean'][name]:>12.4f}{f'{lo}-{hi}':>16}")

    span = [n for v in lengths.values() for n in v]
    print(f"\nPassages are not the same length: {min(span)} to {max(span)} tokens.")
    print("Mean per-token loss falls as a passage lengthens, so the raw means")
    print("above compare passage lengths as well as text conditions.")

    print(f"\nlength controlled, compared with '{result['reference_group']}'")
    for g, e in result["effects_vs_reference"].items():
        print(f"  {g:<26}{e['coef']:>+12.4f}  se {e['se']:.4f}  "
              f"p {e['p']:.4f}   {common.significance(e['p'])}")

    n = result["adjusted_at_n_tokens"]
    print(f"\nadjusted mean, every condition read at {n:.0f} tokens")
    for g, v in result["adjusted_mean"].items():
        print(f"  {g:<26}{v:>12.4f}")

    print(f"\nlog(tokens) coefficient {result['log_n_tokens']['coef']:+.4f} "
          f"(p {result['log_n_tokens']['p']:.4f}); R2 rises from "
          f"{result['r_squared_without_length']} to "
          f"{result['r_squared_with_length']} when length is added.")
    print("No passage was shortened or dropped. The adjusted figure is what the")
    print("fitted line predicts at one shared length, from every passage at its")
    print("real length.")
    print("\nThe conditions differ in vocabulary, sentence length, and textual")
    print("arrangement at once. A mean-loss comparison cannot separate these.")

    if args.out:
        common.write_json(args.out, result)
        print(f"\nwritten: {args.out}")


if __name__ == "__main__":
    common.run(main)
