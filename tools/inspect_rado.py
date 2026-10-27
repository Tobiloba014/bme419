r"""Inspect external STL anatomy/lead meshes without SolidWorks or COMSOL.

Usage:
    pip install trimesh numpy matplotlib

    python tools/inspect_rado.py --input "C:\Users\tobil\Downloads\RADO-SCS_3.0.zip" --output outputs/rado

Accepts an extracted STL directory or a ZIP containing STL files.

This is geometry quality control, NOT meshing, FEM, or neural simulation.
"""
import argparse
import csv
import io
import json
from pathlib import Path
import zipfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import trimesh


def files_from(source):
    source = Path(source)
    if source.is_dir():
        for path in sorted(source.rglob("*")):
            if path.suffix.lower() == ".stl":
                yield str(path.relative_to(source)), path.read_bytes()
    elif source.is_file() and source.suffix.lower() == ".zip":
        with zipfile.ZipFile(source) as archive:
            for name in sorted(archive.namelist()):
                if name.lower().endswith(".stl") and not name.endswith("/"):
                    yield name, archive.read(name)
    else:
        raise ValueError("Input must be a directory or ZIP containing STL meshes")


def load_mesh(raw):
    mesh = trimesh.load(io.BytesIO(raw), file_type="stl", force="mesh", process=False)
    if not isinstance(mesh, trimesh.Trimesh):
        raise ValueError("Not a single triangle mesh")
    if len(mesh.faces) == 0:
        raise ValueError("Mesh has no triangles")
    return mesh


def inspect(source, output, max_points=1600):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    preview = []
    for name, data in files_from(source):
        try:
            mesh = load_mesh(data)
            bounds = mesh.bounds
            row = {
                "file": name, "status": "ok", "vertices": len(mesh.vertices),
                "faces": len(mesh.faces), "watertight": bool(mesh.is_watertight),
                "extents_raw": [float(v) for v in mesh.extents],
                "bounds_min_raw": [float(v) for v in bounds[0]],
                "bounds_max_raw": [float(v) for v in bounds[1]],
                "volume_raw_cubed": float(mesh.volume) if mesh.is_watertight else None,
                "warning": "STL stores no physical units; confirm mm/m before interpreting coordinates."
            }
            # Deterministic sampled vertex cloud; a geometry PREVIEW, not a CAD drawing.
            indices = np.linspace(0, len(mesh.vertices) - 1,
                                  min(max_points, len(mesh.vertices)), dtype=int)
            preview.append((name, mesh.vertices[indices]))
        except Exception as exc:
            row = {"file": name, "status": "error", "error": str(exc)}
        rows.append(row)
    if not rows:
        raise ValueError("No STL meshes found in the supplied input")
    (output / "geometry_manifest.json").write_text(json.dumps(rows, indent=2))
    with (output / "geometry_manifest.csv").open("w", newline="") as handle:
        keys = ["file", "status", "vertices", "faces", "watertight",
                "extents_raw", "bounds_min_raw", "bounds_max_raw", "volume_raw_cubed", "error"]
        writer = csv.DictWriter(handle, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(row[k]) if isinstance(row.get(k), list)
                             else row.get(k, "") for k in keys})
    if preview:
        fig, axes = plt.subplots(1, 2, figsize=(12, 6), layout="constrained")
        for i, (name, xyz) in enumerate(preview):
            # Project 3D vertices to two planes. Not an anatomical coordinate convention.
            for ax, a, b in [(axes[0], 0, 2), (axes[1], 1, 2)]:
                ax.scatter(xyz[:, a], xyz[:, b], s=0.12, alpha=0.35,
                           label=Path(name).stem if i < 12 else None)
        for ax, title, xlabel in [(axes[0], "X-Z projection", "Raw X"),
                                   (axes[1], "Y-Z projection", "Raw Y")]:
            ax.set(title=title, xlabel=xlabel, ylabel="Raw Z")
            ax.set_aspect("equal", adjustable="datalim")
        fig.suptitle("STL geometry preview (unregistered coordinates; units unverified)")
        if len(preview) <= 12:
            axes[1].legend(fontsize=6, markerscale=9, loc="best")
        fig.savefig(output / "anatomy_preview.png", dpi=180)
        plt.close(fig)
    print(f"Inspected {len(rows)} STL files, {len(preview)} readable. Outputs: {output}")
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="RADO-SCS ZIP or extracted folder")
    parser.add_argument("--output", default="outputs/rado")
    arguments = parser.parse_args()
    inspect(arguments.input, arguments.output)
