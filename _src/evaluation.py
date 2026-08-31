"""Teacher-forced per-token loss, aggregated to words.

Every study in this protocol rests on one operation: take a pre-written text,
run it through a fixed model, and record the negative log probability the model
assigned to each token in its actual context. Nothing is generated. The text is
written before it is evaluated.

Values are in nats (natural log). To read them as bits, divide by ln(2).

Two backends
------------
**mlx** — fast, Apple silicon only. (Which I used throughout.)

**torch** — runs anywhere PyTorch runs: Linux, Windows, Intel Mac, CPU or GPU.
Slower on and heavier.

`load_model` picks one automatically: MLX if it is installed and the model is
an MLX checkpoint, otherwise torch. Pass `backend=` to force a choice.

The two do not produce identical numbers for the same model, because
the checkpoints differ in quantization. Differences are small but real.
"""

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class Word:
    """One whitespace-delimited word, with the model's loss value for it."""
    text: str
    start: int
    end: int
    loss_sum: float   # summed over the word's sub-tokens
    n_tokens: int
    # Each sub-token's own (text, loss), in order. Kept so you can evaluate a part of a word 
    # see evaluate_target, which drops trailing punctuation.
    parts: tuple = ()

    @property
    def loss_mean(self) -> float:
        """Per-token mean. Use this to compare words of unequal token length."""
        return self.loss_sum / self.n_tokens


def mlx_available():
    try:
        import mlx.core  #Mac Silicon only
        import mlx_lm    
        return True
    except ImportError:
        return False


def torch_available():
    try:
        import torch         
        import transformers  
        return True
    except ImportError:
        return False


class _MLXModel:
    """this is for Mac silicon only!!"""

    backend = "mlx"

    def __init__(self, model_path):
        from mlx_lm import load
        self.model, self.tokenizer = load(model_path)
        self.name = str(model_path)

    def encode(self, text):
        enc = self.tokenizer._tokenizer(text, return_offsets_mapping=True)
        return enc["input_ids"], enc["offset_mapping"]

    def log_probs(self, ids):
        import numpy as np
        import mlx.core as mx
        import mlx.nn as nn

        logits = self.model(mx.array(ids[:-1])[None])
        lp = nn.log_softmax(logits[0], axis=-1)
        mx.eval(lp)
        return np.array(lp.tolist(), dtype=np.float32)


class _TorchModel:
    """This is for PyTorch."""

    backend = "torch"

    def __init__(self, model_path, device=None, quiet=True):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        if quiet:

            import logging
            import warnings
            import transformers
            transformers.logging.set_verbosity_error()
            transformers.utils.logging.disable_progress_bar()
            for name in ("transformers", "huggingface_hub"):
                logging.getLogger(name).setLevel(logging.ERROR)
            warnings.filterwarnings("ignore", module="huggingface_hub.*")

        if device is None:
            if torch.cuda.is_available():
                device = "cuda"
            elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"
        self.device = device
        self.name = str(model_path)

        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        # float32 on CPU: float16 is very very slow there.
        dtype = torch.float32 if device == "cpu" else torch.float16
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path, dtype=dtype).to(device).eval()

    def encode(self, text):
        enc = self.tokenizer(text, return_offsets_mapping=True)
        return enc["input_ids"], enc["offset_mapping"]

    def log_probs(self, ids):
        import torch

        with torch.no_grad():
            logits = self.model(torch.tensor([ids[:-1]], device=self.device)).logits
            lp = torch.log_softmax(logits[0].float(), dim=-1)
        return lp.cpu().numpy()


def load_model(model_path, backend="auto"):
    """Load a model for evaluation.


    """
    if backend not in ("auto", "mlx", "torch"):
        raise ValueError(f"unknown backend {backend!r}; use auto, mlx, or torch")

    if backend == "mlx":
        if not mlx_available():
            raise RuntimeError(
                "MLX is not installed. "
                "MLX runs only on Apple silicon; use --backend torch instead.")
        return _MLXModel(model_path)

    if backend == "torch":
        if not torch_available():
            raise RuntimeError(
                "PyTorch/transformers are not installed."
                "Run: pip install torch transformers")
        return _TorchModel(model_path)


    failures = []
    for available, make in ((mlx_available, _MLXModel), (torch_available, _TorchModel)):
        if not available():
            continue
        try:
            return make(model_path)
        except Exception as exc:                # noqa: BLE001 - report, then try the next
            failures.append(f"  {make.backend}: {type(exc).__name__}: {exc}")

    if not failures:
        raise RuntimeError(
            "No evaluation backend is installed.\n"
            "  On Apple silicon:  pip install mlx mlx-lm\n"
            "  Anywhere else:     pip install torch transformers")

    raise RuntimeError(
        f"Could not load {model_path!r} with any available backend.\n"
        + "\n".join(failures)
        + "\n\nCheck the model name or path. MLX checkpoints (names usually "
          "containing\n'mlx-community') need the mlx backend; Hugging Face"
          "checkpoints need torch.")


def token_losses(model, text):
    """Per-token loss for every token after the first.

    Returns (offsets, losses), aligned and equal length. `offsets` are
    (start, end) character spans into `text`. The first token is dropped
    because nothing precedes it to condition on.

    The loss value depends on the tokenizer. 
    Compare texts evaluated with the same tokenizer.
    """
    import numpy as np

    ids, offsets = model.encode(text)
    if len(ids) < 2:
        return [], []

    lp = model.log_probs(ids)
    targets = np.array(ids[1:], dtype=np.int64)
    losses = [float(-lp[i, targets[i]]) for i in range(len(targets))]

    return offsets[1:], losses


def to_words(text, offsets, losses):
    """Group token losses into words, summing each word's sub-tokens.

    
    """
    spans = []
    current = None
    previous_end = None

    for (start, end), loss in zip(offsets, losses):
        if start == end:
            continue
        token_text = text[start:end]

        if not token_text.strip():         
            current = None
            previous_end = end
            continue

        starts_word = (
            token_text[:1].isspace()                    
            or (previous_end is not None and start > previous_end) 
        )
        if starts_word:
            current = None

        if current is None:
            current = [start, end, []]
            spans.append(current)
        else:
            current[1] = end
        current[2].append((token_text.strip(), loss))
        previous_end = end

    return [
        Word(text=text[s:e].strip(), start=s, end=e,
             loss_sum=sum(loss for _, loss in parts), n_tokens=len(parts),
             parts=tuple(parts))
        for s, e, parts in spans if parts
    ]


def evaluate_text(model, text):
    """Evaluate a text. Returns a list of Word."""
    return to_words(text, *token_losses(model, text))


def mean_loss(words):
    """Mean loss per *token* across a text.

    Token-weighted, not word-weighted: a word split into four sub-tokens
    contributes four times as much as a single-token word, matching how the
    model much loss value the token actually contained.
    """
    total_tokens = sum(w.n_tokens for w in words)
    if not total_tokens:
        return 0.0
    return sum(w.loss_sum for w in words) / total_tokens


PUNCTUATION = ".,;:!?'\"()[]—–-"


def evaluate_target(model, sentence, target, first_subtoken=False):
    """Return the loss for the first occurrence of one target word.

    Used in Study 2, where the unit of interest is one word within a sentence.
    Returns the target's own sub-tokens, or `None` when the target is absent.

    Punctuation is excluded. The heatmap keeps `body.` together for reading on
    the page, but a target comparison measures `body`, not the noun joined to
    the sentence ending.

    By default, the returned value covers all sub-tokens in the target word and
    reports their mean. Use `first_subtoken=True` to measure only its first
    sub-token.

    These are different choices. A tokenizer may divide `metaphor` into `met`
    and `aphor`: the first part can carry much of the loss, while the next part
    arrives after it. Record which measure you use.
    """

    for word in evaluate_text(model, sentence):
        if word.text.strip(PUNCTUATION).lower() != target.lower():
            continue
        parts = [(txt, loss) for txt, loss in word.parts if txt.strip(PUNCTUATION)]
        if not parts:
            return None
        if first_subtoken:
            parts = parts[:1]
        return Word(text=word.text.strip(PUNCTUATION), start=word.start,
                    end=word.end, loss_sum=sum(l for _, l in parts),
                    n_tokens=len(parts), parts=tuple(parts))
    return None


def words_to_dicts(words):
    """for CSV/JSON output."""
    return [{k: v for k, v in asdict(w).items() if k != "parts"}
            | {"loss_mean": w.loss_mean} for w in words]
