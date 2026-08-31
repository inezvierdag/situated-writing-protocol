# Examples

Everything in this folder was written for this repository. These are demonstration texts, not corpus material and not evidence for a general claim.

They are deliberately small. They run quickly, make the structure of each study visible, and sometimes return results described as “consistent with chance.” At this scale, that is not a failure. It is the appropriate answer.

## Study 1: Protocol and controls

`study1_corpora/` demonstrates *What the Protocol Makes Visible*. It contains three conditions: protocol-derived writing, plain prose, and model-generated continuations

```text
study1_corpora/
├── protocol_derived/
│ └── p01.txt ... p06.txt
├── plain_prose/
│ └── p01.txt ... p06.txt
└── model_generated/
  └── p01.txt ... p06.txt
```

Run:
```bash
python3 scripts/study1_protocol_visible.py \
examples/study1_corpora \
--reference protocol_derived
```

This is the only study in which the model generates text. The continuations were made from the first five words of each protocol-derived passage, at temperature 0.7 and seed 0:

```bash
python3 scripts/make_controls.py \
examples/study1_corpora/protocol_derived \
examples/study1_corpora/model_generated
```

The script reports raw group means, passage-length ranges, and length-adjusted group means. Read the adjusted values alongside the raw ones: the generated passages are longer here, and longer passages often receive lower mean loss simply because they offer more context.

## Study 2: Sentence position

`study2_nouns.json` demonstrates *Where the Sentence Places the Body*. It contains target nouns grouped by lexical field.

Run:

```bash
python3 scripts/study2_sentence_places_body.py examples/study2_nouns.json
```

Each noun enters both sentence frames. Six carrier verbs are rotated through each frame:

```text
The [target] {verb}s the machine.
The machine {verb}s the [target].
```

The definite article remains in both frames. Removing it would make the second frame ungrammatical; then the comparison would partly measure the missing article.

In the first frame, the target appears before the verb. The carrier verb therefore arrives too late to affect the target score, and its reported spread should be zero. The script shows this rather than asking you to take it on trust.

`--subtoken first` is the default. It scores the first piece of a target divided by the tokenizer. `--subtoken mean` averages across its pieces. Record the choice: split words can produce substantially different values under these two measures.

## Study 3: Matched variants

`study3_passages/` demonstrates *What Remains When the Sentence Breaks*. Each source passage has eight matched versions.

```text
study3_passages/
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
python3 scripts/study3_sentence_breaks.py examples/study3_passages
```

The filenames name the three interventions:

| Filename term | Intervention |
|---|---|
| `incompletion` | The sentence ends before closure, without final punctuation. |
| `lexical` | Rarer content words replace selected terms, each used once. |
| `segmentation` | The passage is divided into four- or five-word sentence units. |

The central question is the three-way interaction: when all three interventions appear together, does their combined effect exceed the sum of their separate effects?

The example contains only two source passages. That is enough to show how the design runs, not enough to support a general result. A larger study needs enough passages that one unusual source text cannot determine the outcome.

## Study 4: Writing back through loss

`study4_passage01/` demonstrates *Writing Back Through the Loss*. It contains three successive versions of one passage.

```text
study4_passage01/
	├── cycle0.txt
	├── cycle1.txt
	└── cycle2.txt
```

Run:

```bash
python3 scripts/study4_writing_back.py \
examples/study4_passage01 \
--out-dir outputs/passage01
```

For each cycle, the script creates a heatmap and a score CSV. It reports that cycle’s decile thresholds and upper-decile words, then identifies words that remain in the upper band across versions.

The heatmap shows summed loss across the sub-tokens that make up a visible word. The upper decile is recalculated inside each cycle. A word can leave the upper band even if its own loss rises, because the passage around it has changed.

Mean loss rises across these demonstration cycles. That is not a result and not a target. The example was constructed by moving high-loss words into more exposed positions, and the cycles also differ in length. It shows the procedure, not an ideal outcome.

Use [`templates/revision_log_template.md`](../templates/revision_log_template.md) to record what was retained, moved, removed, or refused between versions. Write the note before scoring the next cycle.

## One passage

## `example_passage.txt`

A single neutral passage, for the `score` utility.

```bash
python3 scripts/score_passage.py examples/example_passage.txt
```

It is the shortest way to see what the loss file looks like before working with your own text.