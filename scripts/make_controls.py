"""Make the model-generated comparison texts for Study 1.

For each source passage, the model receives its first five words and continues from there. 
The continuation is kept until it reaches the source passage's
length and then ends at the first available sentence ending.

Run:

    python3 scripts/make_controls.py my_work/study1/protocol_derived \
                                     my_work/study1/model_generated

Then include the new folder in Study 1 under the same model configuration as
the other conditions.
"""

import re
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_src"))

import common


def truncate(prompt, generated, target_words):
    """Join the prompt and continuation, then stop at the first sentence ending  at or after the source passage's word count.
    The generated condition is not forced to match its source word for word.
    It is allowed to reach a complete sentence once it has reached a comparable length.
    """
    separator = "" if generated[:1].isspace() else " "
    words = (prompt + separator + generated).split()

    kept = []
    for i, word in enumerate(words):
        kept.append(word)
        if i + 1 >= target_words and re.search(r"[.!?]$", word):
            break
    return " ".join(kept)


def main():
    p = common.parser(__doc__)
    p.add_argument("source_dir", help="folder of source passages to prompt from")
    p.add_argument("out_dir", help="where the generated controls are written")
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--seed", type=int, default=0,
                   help="reset before each passage, so a run is repeatable")
    p.add_argument("--prompt-words", type=int, default=5,
                   help="how many of the source passage's opening words to use")
    args = p.parse_args()

    print("\nModel-generated controls for Study 1")
    print(f"  temperature {args.temperature}, seed {args.seed} "
          f"(reset before each passage), prompt {args.prompt_words} words\n")

    texts = common.read_texts(args.source_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    model = common.open_model(args)
    if model.backend != "mlx":
        sys.exit("error: generation requires the mlx backend.\n"
                 "       Every loss value script runs on either backend.")

    import mlx.core as mx
    from mlx_lm import generate as mlx_generate
    from mlx_lm.sample_utils import make_sampler

    for name, text in texts:
        target_words = len(text.split())
        prompt = " ".join(text.split()[:args.prompt_words])

        mx.random.seed(args.seed)
        generated = mlx_generate(
            model.model, model.tokenizer, prompt=prompt,
            max_tokens=int(target_words * 2.2) + 20,
            sampler=make_sampler(temp=args.temperature), verbose=False)

        control = truncate(prompt, generated, target_words)
        (out_dir / f"{name}.txt").write_text(control + "\n")
        print(f"  {name}: prompt {prompt!r} -> {len(control.split())} words "
              f"(source {target_words})")

    print(f"\nwritten: {out_dir}/")


if __name__ == "__main__":
    common.run(main)
