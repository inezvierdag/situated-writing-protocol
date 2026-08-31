# Situated Writing Protocol

A practice-based protocol for bringing teacher-forced language-model evaluation into relation with situated writing. It supports the composition, documentation, measurement, comparison, and revision of pre-written text under a declared model configuration.

## What the code does

- **Study 1 — What the Protocol Makes Visible**  
  Compares groups of passages (Protocol-derived, plain prose, and model-generated) while accounting for differences in passage length.

- **Study 2 — Where the Sentence Places the Body**  
  Compares the same target noun in two constructed sentence positions (before and after the verb) across multiple carrier verbs.

- **Study 3 — What Remains When the Sentence Breaks**  
  Compares matched variants of a passage that differ in incompletion, lexical intervention, and segmentation, and their combinations.

- **Study 4 — Writing Back Through the Loss**  
  Supports heatmap-led recomposition across successive versions of a passage and identifies words that remain in the upper-loss band.

## Reference configuration

The results reported in the thesis were produced locally on an Apple-silicon MacBook using MLX.

```text
Model:        mlx-community/Mistral-7B-v0.3-4bit
Model type:   Base model (not instruction-tuned)
Backend:      MLX
Procedure:    Teacher-forced evaluation of pre-written text
Unit:         Per-token negative log probability, in nats
First token:  Excluded from mean loss
```

The repository also includes a PyTorch route for other systems. It was not used to produce the thesis results.

## Running the examples

Each study includes small examples that show the procedure without using your own writing.

```bash
python3 scripts/study1_protocol_visible.py \
  examples/study1_corpora \
  --reference protocol_derived
python3 scripts/study2_sentence_places_body.py examples/study2_nouns.json
python3 scripts/study3_sentence_breaks.py examples/study3_passages
python3 scripts/study4_writing_back.py examples/study4_passage01 \
  --out-dir outputs/passage01
python3 scripts/score_passage.py examples/example_passage.txt
```

For installation and commands, see [`how-to-run.md`](docs/how-to-run.md).

## Ethical attention before use

- Do not treat high loss as proof of resistance, embodiment, novelty, or value.
- Do not upload private, confidential, copyrighted, or third-party writing without permission.

See [`ethical-boundaries.md`](docs/ethical-boundaries.md) and [`start-here.md`](docs/start-here.md) before using this protocol with your own or others' writing.

## Contents

```text
situated-writing-protocol/
├── scripts/
│   ├── README.md
│   ├── study1_protocol_visible.py
│   ├── study2_sentence_places_body.py
│   ├── study3_sentence_breaks.py
│   ├── study4_writing_back.py
│   ├── score_passage.py
│   └── make_controls.py
├── _src/
│   ├── evaluation.py
│   ├── compare.py
│   ├── heatmap.py
│   └── common.py
├── docs/
│   ├── start-here.md
│   ├── how-to-run.md
│   ├── method.md
│   ├── model-configuration.md
│   └── ethical-boundaries.md
├── examples/
├── templates/            revision log
├── tests/
├── outputs/
├── README.md
├── CITATION.cff
├── LICENSE
├── requirements.txt
└── requirements-portable.txt
```

## Licence and citation

### Licence

- **Code** (`scripts/`, `_src/`, `tests/`): MIT Licence
- **Written protocol, documentation, templates, and examples** (`docs/`, `templates/`, `examples/`, prose in `README.md`): Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)

See [`LICENSE`](LICENSE) for the full text.

### Citation

If you use this protocol, please cite the thesis and this repository.

**Preferred citation (thesis):**

Vierdag, Inez. *The Loss of a Body: The Measurable Improbability of the Situated Sentence*. Research master's thesis, University of Amsterdam, 2026.

**Repository citation:**

Vierdag, Inez. *Situated Writing Protocol*. Version 1.0.0. 2026. https://github.com/inezvierdag/situated-writing-protocol
