"""Apply the planar extracellular field to ModelDB 3810 axon compartments."""
import argparse
import csv
from pathlib import Path

import numpy as np
from scipy.interpolate import RegularGridInterpolator

from examples.legacy_2d.main import CSF_THICKNESSES_MM, X, Y, solve_field


def run(model, output, dt_ms):
    from neuron import h, load_mechanisms

    if not load_mechanisms(str(model)):
        raise RuntimeError("Compile ModelDB 3810 with nrnivmodl first")
    # Load the original morphology and biophysics without its GUI controls.
    source = (model / "MRGaxon.hoc").read_text()
    setup = source.split("//intracellular stimulus//", 1)[0]
    setup = setup.replace('load_proc("nrnmainmenu")', "")
    if not h(setup):
        raise RuntimeError("Could not initialize ModelDB 3810")
    h.dt = dt_ms
    sections = []
    for i in range(20):
        sections.extend([h.node[i], h.MYSA[2*i], h.FLUT[2*i]])
        sections.extend(h.STIN[6*i+j] for j in range(6))
        sections.extend([h.FLUT[2*i+1], h.MYSA[2*i+1]])
    sections.append(h.node[20])
    lengths = np.array([section.L for section in sections])
    centers = np.cumsum(lengths) - lengths / 2
    x_m = (centers - centers[len(centers)//2]) * 1e-6
    segments = [section(0.5) for section in sections]
    probes = [h.node[i](0.5) for i in (0, 20)]
    steps = round(3 / dt_ms)
    # Integer sample times with edges aligned to both tested time steps.
    time = np.arange(steps + 1) * dt_ms
    waveform = np.zeros(steps + 1)
    waveform[round(0.5/dt_ms):round(0.7/dt_ms)] = 1
    waveform[round(0.75/dt_ms):round(0.95/dt_ms)] = -1
    t_vector = h.Vector(time)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["csf_mm", "depth_into_wm_mm", "current_mA", "dt_ms",
                         "left_peak_mV", "right_peak_mV", "left_crossing_ms", "right_crossing_ms"])
        for csf in CSF_THICKNESSES_MM:
            field, white_start, _ = solve_field(csf)
            interpolate = RegularGridInterpolator((Y, X), field)
            for depth_mm in (0.4, 1.5):
                points = np.column_stack((np.full(x_m.shape, white_start + depth_mm * 1e-3), x_m))
                field_mv = 1000 * interpolate(points)
                for current_ma in (0, 1, 2, 3.5, 5, 8, 12):
                    drives = []
                    for segment, gain in zip(segments, field_mv, strict=True):
                        drive = h.Vector(current_ma * gain * waveform)
                        drive.play(segment._ref_e_extracellular, t_vector, 0)
                        drives.append(drive)
                    traces = [h.Vector().record(probe._ref_v) for probe in probes]
                    recorded_time = h.Vector().record(h._ref_t)
                    h.finitialize(-80)
                    for _ in range(steps):
                        h.fadvance()
                    peaks, crossings = [], []
                    for trace in traces:
                        voltage = np.array(trace)
                        peaks.append(float(voltage.max()))
                        indices = np.flatnonzero((voltage[:-1] < 0) & (voltage[1:] >= 0))
                        crossings.append(recorded_time[int(indices[0]) + 1] if indices.size else "")
                    writer.writerow([csf, depth_mm, current_ma, dt_ms, *peaks, *crossings])
                    for drive in drives:
                        drive.play_remove()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dt-ms", type=float, choices=(0.005, 0.0025), default=0.005)
    args = parser.parse_args()
    run(args.model, args.output, args.dt_ms)


if __name__ == "__main__":
    main()
