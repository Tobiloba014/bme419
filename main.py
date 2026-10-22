"""Reproducible 2-D electrical volume conductor + activation-index prototype.

Educational research starting point only. Not a validated neuron, ECAP, or patient model.
Run: python scs_field_model.py
Requires: numpy scipy pandas matplotlib
"""
from pathlib import Path
import csv
import json

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.sparse import diags
from scipy.sparse.linalg import spsolve

OUT = Path(__file__).resolve().parent
# Lengths in meters. x is head-to-foot (longitudinal); y is depth from posterior surface.
DX, DY = 0.3e-3, 0.3e-3
X = np.arange(-24e-3, 24e-3 + DX/2, DX)
Y = np.arange(0, 20e-3 + DY/2, DY)
NX, NY = len(X), len(Y)
XX, YY = np.meshgrid(X, Y)
THICKNESS = 5e-3  # out-of-plane thickness; assumed for 2-D planar current conservation
EPI_END = 1.2e-3
# Illustrative SI electrical conductivities; not complete validated tissue parameterization.
SIG_EPI = 0.15
SIG_CSF = 1.70
SIG_WM_X = 0.60  # longitudinal white matter anisotropy
SIG_WM_Y = 0.083 # depth direction
CURRENTS_MA = np.linspace(0, 12, 121)
CSF_THICKNESSES_MM = [2.0, 3.2, 4.4]
RNG = np.random.default_rng(419)
# Same fiber-specific variability across postural conditions. Not clinical axon thresholds.
FIBER_EXCITABILITY = RNG.lognormal(mean=0, sigma=0.22, size=110)


def tissue_properties(csf_mm):
    white_start = EPI_END + csf_mm * 1e-3
    sig_x = np.select([YY < EPI_END, YY < white_start], [SIG_EPI, SIG_CSF], SIG_WM_X)
    sig_y = np.select([YY < EPI_END, YY < white_start], [SIG_EPI, SIG_CSF], SIG_WM_Y)
    return sig_x, sig_y, white_start


def solve_field(csf_mm):
    """Solve -div(sigma grad(V))=q, with V=0 on the entire outer boundary.
    q: volumetric source-sink in A/m^3 equivalent to paired contacts within a slab.
    """
    sx, sy, white_start = tissue_properties(csf_mm)
    # Smoothized active/return current sources inside superficial epidural domain.
    # Normalized source and sink integrate to +/-1 mA in the 5mm extruded slab.
    def gaussian_contact(x0):
        return np.exp(-0.5*((XX-x0)/0.65e-3)**2 - 0.5*((YY-0.65e-3)/0.27e-3)**2)
    a, b = gaussian_contact(-5e-3), gaussian_contact(+5e-3)
    a /= np.sum(a)*DX*DY*THICKNESS
    b /= np.sum(b)*DX*DY*THICKNESS
    source = 1e-3 * (a - b)
    # Interior-only finite-volume divergence discretization, Dirichlet outer edge.
    ix = np.arange(1, NX-1); iy = np.arange(1, NY-1)
    shape = (NY-2, NX-2)
    ce = 2*sx[1:-1, 1:-1]*sx[1:-1, 2:] / (sx[1:-1, 1:-1]+sx[1:-1, 2:])/DX**2
    cw = 2*sx[1:-1, 1:-1]*sx[1:-1, :-2] / (sx[1:-1, 1:-1]+sx[1:-1, :-2])/DX**2
    cn = 2*sy[1:-1, 1:-1]*sy[2:, 1:-1] / (sy[1:-1, 1:-1]+sy[2:, 1:-1])/DY**2
    cs = 2*sy[1:-1, 1:-1]*sy[:-2, 1:-1] / (sy[1:-1, 1:-1]+sy[:-2, 1:-1])/DY**2
    n = (NY-2)*(NX-2)
    p = np.arange(n).reshape(shape)
    # build sparse COO matrix: keep only within interior neighbor edges
    from scipy.sparse import coo_matrix
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
    return v, white_start, residual


def fiber_proxy(v, white_start):
    """Non-biophysical stimulation activation INDEX, based on the activating function.
    Returns one score per hypothetical fiber, not actual action potentials.
    Fibers run along x, placed at relative depths inside dorsal-column-like white matter.
    """
    rel_depth = np.linspace(0.40e-3, 3.00e-3, len(FIBER_EXCITABILITY))
    fibers_y = white_start + rel_depth
    curvature = np.gradient(np.gradient(v, DX, axis=1), DX, axis=1)
    xmask = (X>=-14e-3)&(X<=14e-3)
    scores=[]
    for y in fibers_y:
        row=np.array([np.interp(y, Y, curvature[:,j]) for j in np.where(xmask)[0]])
        # Absolute magnitude is an activation INDEX only, not a correct cable response.
        scores.append(np.max(np.abs(row)))
    return np.asarray(scores), fibers_y


def save_field_figure(fields):
    fig, axes=plt.subplots(1,3,figsize=(13.0,4.2),layout='constrained',sharex=True,sharey=True)
    vmax=max(np.percentile(np.abs(d['v']),99.3) for d in fields)
    for ax,d in zip(axes,fields):
        img=ax.imshow(d['v']*1e3, origin='lower', extent=[X[0]*1e3,X[-1]*1e3,Y[0]*1e3,Y[-1]*1e3],aspect='auto',cmap='RdBu_r',vmin=-vmax*1e3,vmax=vmax*1e3)
        ax.axhline(EPI_END*1e3,color='white',linestyle=':',linewidth=1.4)
        ax.axhline(d['start']*1e3,color='white',linestyle='--',linewidth=1.6)
        ax.scatter([-5,5],[.65,.65],c=['black','white'],edgecolor='black',s=35,zorder=5)
        ax.set_title(f"CSF thickness {d['csf']:.1f} mm")
        ax.set_xlabel('Longitudinal distance (mm)')
        ax.set_ylim(12,0)
    axes[0].set_ylabel('Depth below dorsal surface (mm)')
    cbar=fig.colorbar(img,ax=axes,shrink=.84,pad=.015); cbar.set_label('Extracellular potential (mV) per 1 mA')
    fig.suptitle('2-D layered electrical field model: simulated postural geometries',fontsize=14,weight='bold')
    fig.savefig(OUT/'01_electric_field.png',dpi=190,facecolor='white'); plt.close(fig)


def save_recruitment_figure(results, reference_current):
    fig,ax=plt.subplots(figsize=(8,5.2),layout='constrained')
    for d in results:
        ax.plot(CURRENTS_MA,100*d['fraction'],lw=2.3,label=f"CSF {d['csf']:.1f} mm")
    ax.axvline(reference_current,color='gray',lw=1.5,ls='--',label=f'Reference {reference_current:.1f} mA')
    ax.set(xlabel='Stimulation current (mA)',ylabel='Hypothetical fibers above activation-index threshold (%)',title='Postural sensitivity of a simplified activation proxy')
    ax.set_ylim(-2,102); ax.set_xlim(0,12); ax.grid(alpha=.22); ax.legend()
    fig.savefig(OUT/'02_activation_proxy.png',dpi=190,facecolor='white'); plt.close(fig)


def main():
    fields=[]
    for csf in CSF_THICKNESSES_MM:
        v,start,residual=solve_field(csf)
        scores,y=fiber_proxy(v,start)
        fields.append(dict(csf=csf,v=v,start=start,residual=residual,scores=scores,y=y))
    # Fixed phenomenological threshold: reference 3.5 mA at median baseline score.
    # Must NOT be interpreted as measured human activation threshold.
    REF_CURRENT=3.5
    threshold=REF_CURRENT * np.median(fields[0]['scores']) * FIBER_EXCITABILITY
    for d in fields:
        d['fraction']=np.mean(CURRENTS_MA[:,None]*d['scores'][None,:] >= threshold[None,:],axis=1)
    save_field_figure(fields)
    save_recruitment_figure(fields,REF_CURRENT)
    # Plot activation-index distributions at a common current.
    fig,ax=plt.subplots(figsize=(8,4.8),layout='constrained')
    for d in fields:
        ax.plot(np.linspace(0.4,3.0,len(d['scores'])), d['scores']/np.median(fields[0]['scores']),lw=2,label=f"CSF {d['csf']:.1f} mm")
    ax.set(xlabel='Fiber depth into white matter (mm)',ylabel='Normalized activating-function index per mA',title='Electrical sensitivity along longitudinal fiber paths')
    ax.grid(alpha=.2);ax.legend();fig.savefig(OUT/'03_fiber_sensitivity.png',dpi=190,facecolor='white');plt.close(fig)
    with (OUT/'sweep_results.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['csf_thickness_mm','current_mA','activation_proxy_fraction','linear_system_relative_residual'])
        for d in fields:
            for i,cur in enumerate(CURRENTS_MA):w.writerow([d['csf'],round(float(cur),4),round(float(d['fraction'][i]),6),float(d['residual'])])
    summary={
        'model':'2-D layered anisotropic volume conductor with phenomenological activating-function threshold',
        'units':'SI internally; plots mm, mA, mV',
        'assumptions':{'slab_thickness_mm':THICKNESS*1e3, 'electrode_centers_x_mm':[-5,5], 'depth_mm':0.65,
                       'csf_thicknesses_mm':CSF_THICKNESSES_MM,'reference_current_mA':REF_CURRENT,
                       'reference_threshold':'median 1mA activating-function index * reference current * fixed random excitability'},
        'at_reference_current':[
             dict(csf_mm=d['csf'], fraction_above_proxy_threshold=float(np.interp(REF_CURRENT,CURRENTS_MA,d['fraction'])), residual=float(d['residual'])) for d in fields
        ],
        'limitations':'NOT physiological prediction, not ECAP, not NEURON; not tested against literature and no convergence study; no safety/efficacy conclusions.'
    }
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2))
    for d in fields:
        print(f"CSF {d['csf']} mm | proxy recruitment @ {REF_CURRENT} mA {np.interp(REF_CURRENT,CURRENTS_MA,d['fraction']):.1%} | linear residual {d['residual']:.1e}")
    print('Saved three plots, CSV and summary JSON.')

if __name__=='__main__':main()
