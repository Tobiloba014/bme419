"""Planar anisotropic conduction with zero outer Dirichlet values."""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve


def solve_dirichlet(sx, sy, source, dx_m, dy_m):
    """Solve -div(sigma grad(V)) = q on a uniform nodal grid.

    Arrays are indexed [depth, longitudinal]. Conductivities are in S/m,
    source is in A/m³, and the result is (potential in V, relative residual).
    Source and conductivity arrays include the outer boundary nodes.
    """
    sx, sy, source = (np.asarray(value, dtype=float) for value in (sx, sy, source))
    if source.ndim != 2 or min(source.shape) < 3 or sx.shape != source.shape or sy.shape != source.shape:
        raise ValueError("Expected matching 2-D grids with at least three nodes per axis")
    if not all(np.isfinite(value).all() for value in (sx, sy, source, dx_m, dy_m)):
        raise ValueError("Grid inputs must be finite")
    if np.any(sx <= 0) or np.any(sy <= 0) or dx_m <= 0 or dy_m <= 0:
        raise ValueError("Conductivity and grid spacing must be positive")
    NY, NX = source.shape
    # Interior-only finite-volume divergence discretization, Dirichlet outer edge.
    shape = (NY-2, NX-2)
    ce = 2*sx[1:-1, 1:-1]*sx[1:-1, 2:] / (sx[1:-1, 1:-1]+sx[1:-1, 2:])/dx_m**2
    cw = 2*sx[1:-1, 1:-1]*sx[1:-1, :-2] / (sx[1:-1, 1:-1]+sx[1:-1, :-2])/dx_m**2
    cn = 2*sy[1:-1, 1:-1]*sy[2:, 1:-1] / (sy[1:-1, 1:-1]+sy[2:, 1:-1])/dy_m**2
    cs = 2*sy[1:-1, 1:-1]*sy[:-2, 1:-1] / (sy[1:-1, 1:-1]+sy[:-2, 1:-1])/dy_m**2
    n = (NY-2)*(NX-2)
    p = np.arange(n).reshape(shape)
    # build sparse COO matrix: keep only within interior neighbor edges
    rows=[p.ravel()]; cols=[p.ravel()]; vals=[(ce+cw+cn+cs).ravel()]
    for conductance, dr, dc in [(-ce,0,1),(-cw,0,-1),(-cn,1,0),(-cs,-1,0)]:
        r0=slice(max(0,-dr),shape[0]-max(0,dr))
        c0=slice(max(0,-dc),shape[1]-max(0,dc))
        r1=slice(max(0,dr),shape[0]-max(0,-dr))
        c1=slice(max(0,dc),shape[1]-max(0,-dc))
        rows.append(p[r0,c0].ravel()); cols.append(p[r1,c1].ravel()); vals.append(conductance[r0,c0].ravel())
    A=coo_matrix((np.concatenate(vals), (np.concatenate(rows),np.concatenate(cols))),shape=(n,n)).tocsr()
    sol=spsolve(A, source[1:-1,1:-1].ravel())
    v=np.zeros((NY,NX)); v[1:-1,1:-1]=sol.reshape(shape)
    # Numerical check of algebraic residual; not a convergence validation.
    residual=np.linalg.norm(A @ sol - source[1:-1,1:-1].ravel()) / max(np.linalg.norm(source[1:-1,1:-1].ravel()),1e-30)
    return v, residual
