# BME 419 spinal cord stimulation research

The current baseline is a planar volume conductor and synthetic activation index.
See the [audit and research architecture](docs/research_architecture.md) and the
[RADO anatomy workflow](docs/anatomy_integration.md).

## Reproduce the baseline and verify the field solver

Use Python 3.12. Run the following from the repository root in a virtual environment.

```sh
python -m pip install -r requirements-baseline.txt
python -m unittest discover -s tests -v
python -m scs.field.verify --config configs/field_verification.toml --output runs/field-verification.json
python main.py
```

The verification command records the configuration, runtime versions, residuals
and analytic errors in JSON and requires a fresh output path. Record the Git SHA
alongside a run intended for the report. The legacy command rewrites the three
baseline PNGs, summary JSON and sweep CSV in the repository root.
