"""Plot the latest completed materials simulation."""
import argparse
import csv
import tomllib
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch


def read_run(folder):
    with (folder / "run_config.toml").open("rb") as stream:
        config = tomllib.load(stream)
    with (folder / "driver.csv").open(newline="") as stream:
        driver = list(csv.DictReader(stream))
    with (folder / "axon_response.csv").open(newline="") as stream:
        responses = list(csv.DictReader(stream))

    materials = list(config["materials"])
    fibers = config["geometry"]["fiber_ids"]
    expected = {(str(fiber), case) for fiber in fibers
                for case in ["zero current", "ideal current", *materials]}
    by_case = {(row["axon_id"], row["case"]): row for row in responses}
    if (set(by_case) != expected or len(responses) != len(expected)
            or [row["case"] for row in driver] != materials):
        raise ValueError(f"Incomplete run: {folder}")
    return config, driver, by_case


def make_figures(folder, config, driver, responses):
    labels = [row["case"] for row in driver]
    delivered = [float(row["delivered_mA"]) for row in driver]
    requested = config["driver"]["requested_ma"]
    ceiling = config["driver"]["ceiling_v"]
    fibers = config["geometry"]["fiber_ids"]

    fig, ax = plt.subplots(figsize=(7.5, 4), layout="constrained")
    bars = ax.bar(labels, delivered, color="#28677e")
    ax.bar_label(bars, fmt="%.3f", padding=4)
    ax.axhline(requested, color="#8c492b", linestyle="--",
               label=f"Requested current ({requested:g} mA)")
    ax.set(title=f"Delivered current by material | {ceiling:g} V ceiling",
           ylabel="Delivered current (mA)", ylim=(0, max(requested, *delivered, 0.1) * 1.25))
    ax.legend(loc="upper left", frameon=False)
    fig.savefig(folder / "delivered_current.png", dpi=200)
    plt.close(fig)

    activation = []
    for fiber in fibers:
        row = []
        for label in labels:
            response = responses[str(fiber), label]
            row.append(int(bool(response["left_cross_ms"] and response["right_cross_ms"])))
        activation.append(row)

    fig, ax = plt.subplots(figsize=(7.5, 4), layout="constrained")
    colors = ["#e6ebef", "#28677e"]
    ax.imshow(activation, cmap=ListedColormap(colors), vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(labels)), labels=labels)
    ax.set_yticks(range(len(fibers)), labels=fibers)
    ax.set(title="Modeled axon responses", ylabel="RADO axon ID")
    ax.legend(handles=[
        Patch(color=colors[1], label="Both ends crossed 0 mV"),
        Patch(color=colors[0], label="Criterion not met"),
    ], loc="upper center", bbox_to_anchor=(0.5, -0.10), ncol=2, frameon=False)
    fig.savefig(folder / "axon_response_heatmap.png", dpi=200)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1] / "runs"
    folders = [args.run] if args.run else sorted(root.glob("20*"), reverse=True)
    for folder in folders:
        try:
            run = read_run(folder)
        except (FileNotFoundError, KeyError, ValueError) as error:
            if args.run:
                parser.error(str(error))
            continue
        make_figures(folder, *run)
        print(f"Figures saved to {folder.resolve()}")
        return
    parser.error("No completed run found. Run main.py first.")


if __name__ == "__main__":
    main()
