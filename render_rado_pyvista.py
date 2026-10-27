"""Render RADO-SCS anatomical STL surfaces (no CAD software needed).

Install: python -m pip install pyvista vtk numpy
Run:
  python render_rado_pyvista.py --input "C:/Users/tobil/Downloads/RADO-SCS_3.0.zip"
Optional: --include-drg, --off-screen, --output outputs/rado/render

Geometry visualization ONLY: NOT an FEM mesh or a physiological simulation.
STLs contain no reliable coordinate units; axes therefore show raw units.
"""
import argparse
import json
import tempfile
import zipfile
from pathlib import Path

import pyvista as pv

TISSUES = {
    "neuro_epiduralspace-1.stl": ("Epidural space", "#E7B36B", 0.09),
    "neuro_csf-1.stl": ("CSF", "#49AED6", 0.17),
    "neuro_meninges-1.stl": ("Meninges", "#6CAD89", 0.12),
    "neuro_whitemater-1.stl": ("White matter", "#ECE1B9", 0.50),
    "neuro_greymater-1.stl": ("Gray matter", "#BD6987", 0.97),
}
DRG = {
    f"neuro_dorsal _roots_drg_leads-{i}.stl":
    (f"DRG candidate {i}", "#E24B4B", 1.0)
    for i in range(1, 5)
}


def select_sources(source, names):
    """Match the actual file basenames, including RADO's 'T8-10 - ' prefix."""
    source = Path(source)
    if source.is_dir():
        paths = [p for p in source.rglob('*') if p.suffix.lower() == '.stl']
        for key in names:
            matches = [p for p in paths if p.name.lower().endswith(key)]
            if len(matches) == 1:
                yield key, matches[0], None
            elif len(matches) != 1:
                print(f"WARNING: Expected one match for {key}, found {len(matches)}")
    elif source.is_file() and source.suffix.lower() == '.zip':
        with zipfile.ZipFile(source) as zf:
            entries = [name for name in zf.namelist() if name.lower().endswith('.stl')]
            with tempfile.TemporaryDirectory() as tmp:
                for key in names:
                    matches = [name for name in entries if Path(name).name.lower().endswith(key)]
                    if len(matches) == 1:
                        # Avoid path traversal and filename collisions: write under our own basename.
                        dest = Path(tmp) / key
                        dest.write_bytes(zf.read(matches[0]))
                        yield key, dest, matches[0]
                    else:
                        print(f"WARNING: Expected one match for {key}, found {len(matches)}")
    else:
        raise ValueError('--input must be the RADO-SCS ZIP or extracted STL directory')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', default='outputs/rado/render')
    parser.add_argument('--include-drg', action='store_true', help='Show DRG candidates, NOT confirmed epidural SCS contacts')
    parser.add_argument('--off-screen', action='store_true', help='Save PNG without opening a 3D window')
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    requested = dict(TISSUES)
    if args.include_drg:
        requested.update(DRG)

    plotter = pv.Plotter(off_screen=args.off_screen, window_size=(1500, 1100))
    plotter.set_background('#111922')
    metadata = []
    actors = []
    for key, path, archive_name in select_sources(args.input, requested):
        label, color, opacity = requested[key]
        mesh = pv.read(path)
        if not isinstance(mesh, pv.PolyData):
            mesh = mesh.extract_surface()
        if mesh.n_cells == 0:
            print('WARNING: Empty geometry', key)
            continue
        actor = plotter.add_mesh(mesh, color=color, opacity=opacity, smooth_shading=True,
                                 show_edges=False, name=key, label=label)
        actors.append((key, actor))
        metadata.append({'file': archive_name or str(path), 'label': label,
                         'points': mesh.n_points, 'faces': mesh.n_cells,
                         'bounds_raw': [float(x) for x in mesh.bounds],
                         'surface_manifold': bool(mesh.is_manifold)})
        print(f'Loaded {label}: {mesh.n_points:,} points, {mesh.n_cells:,} faces')

    if not metadata:
        raise RuntimeError('No matching STL files loaded; check the ZIP content/filenames')

    plotter.add_text('RADO-SCS | Anatomical reference geometry', position='upper_left',
                     font_size=15, color='white')
    plotter.add_text('Unverified STL units • Geometry only • Not FEM or a finished design',
                     position='lower_left', font_size=9, color='white')
    plotter.add_legend(bcolor='#202c38', border=True, size=(0.26, 0.30))
    plotter.show_axes()
    plotter.reset_camera()
    plotter.camera.zoom(1.25)
    png = out / 'rado_surface_render.png'

    def capture():
        plotter.screenshot(str(png))
        print(f'Saved screenshot: {png.resolve()}')

    if not args.off_screen:
        plotter.add_text('Mouse: rotate / zoom | S: save PNG', position='upper_right',
                         font_size=9, color='white')
        plotter.add_key_event('s', capture)
        plotter.add_key_event('S', capture)
    (out / 'render_manifest.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print('The render is an anatomical reference; DRG objects are not proven SCS contacts.')
    if args.off_screen:
        plotter.render()
        capture()
        plotter.close()
    else:
        plotter.show(auto_close=False)
        capture()
        plotter.close()


if __name__ == '__main__':
    main()
