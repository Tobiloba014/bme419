"""Run the manufactured-solution experiment on the production planar stencil."""
import argparse
import json
import logging
import platform
import tomllib
from pathlib import Path

import numpy as np
import scipy

from scs.field.planar import solve_dirichlet


def convergence(intervals, length_m, depth_m, sigma_x_s_m, sigma_y_s_m):
    """Measure error against a 1 V sine-product solution on a rectangle."""
    if len(intervals) < 2 or any(type(n) is not int or n < 3 for n in intervals):
        raise ValueError("Specify at least two integer interval counts of three or more")
    if sorted(set(intervals)) != intervals:
        raise ValueError("Interval counts must be strictly increasing")
    results = []
    wave_x, wave_y = np.pi / length_m, np.pi / depth_m
    for n in intervals:
        axis = np.linspace(0, 1, n + 1)
        sine = np.sin(np.pi * axis)
        sine[-1] = 0
        exact = np.outer(sine, sine)
        source = (sigma_x_s_m * wave_x**2 + sigma_y_s_m * wave_y**2) * exact
        numerical, residual = solve_dirichlet(
            np.full_like(exact, sigma_x_s_m), np.full_like(exact, sigma_y_s_m),
            source, length_m / n, depth_m / n,
        )
        error = float(np.linalg.norm(numerical - exact) / np.linalg.norm(exact))
        row = {"intervals_per_axis": n, "relative_l2_error": error, "relative_residual": residual}
        if results:
            previous = results[-1]
            row["observed_order"] = float(
                np.log(previous["relative_l2_error"] / error)
                / np.log(n / previous["intervals_per_axis"])
            )
        results.append(row)
        logging.info("%d intervals: relative error %.4g, residual %.4g", n, error, residual)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    config = tomllib.loads(args.config.read_text(encoding="utf-8"))
    report = {
        "schema_version": 1,
        "experiment": "homogeneous_anisotropic_manufactured_solution",
        "config": config,
        "versions": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
        "results": convergence(**config),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(report, output, indent=2, allow_nan=False)
        output.write("\n")


if __name__ == "__main__":
    main()
