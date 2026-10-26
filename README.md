# bme419

## Model scope, limitations, and validation plan

**Status:** Educational research starting point; not a validated neuron, ECAP, or patient model. Implementation: [main.py](main.py).

### 1. What the current model demonstrates

A reproducible 2-D layered, anisotropic volume-conductor calculation compares extracellular potential and an activating-function-based index across assumed CSF thicknesses of 2.0, 3.2, and 4.4 mm. It illustrates how geometry changes electrical coupling and the fraction of 110 hypothetical fibers exceeding a fixed proxy threshold during a 0–12 mA sweep. Results are recorded in [summary.json](summary.json), [sweep_results.csv](sweep_results.csv), and three figures.

### 2. What the outputs do not mean

The activation-index fraction is **not measured neural recruitment**. It does not simulate action potentials, ECAP amplitude or latency, patient responses, or clinical safety or efficacy. The 3.5 mA reference is an assumed normalization anchor, not an experimentally established threshold. CSF scenarios are geometry comparisons, not validated predictions of posture effects. A small linear-system residual shows that the discrete equations were solved accurately; it does not establish mesh convergence or physiological validity.

### 3. Assumptions most likely to affect results

Sensitivity has not yet been quantified; these are priorities to test, not a measured ranking:

- **Activation rule:** maximum absolute longitudinal potential curvature, straight fibers at prescribed depths, and a baseline-median threshold scaled by 3.5 mA and fixed lognormal excitability (seed 419). There are no membrane dynamics or pulse timing.
- **Geometry and contacts:** simplified tissue layers, a 5 mm out-of-plane slab, and paired Gaussian source/sink contacts in place of realistic electrode surfaces and anatomy.
- **Electrical and numerical setup:** assumed tissue conductivities and white-matter anisotropy, zero potential on every outer boundary, finite domain size, and a 0.3 mm grid. These choices can alter fields and curvature; the threshold normalization may also mask changes in absolute coupling.

### 4. Next experiments before physiological claims

1. **Verify the field solver:** compare against an analytical or independently solved benchmark; check current balance and refine the mesh, enlarge the domain, and vary boundary conditions until potentials and curvature stabilize.
2. **Measure sensitivity and uncertainty:** sweep conductivities, contact geometry, slab thickness, fiber placement, threshold scaling, and excitability distributions/seeds. Report ranges and whether CSF-condition trends persist.
3. **Test neural activation:** couple fields to an established biophysical axon model with specified pulse waveform, widths, diameters, and orientations; compare thresholds and recruitment against independent published or experimental data.
4. **Validate the intended observable:** compare fields with a matched bench/phantom experiment. For ECAP claims, add a recording/volume-conduction model and validate waveform amplitude and latency against independent ECAP data. Use separate calibration and evaluation data with predefined error criteria.

Until these checks pass, report results as **model-dependent electrical and activation-proxy trends**.
