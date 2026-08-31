"""Study 3 — What Remains When the Sentence Breaks.

Matched variants of closure, repetition, and length.

Each source passage is rewritten into eight versions: a control, three with one
intervention, three with two, and one combining all three.

    incompletion    cuts the sentence before its ordinary ending and leaves it
                    without final punctuation
    lexical         replaces familiar content words with less common
                    alternatives and clears repeated words from the passage
    segmentation    divides the material into sentence units of no more than
                    four or five words

The three-way interaction is the test the design exists for: combined, do the
interventions cost more than the sum of their separate effects?

    python3 scripts/study3_sentence_breaks.py my_work/study3

Expects <root>/<passage>/<version>.txt, where each version is named for the
interventions it applies, joined by '+', or "control" for none:

    passage01/control.txt
    passage01/incompletion.txt
    passage01/lexical+segmentation.txt
    passage01/incompletion+lexical+segmentation.txt
"""

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_src"))

import common
from compare import compare_factorial
from evaluation import evaluate_text, mean_loss


INTERVENTIONS = {
    "incompletion": "Incompletion",
    "lexical": "Combined lexical intervention",
    "segmentation": "Segmentation",
}


def label(cell):

    if cell == "control":
        return "Control"
    return " + ".join(INTERVENTIONS[part] for part in cell.split("+"))


def main():
    p = common.parser(__doc__)
    p.add_argument("passage_dir", help="folder of <passage>/<version>.txt")
    p.add_argument("-o", "--out", help="write JSON here")
    args = p.parse_args()

    common.banner(3, "What Remains When the Sentence Breaks",
                  "Matched variants of closure, repetition, and length")

    passages = common.subfolders(
        args.passage_dir, "passage",
        f"{args.passage_dir}/<passage>/<version>.txt — one folder per source\n"
        f"       passage, each holding control.txt and its matched versions.")

    model = common.open_model(args)
    observations, unknown = [], set()
    for passage in passages:
        for path in sorted(passage.glob("*.txt")):
            applied = [] if path.stem == "control" else path.stem.split("+")
            if any(a not in INTERVENTIONS for a in applied):
                unknown.add(path.stem)
                continue
            words = evaluate_text(model, common.read_text(path))
            observations.append({
                "item": passage.name, "version": path.stem,
                "mean_loss": mean_loss(words),
                "n_tokens": sum(w.n_tokens for w in words),
                **{k: int(k in applied) for k in INTERVENTIONS},
            })

    if unknown:
        print(f"skipped unrecognised version names: {', '.join(sorted(unknown))}")
        print(f"expected 'control', or combinations of: "
              f"{', '.join(INTERVENTIONS)}\n")
    if not observations:
        sys.exit("error: nothing evaluated")

    result = compare_factorial(observations, factors=tuple(INTERVENTIONS))

    print(f"{result['n_observations']} texts from {result['n_items']} source "
          f"passages, R2 = {result['r_squared']}\n")

    control = result["cell_means"].get("control", {}).get("mean")
    print(f"  {'condition / intervention':<48}{'mean loss':>11}{'vs control':>13}")
    for cell, v in sorted(result["cell_means"].items(),
                          key=lambda kv: kv[1]["mean"]):
        delta = "" if cell == "control" else f"{v['mean'] - control:>+13.4f}"
        print(f"  {label(cell):<48}{v['mean']:>11.4f}{delta}")

    print("\neffects, holding the source passage constant")
    print(f"  {'term':<48}{'coef':>9}{'se':>8}{'p':>9}   reading")
    for term, e in result["effects"].items():
        name = " x ".join(INTERVENTIONS[part] for part in term.split(":"))
        print(f"  {name:<48}{e['coef']:>+9.4f}{e['se']:>8.4f}{e['p']:>9.4f}"
              f"   {common.significance(e['p'])}")

    tw = result["three_way_interaction"]
    print("\nDo the three interventions simply add up when combined?")
    print(f"  three-way interaction: coef {tw['coef']:+.4f}, p = {tw['p']:.4f}")
    print(f"  -> {tw['reading']}")

    print("\nEach version remakes the whole passage. Vocabulary, rhythm, pacing,")
    print("and length travel together into a new arrangement.")
    print("This output follows how the declared versions move through the model's")
    print("probability field. The changes stay together, as they do on the page.")

    if args.out:
        common.write_json(args.out, result)
        print(f"\nwritten: {args.out}")


if __name__ == "__main__":
    common.run(main)
