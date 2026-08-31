# Start here

You do not need a lot of programming experience to read this repository.
You only need one distinction: the writing comes first. The model arrives afterwards. It does not know where a sentence came from, what it carries, or why I kept it. It receives the sequence on the page and assigns probabilities to what appears next.

For installation and commands, see [`how-to-run.md`](how-to-run.md).

## What the machine does

A language model reads from left to right, in small pieces called tokens. At each position, it has a distribution of expectations about what might follow.
This method gives the model a passage that is already written and asks one narrow question:
> How much probability did you assign to the word that is actually here?

The model does not revise the passage. It does not explain it. It does not decide whether it is good. It is a reader with a very particular, and rather limited, habit: it notices what it expected and what arrived instead.

## What the loss means

The number is called **loss**, and it is measured in **nats**.
- Lower loss: the model found this word relatively easy to expect here.
- Higher loss: the model assigned relatively little probability to this word here.

As a rough orientation only: values below 2 are often ordinary; around 5 may be worth noticing; above 9 marks a token the model did not strongly expect in that position.

The important word is **here**. The same word can receive a different score in another sentence. There is no stable price tag attached to a word.

A sentence can be high-loss because it is badly written, accidentally malformed, rare, punctuated strangely, or simply placed after an unexpected sequence. The number does not know the difference. That work remains with the writer and reader.
See [`ethical-boundaries.md`](ethical-boundaries.md) before working with anyone else’s writing.

## Two things to check first

### Length changes the average

Mean loss usually falls as a passage becomes longer. Later words have more preceding text to work with, and the model has more clues.
A raw comparison of short passages with long passages is therefore partly a comparison of their lengths. Study 1 accounts for this by adjusting the group comparison for token count. It does not shorten or alter passages; it makes the difference in length visible in the analysis.

### Context comes before the word

A causal model scores a token only from what comes before it. If two sentences are identical up to the word being measured, that word must receive the same score.
`I refuse the machine.` and `I am refused by the machine.` both begin with `I`. Comparing the score of `I` does not test active and passive voice. There is no prior difference for the model to register.
Before comparing target words, make sure that the frames differ before the target.

## What the scripts are for

| Script | Question |
|---|---|
| `study1_protocol_visible.py` | Do these groups of writing differ once length is accounted for? |
| `study2_sentence_places_body.py` | Does the same noun receive different loss before and after the verb? |
| `study3_sentence_breaks.py` | Do the declared formal interventions change loss separately or in combination? |
| `study4_writing_back.py` | Across revisions, which words remain in the upper-loss band? |
| `score_passage.py` | Which words did the model find relatively unexpected in this passage? |

Several scripts also report a `p` value. It asks: if there were no effect in the data, how often would a difference this large appear by chance? A small `p` can indicate that the observed difference is unlikely under that assumption. It does not show that the effect is large, important, or well interpreted.

## The order matters

1. Write the passage and record the conditions of composition.
2. Freeze the version to be studied.
3. Score the passage under a declared configuration.
4. Read the output alongside the passage and your notes.
5. Revise, keep the passage, or refuse the suggestion. Record that decision before scoring again.

If a passage is revised only until the number moves in a preferred direction, the writing has become an optimization exercise. That can be another interesting research, however it is not the practice described here.
The heatmap is a way of returning to the page. 

## Let failure remain visible

Not every declared comparison will show an effect. Report that too.
A method that can only confirm what it hoped to find has stopped being a method. A negative result can clarify the limit of a claim, the weakness of a design, or the fact that the writing did something other than the model made visible.

## Read next

- [`how-to-run.md`](how-to-run.md) — setup, commands, and file layouts
- [`method.md`](method.md) — the procedure and its sequence
- [`model-configuration.md`](model-configuration.md) — what to record with every scoring run
- [`ethical-boundaries.md`](ethical-boundaries.md) — limits on working with writing
- `templates/` — composition notes, pre-scoring memos, variant declarations, and revision logs