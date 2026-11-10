# BME 419 spinal cord stimulation

Compare electrode materials using RADO axon trajectories, a simplified 3D
electrical field, and NEURON.

## Run

1. Set the project interpreter to Python 3.12 with NumPy and NEURON installed.
2. Keep `RADO-SCS_3.0.zip` in Downloads or in the project's `data/` folder.
3. Put the [ModelDB 3810 files](https://github.com/ModelDBRepository/3810) in
   `data/3810/` with `MRGaxon.hoc` and the compiled NEURON mechanism
   (`nrnmech.dll` for a Windows DLL build).
4. Open `main.py` in the IDE and press **Run**.

Each run creates a new folder under `runs/`. It contains `driver.csv`,
`axon_response.csv`, and the settings used in `run_config.toml`. The
`case` column connects the driver and axon data.

## Where things live

| Path | Purpose |
| --- | --- |
| `main.py` | Run the comparison and save results |
| `configs/material_comparison.toml` | Material values and experiment settings |
| `scs/geometry/` | RADO axon coordinates |
| `scs/electrode/` | Current, voltage, and pulse energy |
| `scs/field/` | Extracellular voltage along each axon |
| `scs/neural/` | NEURON response |
| `examples/legacy_2d/` | Original 2D demo |

[Model assumptions and reference data](docs/rado_material_screen.md)
