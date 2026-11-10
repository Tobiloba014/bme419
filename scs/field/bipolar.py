"""Analytic field in a homogeneous, unbounded conductor."""
import numpy as np


def extracellular_mv_per_ma(points, cathode, anode, conductivity_s_m):
    """Point-contact potential in an unbounded homogeneous conductor."""
    distance_cathode = np.linalg.norm(points - cathode, axis=1)
    distance_anode = np.linalg.norm(points - anode, axis=1)
    return (1 / distance_anode - 1 / distance_cathode) / (4 * np.pi * conductivity_s_m)
