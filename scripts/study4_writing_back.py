"""Study 4 — Writing Back Through the Loss.

Heatmap-led recomposition.

The four stages of one cycle:

    1. Composition     write and freeze the source passage before measurement
    2. Evaluation      measure word-level loss in nats
    3. Declaration     record the upper-decile words to retain and move
    4. Recomposition   write and freeze a new passage under that constraint

then evaluate the new passage, make a new map, and repeat once. Terminate after
Cycle 2.

This script performs stages 2 and 3 for every cycle already written, and
reports which words held the upper decile across them. Stages 1 and 4 are the
writing, and belong to the writer.

    python3 scripts/study4_writing_back.py my_work/passage01 --out-dir outputs/passage01

Expects one folder holding the cycles in order:

    passage01/cycle0.txt
    passage01/cycle1.txt
    passage01/cycle2.txt

Word-level loss is the sum over a word's sub-tokens, which is what the heatmap
shows on the page. Deciles are recomputed inside each cycle, so a word can
leave the upper decile without its own loss falling: the passage around it
changed.
"""

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_src"))

import common
from compare import compare_cycles
from heatmap import render, top_decile, classify
from evaluation import evaluate_text, mean_loss, words_to_dicts


def main():
    p = common.parser(__doc__)
    p.add_argument("cycle_dir", help="folder of cycle0.txt, cycle1.txt, ...")
    p.add_argument("--out-dir", help="where heatmaps and loss values are written")
    p.add_argument("--format", default=".jpg", choices=[".jpg", ".png", ".pdf"]) #you can change the output here if you like.
    p.add_argument("--columns", type=int, default=8, help="words per row")
    p.add_argument("--dpi", type=int, default=300)
    args = p.parse_args()

    common.banner(4, "Writing Back Through the Loss", "Heatmap-led recomposition")

    texts = common.read_texts(args.cycle_dir)
    model = common.open_model(args)
    evaluated = {name: evaluate_text(model, text) for name, text in texts}

    passage = Path(args.cycle_dir).name
    out_dir = Path(args.out_dir or f"outputs/{passage}")
    out_dir.mkdir(parents=True, exist_ok=True)

    for name, words in evaluated.items():
        low, high = top_decile(words)
        image = out_dir / f"{name}_heatmap{args.format}"
        render(words, image, title=f"{passage} — {name}",
               words_per_row=args.columns, dpi=args.dpi)
        common.write_csv(
            out_dir / f"{name}_scores.csv",
            [{"word": w["text"], "word_loss": round(w["loss_sum"], 4),
              "n_tokens": w["n_tokens"], "loss_mean": round(w["loss_mean"], 4)}
             for w in words_to_dicts(words)])

        upper = [w for w, band in classify(words) if band == "high"]
        print(f"{name}")
        print(f"  mean loss {mean_loss(words):.4f} nats/token, "
              f"{len(words)} ranked words")
        print(f"  red from {high:.4f} nats, blue to {low:.4f} nats "
              f"(this cycle's own deciles)")
        print("  upper decile: "
              + ", ".join(f"{w.text} {w.loss_sum:.4f}" for w in upper))
        print(f"  written: {image.name}, {name}_scores.csv")

    result = compare_cycles(evaluated)
    carried = [r for r in result["carried_words"] if len(r["top_decile_in"]) >= 2]

    print(f"\nwords in the upper decile of two or more cycles: {len(carried)}"
          f"   (* marks a cycle where the word was in the upper decile)")
    for r in carried:
        path = " -> ".join(
            f"{c}:{r['percentile'][c]:.0f}pct"
            + ("*" if c in r["top_decile_in"] else " ")
            for c in r["cycles_present"])
        print(f"  {r['word']:<18} {path}")

    common.write_json(out_dir / f"{passage}_rank_migration.json", result)
    print("\nEach cycle redraws its own red line. A word can leave the upper")
    print("band without becoming less unexpected: the passage around it has")
    print("changed. Word-level loss gathers the values of its sub-tokens.")
    print("\nThe heatmap is not an instruction to obey. It is a place to begin.")
    print("Before measuring the next cycle, record what you retained, moved,")
    print("removed, or refused.")
    print("Start with the red words. See where they insist on going.")
    print(f"\nwritten: {out_dir}/")


if __name__ == "__main__":
    common.run(main)
