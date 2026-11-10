"""Estimate delivered current and pulse energy for the resistive driver model."""


def material_cases(driver, materials):
    requested_ma = driver["requested_ma"]
    phase_s = driver["phase_us"] * 1e-6
    area = driver["contact_area_mm2"]
    for name, material in materials.items():
        contact_ohm = material["impedance_ohm"] * material["measurement_area_mm2"] / area
        resistance = driver["tissue_ohm"] + 2 * contact_ohm
        current_ma = min(requested_ma, 1000 * driver["ceiling_v"] / resistance)
        current_a = current_ma / 1000
        yield {
            "case": name,
            "requested_mA": requested_ma,
            "delivered_mA": current_ma,
            "required_V": requested_ma / 1000 * resistance,
            "pulse_energy_uJ": 2 * current_a**2 * resistance * phase_s * 1e6,
            "charge_pct_of_reported": (
                100 * current_a * phase_s * 1000 / (area / 100)
                / material["charge_injection_mc_cm2"]
            ),
        }
