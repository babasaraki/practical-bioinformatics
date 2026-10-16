"""Shared helpers for the Python chapters of
*Practical Approach to Learning Bioinformatics*.

Every Python chapter starts with::

    import sys; sys.path.insert(0, "..")
    from pybfx import book_data, style

`book_data` resolves a path inside the bundled ``data/`` directory from any
chapter folder; `style` applies the book's Matplotlib house style.
"""
from __future__ import annotations

import os
from pathlib import Path

__all__ = ["book_data", "style", "PALETTE", "book_root"]

PALETTE = ["#1A5276", "#117864", "#B9770E", "#922B21",
           "#6C3483", "#2E86C1", "#7D6608", "#5D6D7E"]


def book_root() -> Path:
    """Return the book's root directory, searching upward for ``data/``."""
    here = Path(os.getcwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / "data" / "MANIFEST.tsv").exists():
            return candidate
    raise FileNotFoundError(
        "Could not locate the book root (no data/MANIFEST.tsv found). "
        "Run `python scripts/fetch_data.py` from the book root first."
    )


def book_data(*parts: str) -> str:
    """Absolute path to a bundled data file, e.g. ``book_data('proteins', 'globins.fasta')``."""
    path = book_root() / "data" / Path(*parts)
    if not path.exists():
        raise FileNotFoundError(
            f"bundled data file not found: {path}\n"
            "Run `python scripts/fetch_data.py` from the book root first."
        )
    return str(path)


def style() -> None:
    """Apply the book's Matplotlib house style (call once per chapter)."""
    import matplotlib as mpl
    from cycler import cycler

    mpl.rcParams.update({
        "figure.figsize": (6, 4),
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.titleweight": "bold",
        "axes.labelsize": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": "#E5E7E9",
        "grid.linewidth": 0.6,
        "axes.prop_cycle": cycler(color=PALETTE),
        "legend.frameon": False,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
    })
