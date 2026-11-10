"""Load and stimulate a ModelDB 3810 axon."""
import numpy as np


def load_axon(model):
    from neuron import h, load_mechanisms

    dll = model / "nrnmech.dll"
    if dll.is_file():
        h.nrn_load_dll(str(dll.resolve()))
    elif not load_mechanisms(str(model)):
        raise RuntimeError(f"No compiled NEURON mechanisms found in {model}")
    setup = (model / "MRGaxon.hoc").read_text().split("//intracellular stimulus//", 1)[0]
    if not h(setup.replace('load_proc("nrnmainmenu")', "")):
        raise RuntimeError("Could not initialize ModelDB 3810")
    sections = []
    for i in range(20):
        sections.extend([h.node[i], h.MYSA[2*i], h.FLUT[2*i]])
        sections.extend(h.STIN[6*i+j] for j in range(6))
        sections.extend([h.FLUT[2*i+1], h.MYSA[2*i+1]])
    sections.append(h.node[20])
    return sections


def stimulate(sections, amplitudes_mv, dt_ms, phase_us, gap_us):
    from neuron import h

    h.dt = dt_ms
    steps = round(4 / dt_ms)
    times = h.Vector(np.arange(steps + 1) * dt_ms)
    waveform = np.zeros(steps + 1)
    onset = round(0.5 / dt_ms)
    phase = round(phase_us / (1000 * dt_ms))
    gap = round(gap_us / (1000 * dt_ms))
    waveform[onset:onset + phase] = 1
    reverse = onset + phase + gap
    waveform[reverse:reverse + phase] = -1
    drives = []
    for section, amplitude in zip(sections, amplitudes_mv, strict=True):
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
    for drive in drives:
        drive.play_remove()
    return *peaks, *crossings
