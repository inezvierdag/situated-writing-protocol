# Method

The method moves in a recurring sequence: composition, measurement, reading, and revised composition.
The measurement enters after writing as one way of attending to the text: it can make a pattern visible, trouble an intuition, or return me to a sentence with another question.

## 1. Record the conditions

Before the loss value, record the conditions in which the passage was written: the constraint, formal problem, material situation, and choices I am keeping open or refusing to resolve.


This note comes first because it records the writing situation before the score begins to shape the reading.


## 2. Freeze the passage

Save the passage unchanged and give it an ID. This is the source version.
A revision becomes a new file with a new ID. The sequence remains visible: what changed, what stayed, and when the score entered the process.


## 3. Measure what is there

Run teacher-forced evaluation on the frozen passage. The model receives the text as it already exists. At each position, it assigns a probability to the token that appears after the preceding tokens.
The passage is evaluated, not generated. The writing comes first; the model enters afterwards.
Record the model, tokenizer, quantization and context policy before scoring.

```bash

python3 scripts/score_passage.py examples/example_passage.txt --level token -o out.csv

```

## 4. Read the scores

Keep the token-level scores. The word-level view is built from them.

- **Sum** shows the total loss carried by the visible word.
- **Mean** shows the average loss per sub-token.

## 5. Compare declared changes

A comparison begins with a declared change. A matched variant changes one formal relation while keeping the rest as steady as possible.
Before running a comparison, record what changes, what remains fixed, and which word, region, or passage is being read.
Length matters. Later tokens arrive with more context, so longer passages often receive lower mean loss. Keep matched variants close in length. When groups differ in length, use `study1_protocol_visible.py`, which adjusts the group comparison for token count.


### A comparison that cannot work

A causal model evaluates a token from what comes before it. If two frames are identical up to the word being measured or if there is nothing before, they will return almost the same loss value for that word. 

`I refuse the machine.` and `I am refused by the machine.` both place `I` at the beginning, with no preceding text. They do not test active and passive voice at that position.

Make sure that the frames differ **before** the target word. 

## 6. Return to the passage

The analytical work begins when the scores meet the passage, the composition note, and close reading.
A marked word can bring syntax, pacing, repetition, segmentation, or tone back into attention. It is an invitation to read again, not a conclusion about what the sentence means.

## 7. Revise, or refuse to

If the score changes my relation to the passage, record that change before scoring the next version. Use [`templates/revision_log_template.md`](../templates/revision_log_template.md).

The heatmap is a condition to write against, not a target to optimise. Rewriting until a number moves in a preferred direction produces a passage shaped by the metric. That may be a valid practice, but it is a different one and should be named as such.
A revision log written after seeing the next score becomes a justification rather than a record. No script can prevent that. It is a discipline of the research practice.


## 8. Keep the registers apart

The method brings three kinds of statement into relation without making them the same:

| Register | Example |
|---|---|
| Computational observation | `deliberately` scored 13.21 nats, the highest word in this passage. |
| Practice observation | I kept `deliberately` and moved it to the clause end. |
| Interpretation | The word carries a history the model cannot receive. |
  
The first can be reproduced. The second can be documented. The third must be argued.

## Report what does not hold

A protocol that can only confirm is not a protocol. If a declared comparison does not support the expectation that led to it, report that result.
A negative result does not undo the writing. It clarifies the limits of the particular claim the procedure was able to test.

### Words split into sub-tokens

The tokenizer may divide one visible word into several pieces. In Study 2, the first sub-token is used by default. `--subtoken mean` instead averages across the word’s pieces. These are different measurements, so state which one you used.

### Grammatical comparison frames

Keep every frame grammatical. If one sentence drops an article or introduces another grammatical disturbance, the score may register that disturbance rather than the formal relation you intend to compare.