# Scripts

These scripts implement the four studies described in the thesis. Each file corresponds to one declared procedure, and each procedure is run on a frozen passage or a matched set of passages.

The scripts are intentionally separate so that the method stays legible, reproducible, and easy to relate back to the written studies.

## What each script does

| Script | Purpose |
|---|---|
| `study1_protocol_visible.py` | Compares the protocol-derived writing with controls, with length adjustment. |
| `study2_sentence_places_body.py` | Tests how the same word behaves in different clause positions. |
| `study3_sentence_breaks.py` | Compares declared formal variants such as closure, repetition, and length. |
| `study4_writing_back.py` | Handles heatmap-led recomposition across cycles. |
| `score_passage.py` | Scores a single passage and reports word-level loss. |
| `make_controls.py` | Generates Study 1's model-generated condition. The only script that writes text. |

## Reading the folder

The folder follows the order of the method rather than the order of code reuse. That means each script names a study or a scoring task directly, instead of hiding the procedure inside a generic utility layer.

This keeps the project understandable for humanities readers, who should be able to see at a glance which file belongs to which part of the research.

The shared machinery sits in `_src/`: `evaluation.py` performs the measurement, `compare.py` the statistics, `heatmap.py` the figure, and `common.py` the arguments and file handling. Nothing there is specific to a study, and nothing there needs reading to run one.

## Keep in mind

- Score the passage before interpreting it.
- Compare only frames that differ before the measured word.
- Treat length as a confound whenever passages are not comparable in size.
- Record the model, tokenizer, and procedure alongside any reported number.

## Related files

- [`start-here.md`](../docs/start-here.md)
- [`method.md`](../docs/method.md)
- [`ethical-boundaries.md`](../docs/ethical-boundaries.md)
