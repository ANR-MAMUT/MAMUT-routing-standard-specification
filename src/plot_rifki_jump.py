"""Plot the final arc of the frozen Rifki-30 route.

Pass fixtures/rifki30-route.json from 0nyr/routing-numerical-contracts
at revision 75905c8827f959621ea808894e28136d248d2d15.
"""

import argparse
import hashlib
import json
from bisect import bisect_left, bisect_right
from pathlib import Path

import matplotlib.pyplot as plt


FIXTURE_SHA256 = "6d0650fc5884e897344c6382f5211d20313a3bb3529ebae6d4daeb8a3763ea6e"
OUTPUT = Path(__file__).resolve().parents[1] / "figures" / "rifki30-depot-jump.pdf"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path)
    args = parser.parse_args()
    data = args.fixture.read_bytes()
    if hashlib.sha256(data).hexdigest() != FIXTURE_SHA256:
        parser.error("the fixture differs from the pinned Rifki-30 route")
    fixture = json.loads(data)

    # The fixture numbers customers in route order.
    tail = fixture["route"][-1]
    customer = fixture["provenance"]["original_route"][-1]
    arc = next(a for a in fixture["arcs"] if (a["from"], a["to"]) == (tail, 0))
    xs, ys = arc["xs"], arc["ys"]
    t = 2880
    lower, upper = bisect_left(xs, t), bisect_right(xs, t) - 1

    plt.rcParams.update({"font.family": "STIXGeneral", "font.size": 11, "pdf.fonttype": 42})
    fig, ax = plt.subplots(figsize=(11 / 2.54, 6.1 / 2.54), layout="constrained")
    color = "#24465B"
    for start in (lower - 1, upper):
        ax.plot(xs[start:start + 2], ys[start:start + 2], color=color, linewidth=1.8)
    for idx, label, fill, offset, align in (
        (lower, "attained", color, (7, -4), "left"),
        (upper, "right limit", "white", (-7, 5), "right"),
    ):
        ax.plot(t, ys[idx], "o", markersize=7, markeredgewidth=1.5,
                markerfacecolor=fill, markeredgecolor=color)
        ax.annotate(f"{ys[idx]:g} ({label})", (t, ys[idx]), xytext=offset,
                    textcoords="offset points", ha=align, va="center")

    ax.set(xlim=(t - 18, t + 18), ylim=(3062, 3148),
           xticks=[2864, 2872, 2880, 2888, 2896], yticks=[3070, 3090, 3110, 3130],
           xlabel=f"Departure from customer {customer} (instance time units)",
           ylabel="Arrival (instance time units)")
    ax.ticklabel_format(axis="both", style="plain", useOffset=False)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(direction="out", length=3)
    fig.savefig(OUTPUT, metadata={"CreationDate": None})


if __name__ == "__main__":
    main()
