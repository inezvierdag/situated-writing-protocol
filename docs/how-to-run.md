# How to run the protocol

This guide explains how to run the computational procedures used in the thesis. For the method and its limits, read [`method.md`](method.md), [`start-here.md`](start-here.md), and [`ethical-boundaries.md`](ethical-boundaries.md).

## Set up

The repository runs on macOS, Linux, and Windows. See [`model-configuration.md`](model-configuration.md).

- **Apple silicon Mac** — M1, M2, M3, or later. The repository can use MLX, which is faster on this hardware.
- **Intel Mac, Linux, or Windows** — the repository uses PyTorch. It can run on a CPU or GPU, although CPU scoring may take longer.

The scripts select an available backend automatically. To specify one, add `--backend mlx` or `--backend torch` after the script name.

Open a terminal and move into the repository folder:

```bash

cd ~/situated-writing-protocol

```

Every command below assumes this location. If you receive a `No such file or directory` error, first check that you are in the repository folder and that the path you supplied is correct.
Install the dependencies once:

```bash
# Apple silicon Mac: M1, M2, M3, or later
pip3 install -r requirements.txt

# Intel Mac, Linux, or Windows
pip3 install -r requirements-portable.txt
```

On Windows, use `python` rather than `python3`, and `pip` instead of `pip3`.

Check that the installation worked:

```bash
python3 scripts/study1_protocol_visible.py --help
```

If this command fails, resolve the error before continuing.

## Choose a model

The first scoring command downloads the required model from Hugging Face and stores it locally. Later runs use the local copy.

If you already have a compatible model on your computer, add `--model` followed by its path:

```bash
python3 scripts/score_passage.py \
  --model /path/to/your/model \
  examples/example_passage.txt
```

Use the same model, tokenizer, backend, and quantisation throughout a comparison. A score belongs to that declared configuration.

## Run the examples

Start with the synthetic examples. They show the output format without using your own writing.

```bash
python3 scripts/study1_protocol_visible.py \
  examples/study1_corpora \
  --reference protocol_derived

python3 scripts/study2_sentence_places_body.py examples/study2_nouns.json

python3 scripts/study3_sentence_breaks.py examples/study3_passages

python3 scripts/study4_writing_back.py examples/study4_passage01

python3 scripts/score_passage.py examples/example_passage.txt
```

To check the comparison calculations without loading a model:

```bash
python3 tests/test_compare.py
```

## Use your own writing

Write first. Record the conditions of composition. Freeze the passage. Score it afterwards. Keep working material in a separate folder, such as `my_work/`. 

### Study 1: Protocol and controls

Create one folder per condition, with one `.txt` file per passage:

```text
my_work/study1/
├── protocol_derived/
│ ├── p01.txt
│ └── ...
├── plain_prose/
│ ├── p01.txt
│ └── ...
└── model_generated/
   ├── p01.txt
   └── ...
```

Run:

```bash
python3 scripts/study1_protocol_visible.py \
  my_work/study1 \
  --reference protocol_derived
```

The output includes raw and length-adjusted group means. Read both: differences in passage length can shape the raw result.

To make the model-generated condition:

```bash
python3 scripts/make_controls.py \
  my_work/study1/protocol_derived \
  my_work/study1/model_generated
```

This is the repository’s only generation command. The other scripts score text that already exists.

### Study 2: Sentence position

Create a JSON file of target nouns, grouped by lexical field:

```json
{
  "body": ["body", "flesh", "hand", "mouth"],
  "object": ["knife", "mirror", "plate", "room"]
}
```

Run:

```bash
python3 scripts/study2_sentence_places_body.py \
  my_work/nouns.json \
  -o outputs/study2.csv
```

Choose nouns that fit both sentence frames:

```text
The [noun] refuses the machine.
The machine refuses the [noun].
```

The frames must differ before the target word. Otherwise the model receives the same (or no) preceding context and the comparison cannot test positional difference.

### Study 3: Matched variants

Create one folder per source passage. Every folder must contain the same eight versions:

```text
my_work/study3/
└── passage01/
    ├── control.txt
    ├── incompletion.txt
    ├── lexical.txt
    ├── segmentation.txt
    ├── incompletion+lexical.txt
    ├── incompletion+segmentation.txt
    ├── lexical+segmentation.txt
    └── incompletion+lexical+segmentation.txt
```

Run:

```bash
python3 scripts/study3_sentence_breaks.py my_work/study3
```

Keep versions close in length. The filenames declare the intervention and must use only `incompletion`, `lexical`, `segmentation`, and `+`, or `control`.

### Study 4: Writing back through loss

Create one folder for each passage, with versions named in the order in which they were written:

```text
my_work/study4/passage01/
├── cycle0.txt
├── cycle1.txt
└── cycle2.txt
```

Run:

```bash
python3 scripts/study4_writing_back.py \
  my_work/study4/passage01 \
  --out-dir outputs/passage01
```

The script writes a heatmap and score CSV for each cycle, then identifies words that remain in the upper decile across versions. The decile is recalculated within each version.

### Score one passage

```bash
python3 scripts/score_passage.py \
  my_work/passage01.txt \
  -o outputs/passage01.csv
```

Add `--level token` to receive individual token scores rather than word-level scores.

## Error

| Problem                                                    | Check                                                                          |
| ---------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `No such file or directory`                                | Confirm that you are in the repository folder and that the path is correct.    |
| `command not found: python3`                               | Install Python, reopen Terminal, and try again. On Windows, use `python`.      |
| `No scoring backend is installed` or `ModuleNotFoundError` | Re-run the relevant `pip install -r ...` command and inspect its error output. |
| `Could not load ... with any available backend`            | Check the model name and backend. MLX models require Apple silicon.            |
| `error: no .txt files`                                     | Confirm that the target folder contains `.txt` files.                          |

## Read the output carefully

A loss value records model-relative expectation under one stated setup. It can return you to a question about rhythm, syntax, repetition, segmentation, or revision. 
