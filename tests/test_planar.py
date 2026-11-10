import unittest

import numpy as np

from examples.legacy_2d.main import CSF_THICKNESSES_MM, CURRENTS_MA, FIBER_EXCITABILITY, fiber_proxy, solve_field
from scs.field.verify import convergence


class PlanarTests(unittest.TestCase):
    def test_manufactured_solution_converges_at_second_order(self):
        results = convergence([16, 32, 64], 0.048, 0.020, 0.60, 0.083)
        for row in results[1:]:
            self.assertAlmostEqual(row["observed_order"], 2, delta=0.02)
        self.assertLess(results[-1]["relative_l2_error"], 3e-4)
        self.assertLess(results[-1]["relative_residual"], 1e-11)

    def test_legacy_proxy_sweeps(self):
        threshold = None
        for csf_mm, expected in zip(CSF_THICKNESSES_MM, [55, 34, 12], strict=True):
            with self.subTest(csf_mm=csf_mm):
                field, white_start, residual = solve_field(csf_mm)
                scores, _ = fiber_proxy(field, white_start)
                if threshold is None:
                    threshold = 3.5 * np.median(scores) * FIBER_EXCITABILITY
                sweep = np.sum(CURRENTS_MA[:, None] * scores >= threshold, axis=1)
                self.assertEqual(sweep[35], expected)
                self.assertEqual(sweep[0], 0)
                self.assertTrue(np.all(np.diff(sweep) >= 0))
                self.assertLess(residual, 1e-11)
