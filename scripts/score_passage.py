"""Measure one passage, token by token.

This is the basic operation behind all four studies. You can use it
for trying a single passage before deciding what to do with it. 
Or if you are interested in how the model analyzes your writing.

    python3 scripts/score_passage.py my_work/passage01.txt
    python3 scripts/score_passage.py my_work/passage01.txt --level token -o out.csv
"""

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_src"))

import common
from evaluation import evaluate_text, token_losses, mean_loss, words_to_dicts


def main():
    p = common.parser(__doc__)
    p.add_argument("text_file")
    p.add_argument("--level", choices=["word", "token"], default="word",
                   help="reporting unit (default: word)")
    p.add_argument("-o", "--out", help="write a CSV here")
    args = p.parse_args()

    text = common.read_text(args.text_file)
    model = common.open_model(args)
    words = evaluate_text(model, text)

    if args.level == "token":
        offsets, losses = token_losses(model, text)
        rows = [{"token": text[s:e], "loss": round(v, 4), "start": s, "end": e}
                for (s, e), v in zip(offsets, losses)]
        key, unit = "loss", "token"
    else:
        rows = [{"word": w["text"], "loss_sum": round(w["loss_sum"], 4),
                 "n_tokens": w["n_tokens"], "loss_mean": round(w["loss_mean"], 4),
                 "start": w["start"], "end": w["end"]}
                for w in words_to_dicts(words)]
        key, unit = "loss_sum", "word"

    print(f"\n{len(words)} words, {sum(w.n_tokens for w in words)} evaluated tokens")
    print(f"mean loss: {mean_loss(words):.4f} nats per token\n")
    print(f"most expensive {unit}s (the model expected these least):")
    for r in sorted(rows, key=lambda x: -x[key])[:10]:
        print(f"  {r[unit].strip():<20} {r[key]:>9.4f}")

    if args.out:
        common.write_csv(args.out, rows)
        print(f"\nwritten: {args.out}")


if __name__ == "__main__":
    common.run(main)
