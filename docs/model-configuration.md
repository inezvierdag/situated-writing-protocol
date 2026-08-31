# Model configuration

A loss value belongs to the setup that produced it. Record that setup when you score, not afterwards from memory. (Would have spared me a lot of time if I worked like this at the moment of research.)

Use [`templates/pre_scoring_memo_template.md`](../templates/pre_scoring_memo_template.md) for each run.

## Record for every run

- Model name and checkpoint
- Tokenizer
- Quantization or precision
- Context window
- Computer, operating system, and date
- Repository commit or release version


## Thesis configuration

The results reported in the thesis were produced locally on an Apple-silicon MacBook using MLX.

```text
Model: mlx-community/Mistral-7B-v0.3-4bit
Model type: Base model.
Backend: MLX
Procedure: Teacher-forced evaluation of pre-written text
Unit: Per-token negative log probability, in nats
First token: Excluded from mean loss
```

The repository also includes a PyTorch route for other systems. I did not use this in my research but I included it to execute the research on another system.


## Keep comparisons consistent

Use the same model, tokenizer, and quantization within the same comparison. Different configurations can produce different values for the same passage. (Which can be another research altogether.)
Use the base model for questions about writing. Do not substitute an instruction-tuned model, which has been shaped towards assistant-like language.
Also do not mix MLX and PyTorch results within one comparison.


## Two methodological checks

- **Passage length:** mean per-token loss usually falls as a passage gets longer. Keep matched variants close in length. For group comparisons of passages with different lengths, use `study1_protocol_visible.py`, which adjusts for token count.
- **Target words:** exclude punctuation from a word-level target. If the target has multiple sub-tokens, record whether you use its first sub-token or the mean across its sub-tokens. Study 2 uses the first sub-token.

Keep comparison frames grammatical and different before the target word. A causal model only uses what comes before the token it scores.
