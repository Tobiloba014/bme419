# Research architecture and verification plan

## Audit of main at 055d42e

The planar baseline has a deterministic shared synthetic fiber population, a
sparse conservative face-flux stencil with harmonic averaging, explicit
anisotropy and a reproducible three-condition sweep. Its residual measures how
well the solver satisfies the assembled linear system.

The model assumes an extruded 5 mm slab, diagonal conductivity aligned to the
grid, stepped layer interfaces, Gaussian bipolar sources and a grounded outer
box. Both Gaussians are normalized over the full grid while the solve uses only
interior nodes. Each interior contact integral therefore differs from its nominal
1 mA. The prescribed source fixes current independently of interface voltage.
The study changes CSF thickness as a geometric proxy for posture. It does not
compute contact impedance. The absolute longitudinal potential curvature loses
polarity information and the threshold population is calibrated synthetically
at 3.5 mA. The sweep cannot determine spike timing, fiber recruitment or ECAPs.

The original script couples discretization, configuration, plotting and results.
The solver extraction keeps the existing entry point and its output conventions.
All four RADO utility scripts and rendered previews are tracked on main. The
manifests record raw surface dimensions and mesh properties. A published STL
bundle is an external input. Local PyCharm revisions were not inspected. The
separate docs/model-scope-validation branch has an earlier scope README.

## Module boundaries

Use Python arrays at the computation boundary and explicit IDs for joins.
Persist run metadata as versioned JSON, input settings as TOML, and small
tabular results as CSV. Use NPZ for regular arrays and XDMF/HDF5 for larger FEM
outputs. Every artifact records units, axis order, upstream artifact hashes,
configuration, seed if used, dependency versions and Git revision before it
is included in report results. Only the planar solver and verification runner
are implemented in this layout.

| Proposed package | Input | Output |
| --- | --- | --- |
| scs.geometry | RADO release, checksum, verified units and transform | Tagged tetrahedra and boundary facets, tissue and contact maps, coordinates in m |
| scs.electrode | Contact ID and area in m², waveform in A and s, sourced interface data | Polarization in V, phase charge in C, charge density in C/m², compliance and energy estimates |
| scs.field | Mesh tags, conductivity tensors in S/m, signed contact currents or potentials with a reference | Extracellular potential in V and current balance in A, with interpolation coordinates |
| scs.neural | Compartment positions, sampled potential versus time, axon model and parameters | Per-fiber threshold, spike times in s, population weights and target/off-target labels |
| scs.ecap | Compartment membrane currents, recording transfer fields and acquisition settings | Contact-referenced waveform in V, timestamps, artifact mask and derived features |
| scs.control | Past delivered settings, observable ECAP features and optional measured impedance, constraint configuration | Estimated recruitment with uncertainty, next candidate settings, fallback state and event log |
| scs.experiments | Versioned settings, split definitions and upstream artifact IDs | Metrics, uncertainty and complete run metadata |

Keep anatomy, FEM and NEURON dependencies optional until their modules are
implemented. Define the coordinate frame, electrical reference and contact
current sign convention before exchanging fields.

## Test gates through December 8, 2026

| Target | Dependency | Pass condition |
| --- | --- | --- |
| Nov 9–15 | Existing baseline | Preserve legacy outputs and demonstrate second-order accuracy for a smooth analytic field. Next verify layered flux continuity and test domain and grid sensitivity for the legacy source. |
| Nov 16–22 | Source archive and verified geometry | Verify scale against a documented dimension, label tissue and contact surfaces, and demonstrate mesh quality and current balance on a small volume. Verify the 3-D solver on an analytic benchmark before using RADO. |
| Nov 16–22, in parallel | Traceable materials records | Record substrate, area, frequency, electrolyte, reference electrode and waveform. Fit an interface circuit only when measurements identify the parameters. Use analytical circuit checks and keep inferred values separate. |
| Nov 23–29 | Verified field interpolation | Reproduce a published NEURON reference case, then check time-step sensitivity and propagated spikes under extracellular drive. Test an ECAP forward model with a known source and verify contact referencing and recording-geometry sensitivity. |
| Nov 30–Dec 5 | Observable ECAP and a modeled recruitment reference | Compare open-loop, fixed-ECAP feedback and recruitment-aware control with identical observations, latency and limits on held-out geometry and parameter scenarios. Report recruitment error, off-target activation, energy, constraint violations and estimator failure cases. |
| Dec 6–8 | Frozen experiment inputs | Reproduce report figures from a clean environment. If later gates are incomplete, report verified baseline results and identify controller outcomes as pending. |

Start with a low-dimensional estimator and check whether different recruitment
states can produce similar observations before adding ML. Keep simulator truth
available to the evaluator only. Give the ECAP baseline a calibrated gain,
saturation and missing-measurement handling. Vary plant parameters independently
of the controller's fitted model to measure robustness. Evaluate energy using
time integration of terminal voltage times current under matched constraints.

## What the first experiment verifies

For constant diagonal conductivity and a rectangular domain, set the exact
potential to a 1 V sine product with one half-wave in each direction. The
forcing equals that potential multiplied by
`sigma_x*(pi/Lx)^2 + sigma_y*(pi/Ly)^2`. This exercises both conductivity
components and independent spacings. Each halving of grid spacing should reduce
potential error about fourfold for this smooth problem. Relative discrete L2
errors are 0.003219, 0.0008036, 0.0002008 and 0.00005020 on grids with 16, 32,
64 and 128 intervals per axis. Interface accuracy, source quadrature,
postural validity and clinical validity remain open.

## Materials intake

Keep bulk conductivity, tissue spreading resistance and electrode–electrolyte
impedance separate. Preserve raw measurements and uncertainty. The supplied
table lists a density in the IrOx coating-thickness row and omits separators
from several reported impedance and storage-capacity entries. Resolve those
against their sources. Single-frequency impedance magnitude cannot identify
both double-layer capacitance and charge-transfer resistance. Preserve SIROF
and AIROF as separate records. Store charge-storage capacity separately from
waveform-specific charge-injection measurements. Published bench values enter
the model as conditional evidence rather than implant operating limits.

## Published starting points

- [RADO-SCS 3.0 dataset](https://zenodo.org/records/3715368)
- [McIntyre–Richardson–Grill reference implementation](https://modeldb.science/3810)
- [Computational model of SCS ECAP recordings](https://pmc.ncbi.nlm.nih.gov/articles/PMC6920600/)
- [Human ECAP recordings across posture and pulse width](https://pmc.ncbi.nlm.nih.gov/articles/PMC8320888/)
- [Electrode materials review](https://pmc.ncbi.nlm.nih.gov/articles/PMC8257249/)
