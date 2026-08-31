"""Study 2 — Where the Sentence Places the Body.

Pre-verbal and post-verbal target positions.

Each target noun enters two constructed transitive frames, with six carrier
verbs rotated through each:

    pre-verbal    The [target] {verb}s the machine.
    post-verbal   The machine {verb}s the [target].

Both frames keep the definite article. Dropping it would leave the post-verbal
frame ungrammatical, and the comparison would then measure the missing article
rather than the target's position.

In the pre-verbal frame the target is evaluated before the verb, so the six
carrier verbs return the same value. In the post-verbal frame each verb is
already part of the sequence when the target arrives, so each creates a
different local context.

    python3 scripts/study2_sentence_places_body.py my_work/nouns.json -o out.csv

Expects a JSON file grouping the target nouns by lexical field:

    {"body": ["stomach", "throat"], "neutral": ["thing", "way"]}
"""

import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_src"))

import common
from evaluation import evaluate_target


CARRIER_VERBS = ["refuses", "names", "trains", "contains", "recognizes",
                 "absorbs"] #you can add more verbs here if you want to test more contexts


def load_fields(path):
    """Read the lexical-field file, or exit saying what is wrong with it."""
    try:
        fields = json.loads(common.read_text(path))
    except json.JSONDecodeError as exc:
        sys.exit(f"error: {path} is not valid JSON ({exc}).\n"
                 f"       Look for a missing comma, or a comma after the last "
                 f"entry.\n"
                 f"       Compare it with examples/study2_nouns.json.")
    if not isinstance(fields, dict) or not fields:
        sys.exit(f'error: {path} should look like '
                 f'{{"lexical field": ["noun", "noun"], ...}}')
    return fields


def evaluate_frames(model, fields, first_subtoken, on_skip=None):
    """Measure every noun in both frames. Returns one row per noun."""
    rows = []
    for field, nouns in fields.items():
        for noun in nouns:
            pre, post = [], []
            for verb in CARRIER_VERBS:
                w = evaluate_target(model, f"The {noun} {verb} the machine.",
                                 noun, first_subtoken=first_subtoken)
                if w:
                    pre.append(w.loss_mean)
                w = evaluate_target(model, f"The machine {verb} the {noun}.",
                                 noun, first_subtoken=first_subtoken)
                if w:
                    post.append(w.loss_mean)

            if not pre or not post:
                if on_skip:
                    on_skip(noun)
                continue

            mean_pre, mean_post = sum(pre) / len(pre), sum(post) / len(post)
            rows.append({
                "noun": noun, "lexical_field": field,
                "pre_verbal": round(mean_pre, 4),
                "post_verbal": round(mean_post, 4),
                "difference": round(mean_pre - mean_post, 4),
                "pre_verbal_spread_across_verbs": round(max(pre) - min(pre), 6),
            })
    return rows


def main():
    p = common.parser(__doc__)
    p.add_argument("nouns", help='JSON: {"lexical field": ["noun", ...], ...}')
    p.add_argument("--subtoken", choices=["first", "mean"], default="first",
                   help="how to measure a target the tokenizer splits: its first "
                        "sub-token, or the mean across its span (default: first)")
    p.add_argument("-o", "--out", help="write a CSV here")
    args = p.parse_args()

    common.banner(2, "Where the Sentence Places the Body",
                  "Pre-verbal and post-verbal target positions")

    fields = load_fields(args.nouns)
    model = common.open_model(args)

    rows = evaluate_frames(
        model, fields, first_subtoken=(args.subtoken == "first"),
        on_skip=lambda n: print(f"  (skipped {n}: not locatable in one frame)"))
    if not rows:
        sys.exit("error: no nouns could be evaluated")

    pre = sum(r["pre_verbal"] for r in rows) / len(rows)
    post = sum(r["post_verbal"] for r in rows) / len(rows)

    print(f"across all {len(rows)} target nouns")
    print(f"  pre-verbal    The [target] {{verb}}s the machine    {pre:>8.4f} nats")
    print(f"  post-verbal   The machine {{verb}}s the [target]    {post:>8.4f} nats")
    print(f"  difference    pre-verbal minus post-verbal        {pre - post:>+8.4f} nats")

    print("\nby lexical field")
    print(f"  {'lexical field':<22}{'nouns':>6}{'pre-verbal':>13}"
          f"{'post-verbal':>14}{'difference':>13}")
    for field in fields:
        group = [r for r in rows if r["lexical_field"] == field]
        if not group:
            continue
        gp = sum(r["pre_verbal"] for r in group) / len(group)
        gq = sum(r["post_verbal"] for r in group) / len(group)
        print(f"  {field:<22}{len(group):>6}{gp:>13.4f}{gq:>14.4f}{gp - gq:>+13.4f}")

    spread = max(r["pre_verbal_spread_across_verbs"] for r in rows)
    print("\nIn the pre-verbal frame the target is evaluated before the verb, so")
    print("changing the verb cannot change its loss. The six carrier verbs")
    print(f"return the same value; the spread across them is {spread:.4f} nats,")
    print("which is the model's quantized arithmetic, not a difference between")
    print("the verbs.")
    print("\nThe two frames differ in position, grammatical role, and preceding")
    print("context at once. The result belongs to the frames as a whole; it does")
    print("not isolate grammatical role.")
    print(f"\nMulti-token targets evaluated as: "
          f"{'first sub-token' if args.subtoken == 'first' else 'mean across the token span'}.")

    if args.out:
        common.write_csv(args.out, rows)
        print(f"\nwritten: {args.out}")


if __name__ == "__main__":
    common.run(main)
