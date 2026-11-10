# BME 419 spinal cord stimulation

Compare how electrode materials affect delivered current and simulated axon
responses. The main workflow uses RADO axon coordinates with an idealized 3D
bipolar field. See [model assumptions](docs/rado_material_screen.md) for the
simplifications and reference data.

## Run the main comparison

Use Python 3.12 with NumPy and NEURON:

```sh
python -m pip install numpy==2.3.5 neuron==9.0.2
```

Keep the RADO ZIP on your computer. The runner reads it directly. Set up the
[compiled ModelDB 3810 axon model](docs/materials_axon_pilot.md#reproduction)
for your NEURON installation. The compilation example there uses Linux.
On Windows, supply the directory containing your compiled mechanisms and
`MRGaxon.hoc`. The simulation command itself works in PowerShell with your paths.

```powershell
python main.py --archive "$env:USERPROFILE/Downloads/RADO-SCS_3.0.zip" --model "C:/path/to/3810" --output runs/baseline
```

The output directory must be new. The default settings are in
`configs/material_comparison.toml`. Pass `--config` to run a different file.

| Output | Contents |
| --- | --- |
| `driver.csv` | One row per material with requested and delivered current, required voltage, and biphasic pulse energy |
| `axon_response.csv` | One row per axon and case, including zero and ideal-current controls |
| `run_config.toml` | Exact copy of the settings used |

Join the material rows using the `case` column. Blank crossing times mean the
corresponding end node did not cross 0 mV during the recording window.

## Code map

| File | Responsibility |
| --- | --- |
| `main.py` | Runs the steps in order and writes the three outputs |
| `scs/geometry/rado.py` | Reads the RADO fiber coordinates and diameters |
| `scs/electrode/driver.py` | Converts material measurements into estimated load and delivered current |
| `scs/field/bipolar.py` | Calculates extracellular voltage per mA at each compartment |
| `scs/neural/mrg.py` | Runs NEURON using those compartment voltages |

## Earlier experiments

The original 2D demo and its saved outputs live in `examples/legacy_2d/`.
To run it, install `requirements-baseline.txt` and use
`python -m examples.legacy_2d.main` from the repository root. Run the baseline
tests with `python -m unittest discover -s tests -v`.
