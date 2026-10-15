"""Grafico de Entrega 2: Log Loss de Validacion vs numero de semillas del ensamble.

Uso: python docs/entrega2_charts.py  (lee reports/entrega2_curva_semillas.csv)
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
# Paleta categorica validada (orden fijo; slots 1-4) + trazo/marcador como codificacion secundaria
SERIES = [
    ("A3", "A3 (pura, ReLU)", "#2a78d6", "-", "o"),
    ("C4", "C4 (pura, ELU)", "#eb6834", "--", "s"),
    ("A3+C4", "A3 + C4 (pura)", "#1baf7a", "-.", "D"),
    ("E3", "E3 (destilada)", "#eda100", ":", "^"),
]


def main():
    c = pd.read_csv(ROOT / "reports" / "entrega2_curva_semillas.csv")
    fig, ax = plt.subplots(figsize=(9, 5.2), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    for key, label, color, ls, mk in SERIES:
        d = c[c.familia == key].sort_values("n_semillas")
        x = d.n_semillas * (2 if key == "A3+C4" else 1)  # A3+C4 con m semillas = 2m redes
        ax.plot(x, d.val_LogLoss, color=color, lw=2, ls=ls, marker=mk, ms=4, label=label)
        ax.annotate(f"{label}  {d.val_LogLoss.iloc[-1]:.4f}", (x.iloc[-1], d.val_LogLoss.iloc[-1]),
                    xytext=(6, 0), textcoords="offset points", va="center", fontsize=8, color=INK)
    ax.axhline(0.58431, color=INK2, lw=1, ls=(0, (4, 3)))
    ax.text(1, 0.58431 + 0.00004, "Ensemble_PLE_Fase4 (10 redes, destilada): 0.58431", color=INK2, fontsize=8, va="bottom")
    ax.set_xlabel("Numero de redes en el ensamble", color=INK2)
    ax.set_ylabel("Log Loss de Validacion (menor es mejor)", color=INK2)
    ax.set_title("Log Loss de Validacion segun el tamano del ensamble", color=INK, loc="left", fontsize=12)
    ax.grid(axis="y", color=GRID, lw=0.8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=8)
    ax.set_xlim(0.5, 52)
    ax.legend(frameon=False, fontsize=8, labelcolor=INK, loc="upper right")
    fig.tight_layout()
    out = ROOT / "docs" / "images" / "10_entrega2_curva_semillas.png"
    fig.savefig(out, facecolor=SURFACE)
    print(out)


if __name__ == "__main__":
    main()
