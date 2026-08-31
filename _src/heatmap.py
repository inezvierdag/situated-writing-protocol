"""Render word-level losses as a grid heatmap image.

Two separate things live in this module, and they are not the same rule:

  render()      A continuous colour scale from the passage's own lowest to its own highest word-level loss. 
                This is the figure--cool (blue) where low loss value, warm (red) where high loss value. 
                (i went for red and blue but you could try other colours)

  top_decile()  The passage's own 90th / 10th percentile cut-offs, used to
                *name* which words count as high or low cost in writing.

                
"""

import matplotlib
matplotlib.use("Agg")            

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np

# Size of the heatmap.
WORDS_PER_ROW = 8
CELL_WIDTH_IN = 1.3
CELL_HEIGHT_RATIO = 0.7
DPI = 300
MIN_FONTSIZE = 11.0


LIGHT_TEXT_ABOVE = 0.7

HIGH_PERCENTILE = 90
LOW_PERCENTILE = 10


def top_decile(words, high=HIGH_PERCENTILE, low=LOW_PERCENTILE):
    """Passage-relative decile cut-offs, from this text alone.

    Returns (low_cut, high_cut) over (summed) word loss. 
    Used for reporting which words are high or low cost.
    """
    losses = [w.loss_sum for w in words]
    if not losses:
        return 0.0, 0.0
    return float(np.percentile(losses, low)), float(np.percentile(losses, high))


def classify(words):
    """Tags each word 'high', 'low', or 'mid' against this passage's 10% highest or lowest loss."""
    low_cut, high_cut = top_decile(words)
    return [(w, "high" if w.loss_sum >= high_cut
             else "low" if w.loss_sum <= low_cut
             else "mid") for w in words]


def _shrink_to_fit(fig, labels, cell_width_pt, start_size):
    """
    A long word must never be too big so this steps each label down until it fits in the box/cell.
    """
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    floor = MIN_FONTSIZE * 0.6

    for label in labels:
        size = start_size
        while size > floor:
            width_pt = label.get_window_extent(renderer=renderer).width * 72.0 / fig.dpi
            if width_pt <= cell_width_pt * 0.92:
                break
            size -= 0.5
            label.set_fontsize(size)
            fig.canvas.draw()


def render(words, out_path, title="", words_per_row=WORDS_PER_ROW,
           cell_width=CELL_WIDTH_IN, dpi=DPI):
    """
    You can use: .jpg, .png, and .pdf
    Each word is one cell, coloured by its loss
    """
    if not words:
        raise ValueError("nothing to evaluated")

    losses = [w.loss_sum for w in words]
    low, high = min(losses), max(losses)
    if high == low:
        high = low + 1e-6

    cmap = plt.get_cmap("coolwarm")
    norm = mcolors.Normalize(vmin=low, vmax=high)

    n_rows = -(-len(words) // words_per_row)      
    cell_height = cell_width * CELL_HEIGHT_RATIO
    base_fontsize = max(MIN_FONTSIZE, cell_width * 9.0)

    fig, ax = plt.subplots(
        figsize=(words_per_row * cell_width, n_rows * cell_height + 1.4))
    ax.set_xlim(0, words_per_row)
    ax.set_ylim(0, n_rows)
    ax.axis("off")
    fig.patch.set_facecolor("white")



    fig.canvas.draw()
    cell_width_px = (ax.transData.transform((1, 0))[0]
                     - ax.transData.transform((0, 0))[0])
    cell_width_pt = cell_width_px * 72.0 / fig.dpi

    labels = []
    for i, word in enumerate(words):
        row = n_rows - 1 - i // words_per_row
        col = i % words_per_row
        shade = norm(word.loss_sum)
        colour = cmap(shade)

        ax.add_patch(plt.Rectangle((col, row), 1, 1,
                                   facecolor=colour, edgecolor=colour, linewidth=0))
        labels.append(ax.text(
            col + 0.5, row + 0.5,
            word.text.replace("\n", "↵").replace("\t", "→"),
            ha="center", va="center", fontsize=base_fontsize,
            color="white" if shade > LIGHT_TEXT_ABOVE else "black"))

    _shrink_to_fit(fig, labels, cell_width_pt, base_fontsize)

    scalar_map = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    scalar_map.set_array([])
    bar = fig.colorbar(scalar_map, ax=ax, orientation="horizontal",
                       fraction=0.06, pad=0.04, aspect=30)
    bar.set_label("per-word cross-entropy loss  (cool = easy · warm = expensive)",
                  fontsize=max(9, base_fontsize * 0.75))
    bar.ax.tick_params(labelsize=max(8, base_fontsize * 0.7))

    if title:
        ax.set_title(title, fontsize=max(11, base_fontsize), pad=10)

    fig.tight_layout()
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
