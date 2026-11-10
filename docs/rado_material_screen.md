# Running the RADO materials simulation

## Methods and limitations

The calculation treats the group's nominal 1 kHz impedance magnitude as
effective pulse resistance and scales it by measured area divided by the
assumed 1 mm² design area. Both contacts use the same material. The
circuit assumes a 600 Ω tissue load, a 5 V ceiling, and two 200 µs phases.
Delivered current is the smaller of the requested current and voltage
ceiling divided by the combined load. Pulse energy is twice the phase
duration times current squared times the combined load. The charge
screen uses the reported charge-injection values as context, not as
validated safety limits. Nominal values were taken as the first number
where the table lacked separators. PEDOT:PSS combines a glassy-substrate
impedance and a smooth-coating charge datum. IrOx's unusually high
estimated voltage reflects the 200 kΩ input and this extrapolation.

A bipolar point-source equation in an infinite isotropic medium
(0.15 S/m assumed) calculates extracellular potential at RADO-SCS axon
coordinates. Contact locations are idealized and fixed across materials,
3 mm in x from the center of fiber 1930 and separated by 10 mm in z.
The tissue resistance used by the driver is a circuit assumption,
independent of the analytic field. This is a 3D model using actual RADO
axon trajectories. It has no tetrahedral tissue mesh, tissue interfaces,
or registered STL contacts. Five 10 µm RADO trajectories were cropped
to 21 nodes and driven in NEURON using the ModelDB 3810 axon model.
The endpoint crossing measure does not distinguish propagation from
direct activation. Both time steps (5 and 2.5 µs) gave the same crossing
classification, including the zero-current and ideal 3.5 mA controls.
These five fibers are a sample and do not establish population recruitment
or clinical benefit.

## Reproduce

Keep the [RADO-SCS 3.0 archive](https://zenodo.org/records/3715368) locally.
The runner reads the five required trajectories and diameter data directly
from the ZIP. Commit scripts, documentation, and small result files to GitHub.

Follow the [main workflow instructions](../README.md). To reproduce the finer
run, copy the config, change `dt_ms` to `0.0025`, and pass the copy with
`--config`. Choose a new output directory.

The original combined CSVs under `results/` are reference runs from before
the split into driver and axon response files.
