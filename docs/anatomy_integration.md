# BME 419 — Anatomy integration and model development

## What we have already simulated

The repository root's `main.py` solves a simplified **2-D layered volume conductor** with anisotropic white matter and an artificial bipolar source/sink. It sweeps three CSF thicknesses (2.0, 3.2, and 4.4 mm) and outputs electrical potential maps and a **phenomenological activating-function threshold proxy**.

This is not a neuron model. The plotted fraction above the artificial threshold is **not a clinical estimate of recruited axons or an ECAP**. The code uses synthetic excitability, idealized source placement, and zero-potential outer boundaries. A small algebraic residual is not a mesh-convergence or biological validation test.

## Why RADO-SCS?

Khadka et al.'s RADO-SCS 3.0 supplies anatomically detailed T9–T11 STL geometry with pre-positioned clinical SCS leads. Its [upstream instructions](https://github.com/nkhadka00/RADO-SCS) explicitly require separate **meshing**, **electrical FEM solving**, and optional coupling to **NEURON/MATLAB**. The GitHub repository itself holds instructions, not all anatomical STL assets. Obtain the model ZIP from the linked external release, check the source license and attribution, and do not assume it is a fully runnable simulator.

**Source attribution:** Khadka N., Liu X., Zander H., Swami J., Rogers E., Lempka S.F., Bikson M. (2019), *Realistic Anatomically Detailed Open-Source Spinal Cord Stimulation (RADO-SCS) Model*, bioRxiv, DOI: 10.1101/857946. Source describes a CC BY 4.0 release; confirm asset terms on download.

## Next reproducible step: geometry inspection

No SolidWorks required.

```bash
python -m pip install numpy matplotlib trimesh
python tools/inspect_rado.py --input /path/to/RADO-SCS_3.0.zip --output outputs/rado
```

Or pass a directory of extracted STL files. This outputs:

- `geometry_manifest.json` and `geometry_manifest.csv`: raw coordinate extents, bounds, triangle counts and watertightness for each STL.
- `anatomy_preview.png`: projected point-cloud overview, useful for checking what files were imported.

**Do not interpret raw STL coordinates as mm without verifying their units.** The preview is not a final external device drawing or simulation result. It is a check on the anatomical components available for subsequent modeling. Before solving fields, identify the tissue regions and electrode contacts, check overlap/interface topology, build a labeled 3-D volume mesh, and choose a return-current condition.

## Research work packages (ordered)

1. **Geometry and tissue map**: catalog anatomical parts and leads, identify which STL corresponds to CSF, spinal gray and white matter, epidural region, and relevant contacts; verify coordinate units, surfaces and intended stimulation level.
2. **Electrical physics**: assign literature-grounded and uncertainty-bounded anisotropic conductivities; generate a conforming tetrahedral mesh; solve `div(sigma grad(V))=0` with electrode current and appropriate boundary conditions. Perform mesh and boundary sensitivity studies.
3. **Neural response**: sample the extracellular potentials along axon compartment positions and use a published **NEURON** myelinated-axon model; estimate actual *modeled* spike initiation and activation thresholds. The root model's second-derivative index remains a baseline only.
4. **Synthetic sensing**: construct and verify an ECAP forward/recording model; don't assume simulated axon firing automatically produces a measured ECAP.
5. **Comparators and proposed redesign**: compare open-loop, conventional fixed-ECAP closed-loop, and candidate recruitment-aware predictive control under held-out postural/anatomical cases. Include latency, model error, observability, and fail-safe limits.
6. **Design decision**: select a change only after quantitative results; final hardware drawings and firmware architecture document the selected design.

## Next team-facing deliverable

Share a baseline figure of imported anatomical STLs and electrode location (with source credit and verified units), the tissue/contact manifest, and the pipeline diagram. This is **progress toward the drawing**, not a claim to have completed the physical CAD drawing.

## Limitations

No RADO anatomical meshes, 3-D FEM result, NEURON firing model, ECAP sensor model, trained ML model, or verified design improvement are included in this integration step. All of those require additional work and validation.
