"""Run the RADO electrode materials comparison."""
import argparse
import csv
import tomllib
from pathlib import Path

import numpy as np

from scs.electrode.driver import material_cases
from scs.field.bipolar import extracellular_mv_per_ma
from scs.geometry.rado import read_fibers
from scs.neural.mrg import load_axon, stimulate


def run(config_path, archive, model, output):
    config_bytes = config_path.read_bytes()
    config = tomllib.loads(config_bytes.decode())
    geometry = config["geometry"]
    driver = config["driver"]
    neural = config["neural"]
    dt_ms = neural["dt_ms"]
    phase_us = driver["phase_us"]
    gap_us = neural["gap_us"]
    if dt_ms <= 0 or phase_us <= 0 or gap_us < 0 or 2 * phase_us + gap_us >= 3500:
        raise ValueError("The pulse must fit inside the 4 ms recording window")
    for duration_us in (500, phase_us, gap_us, 4000):
        steps = duration_us / (1000 * dt_ms)
        if not np.isclose(steps, round(steps), rtol=0, atol=1e-9):
            raise ValueError("Pulse edges and recording duration must align with the time step")

    ids = geometry["fiber_ids"]
    fibers = read_fibers(archive, ids)
    center = fibers[0][110]
    cathode = center + geometry["cathode_offset_m"]
    anode = center + geometry["anode_offset_m"]
    sections = load_axon(model)
    materials = list(material_cases(driver, config["materials"]))
    controls = [
        {"case": "zero current", "delivered_mA": 0},
        {"case": "ideal current", "delivered_mA": driver["requested_ma"]},
    ]

    output.mkdir(parents=True, exist_ok=False)
    (output / "run_config.toml").write_bytes(config_bytes)
    with (output / "driver.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(materials[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(materials)
    with (output / "axon_response.csv").open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow([
            "axon_id", "case", "dt_ms", "delivered_mA", "axon_external_peak_to_peak_mV",
            "left_peak_mV", "right_peak_mV", "left_cross_ms", "right_cross_ms",
        ])
        for index, coordinates in zip(ids, fibers, strict=True):
            gain = extracellular_mv_per_ma(
                coordinates, cathode, anode, geometry["conductivity_s_m"]
            )
            for case in controls + materials:
                current_ma = case["delivered_mA"]
                amplitudes = current_ma * gain
                response = stimulate(sections, amplitudes, dt_ms, phase_us, gap_us)
                writer.writerow([index, case["case"], dt_ms, current_ma, np.ptp(amplitudes), *response])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/material_comparison.toml"))
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.config, args.archive, args.model, args.output)


if __name__ == "__main__":
    main()
