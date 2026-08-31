import argparse
import csv
import json
import sys
from pathlib import Path


MLX_MODEL = "mlx-community/Mistral-7B-v0.3-4bit"
TORCH_MODEL = "mistralai/Mistral-7B-v0.3"


def default_model(backend):
    from evaluation import mlx_available
    if backend == "torch":
        return TORCH_MODEL
    if backend == "mlx":
        return MLX_MODEL
    return MLX_MODEL if mlx_available() else TORCH_MODEL


def parser(description, epilog=None):
    """An argument parser carrying the options every study takes."""
    p = argparse.ArgumentParser(
        description=description, epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", default=None,
                   help="model path or Hugging Face repo id. Defaults to "
                        f"{MLX_MODEL} on Apple silicon, {TORCH_MODEL} elsewhere.")
    p.add_argument("--backend", default="auto", choices=["auto", "mlx", "torch"],
                   help="mlx is Apple-silicon only and faster; torch runs "
                        "anywhere (default: auto)")
    return p


def open_model(args):
    """Resolve the model and load it, reporting failures readably."""
    from evaluation import load_model
    model_path = args.model or default_model(args.backend)
    try:
        return load_model(model_path, backend=args.backend)
    except RuntimeError as exc:
        sys.exit(f"error: {exc}")


def run(main):
    """Wrap a study's main() so interrupts and load failures stay readable."""
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\ninterrupted.")
    except RuntimeError as exc:
        sys.exit(f"error: {exc}")


# --------------------------------------------code-------------------------

def read_text(path):
    """Read one text file, or exit with something a reader can act on."""
    path = Path(path)
    if path.is_dir():
        sys.exit(f"error: {path} is a folder, not a text file.\n"
                 f"       This takes a single .txt file.")
    if not path.exists():
        sys.exit(f"error: no such file: {path}\n"
                 f"       Check the spelling, and check you are in the "
                 f"repository folder (cd ~/situated-writing-protocol).")
    text = path.read_text().strip()
    if not text:
        sys.exit(f"error: {path} is empty.")
    return text


def read_dir(directory):
    directory = Path(directory)
    if not directory.exists():
        sys.exit(f"error: no such folder: {directory}\n"
                 f"       Check the spelling, and check you are in the "
                 f"repository folder (cd ~/situated-writing-protocol).")
    if not directory.is_dir():
        sys.exit(f"error: {directory} is a file, not a folder.\n"
                 f"       This takes a folder of .txt files.")
    return directory


def read_texts(directory, pattern="*.txt"):
    directory = read_dir(directory)
    paths = sorted(directory.glob(pattern))
    if not paths:
        sys.exit(f"error: no {pattern} files in {directory}\n"
                 f"       Check the files are plain text and end in .txt.")
    return [(p.stem, read_text(p)) for p in paths]


def subfolders(root, what, expected):
    """List a folder's subdirectories, or explain the layout that was wanted."""
    root = read_dir(root)
    folders = sorted(d for d in root.iterdir() if d.is_dir())
    if not folders:
        sys.exit(f"error: no {what} folders inside {root}\n"
                 f"       Expected {expected}")
    return folders


def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if rows:
        with open(path, "w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


# ------------------------the report--------------------------------------

def banner(number, title, subtitle):
    print(f"\nStudy {number}: {title}")
    print(f"  {subtitle}\n")


def significance(p):
    """Plain-language reading of a p-value, so the number is not left bare."""
    if p < 0.001:
        return "very unlikely to be chance"
    if p < 0.01:
        return "unlikely to be chance"
    if p < 0.05:
        return "probably not chance"
    if p < 0.10:
        return "unclear; could be chance"
    return "consistent with chance"
