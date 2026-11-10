"""Fixed-geometry charge screen and resistive terminal-load sensitivity."""
import argparse
import csv
import itertools
import tomllib
from pathlib import Path


def run(config, output):
    current = config["current_ma"] * 1e-3
    duration = config["phase_us"] * 1e-6
    area_cm2 = config["contact_area_mm2"] / 100
    density = current * duration * 1000 / area_cm2
    output.mkdir(parents=True, exist_ok=True)
    with (output / "charge_screen.csv").open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["material", "modeled_mC_cm2", "reported_mC_cm2", "modeled_over_reported"])
        for material, limit in config["reported_charge_injection_mc_cm2"].items():
            writer.writerow([material, density, limit, density / limit])
    with (output / "load_sweep.csv").open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["tissue_ohm", "each_contact_ohm", "terminal_V", "output_uJ_per_phase"])
        for tissue, contact in itertools.product(config["tissue_ohm"], config["contact_ohm"]):
            resistance = tissue + 2 * contact
            writer.writerow([tissue, contact, current * resistance,
                             current**2 * resistance * duration * 1e6])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(tomllib.loads(args.config.read_text()), args.output)


if __name__ == "__main__":
    main()
