"""Couple a 3D analytic bipolar field to RADO trajectories and NEURON."""
import argparse
import csv
import io
from pathlib import Path
from zipfile import ZipFile

import numpy as np
from neuron import h, load_mechanisms

# Group table nominal impedance (ohm), test area (mm²), charge injection (mC/cm²).
# PEDOT:PSS uses glassy-substrate impedance and smooth-coating charge data.
MATERIALS = {
    "Pt-Ir": (21200, 0.078, 0.30),
    "IrOx (SIROF)": (200000, 0.300, 1.90),
    "PEDOT:PSS": (900, 0.300, 1.36),
    "TiN": (31100, 0.150, 6.30),
}
AREA_MM2 = 1.0
SIGMA_S_M = 0.15
TISSUE_OHM = 600
REQUEST_MA = 3.5
CEILING_V = 5.0
PHASE_S = 200e-6
FIBER_IDS = (1930, 1940, 1950, 1960, 1970)


def read_fibers(archive):
    with ZipFile(archive) as bundle:
        prefix = next(name for name in bundle.namelist()
                      if name.endswith("/AxonDiameters.npy")).rsplit("/", 1)[0]

        def array(name):
            return np.load(io.BytesIO(bundle.read(f"{prefix}/{name}.npy")))

        diameters = array("AxonDiameters").ravel()
        fibers = []
        for index in FIBER_IDS:
            coords = array(f"axon_{index}")
            # Center a 21-node window on the trajectory's middle node.
            middle = ((len(coords) - 1) // 22) * 11
            window = coords[middle - 110:middle + 111]
            if not np.isclose(diameters[index], 10) or window.shape != (221, 3):
                raise ValueError(f"Incompatible RADO axon {index}")
            fibers.append(window)
        return fibers


def extracellular_mv_per_ma(points, cathode, anode):
    """Point-contact potential in an unbounded homogeneous conductor."""
    distance_cathode = np.linalg.norm(points - cathode, axis=1)
    distance_anode = np.linalg.norm(points - anode, axis=1)
    return (1 / distance_anode - 1 / distance_cathode) / (4 * np.pi * SIGMA_S_M)


def run(archive, model, output, dt_ms):
    fibers = read_fibers(archive)
    center = fibers[0][110]
    # Idealized pair fixed for all five trajectories and all materials.
    cathode = center + np.array([0.003, 0, -0.005])
    anode = center + np.array([0.003, 0, 0.005])
    if not load_mechanisms(str(model)):
        raise RuntimeError("Compile ModelDB 3810 with nrnivmodl first")
    setup = (model / "MRGaxon.hoc").read_text().split("//intracellular stimulus//", 1)[0]
    if not h(setup.replace('load_proc("nrnmainmenu")', "")):
        raise RuntimeError("Could not initialize ModelDB 3810")
    h.dt = dt_ms
    sections = []
    for i in range(20):
        sections.extend([h.node[i], h.MYSA[2*i], h.FLUT[2*i]])
        sections.extend(h.STIN[6*i+j] for j in range(6))
        sections.extend([h.FLUT[2*i+1], h.MYSA[2*i+1]])
    sections.append(h.node[20])
    steps = round(4 / dt_ms)
    times = h.Vector(np.arange(steps + 1) * dt_ms)
    waveform = np.zeros(steps + 1)
    waveform[round(0.5/dt_ms):round(0.7/dt_ms)] = 1
    waveform[round(0.75/dt_ms):round(0.95/dt_ms)] = -1
    cases = [("zero current", 0, 0, 0, 0), ("ideal current", REQUEST_MA, "", "", "")]
    for material, (impedance, measured_area, injection) in MATERIALS.items():
        resistance = TISSUE_OHM + 2 * impedance * measured_area / AREA_MM2
        current_ma = min(REQUEST_MA, 1000 * CEILING_V / resistance)
        current_a = current_ma / 1000
        cases.append((material, current_ma, REQUEST_MA / 1000 * resistance,
                      2 * current_a**2 * resistance * PHASE_S * 1e6,
                      100 * current_a * PHASE_S * 1000 / (AREA_MM2 / 100) / injection))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["axon_id", "case", "dt_ms", "delivered_mA", "required_V",
                         "pulse_energy_uJ", "charge_pct_of_reported",
                         "axon_external_peak_to_peak_mV", "left_peak_mV", "right_peak_mV",
                         "left_cross_ms", "right_cross_ms"])
        for index, coords in zip(FIBER_IDS, fibers, strict=True):
            gain = extracellular_mv_per_ma(coords, cathode, anode)
            for name, current_ma, required_v, energy, charge in cases:
                drives = []
                for section, amplitude in zip(sections, current_ma * gain, strict=True):
                    drive = h.Vector(amplitude * waveform)
                    drive.play(section(0.5)._ref_e_extracellular, times, 0)
                    drives.append(drive)
                traces = [h.Vector().record(h.node[i](0.5)._ref_v) for i in (0, 20)]
                recorded_time = h.Vector().record(h._ref_t)
                h.finitialize(-80)
                for _ in range(steps):
                    h.fadvance()
                peaks, crossings = [], []
                for trace in traces:
                    voltage = np.array(trace)
                    peaks.append(voltage.max())
                    indices = np.flatnonzero((voltage[:-1] < 0) & (voltage[1:] >= 0))
                    crossings.append(recorded_time[int(indices[0]) + 1] if indices.size else "")
                writer.writerow([index, name, dt_ms, current_ma, required_v, energy, charge,
                                 np.ptp(current_ma * gain), *peaks, *crossings])
                for drive in drives:
                    drive.play_remove()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dt-ms", type=float, choices=(0.005, 0.0025), default=0.005)
    args = parser.parse_args()
    run(args.archive, args.model, args.output, args.dt_ms)
