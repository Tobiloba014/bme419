# BME 419 spinal cord stimulation

Compare electrode materials using RADO axon trajectories, a simplified 3D
electrical field, and NEURON.

## Run

1. Set the project interpreter to Python 3.12 with NumPy and NEURON installed.
2. Keep `RADO-SCS_3.0.zip` in Downloads or in the project's `data/` folder.
3. Download the [ModelDB 3810 ZIP](https://github.com/ModelDBRepository/3810/archive/b15daeda6ea368df0198d257f339cf5e840cf31c.zip).
   Extract it so `MRGaxon.hoc` and `AXNODE.mod` are directly inside `data/3810/`.
   In the Windows NEURON installer setup, open the mechanism compiler
   (`mknrndll` if provided), select that folder, and build `nrnmech.dll`.
   See the [NEURON mechanism instructions](https://www.neuronsimulator.org/en/latest/courses/using_nmodl_files.html)
   for the compiler supplied with the installed version.
4. Open `main.py` in the IDE and press **Run**.

Each run creates a new folder under `runs/`. It contains `driver.csv`,
`axon_response.csv`, and the settings used in `run_config.toml`. The
`case` column connects the driver and axon data.

## View the anatomy

With PyVista installed, open `render_rado_pyvista.py` and press **Run**.
It uses the same ZIP locations and saves under `runs/rado-render/`.

## Plot the results

With Matplotlib installed in the project interpreter, open
`tools/plot_results.py` and press **Run**. It uses the latest completed
simulation and saves `delivered_current.png` and `axon_response_heatmap.png`
in the same run folder.

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
