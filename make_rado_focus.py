
"""RADO-SCS 3D anatomical visualization.

Loads selected STL files directly from the RADO-SCS 3.0 ZIP archive
or an extracted directory.

Produces:
    focused_3d.png
    focused_manifest.json

Dependencies:
    pip install numpy matplotlib trimesh

This is anatomical visualization, NOT an electrical FEM simulation.
STL coordinates are displayed in raw units until verified.
"""

import argparse
import io
import json
import zipfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import trimesh


# ============================================================
# CONFIGURATION
# ============================================================

INCLUDE_DRG_LEADS = False

MAX_POINTS_PER_COMPONENT = 12000

TISSUE_FILES = {
    "neuro_csf-1.stl": {
        "label": "Cerebrospinal Fluid",
        "color": "#58b6ed",
        "alpha": 0.035,
    },
    "neuro_epiduralspace-1.stl": {
        "label": "Epidural Space",
        "color": "#efb366",
        "alpha": 0.025,
    },
    "neuro_greymater-1.stl": {
        "label": "Gray Matter",
        "color": "#c56b84",
        "alpha": 0.75,
    },
    "neuro_meninges-1.stl": {
        "label": "Meninges",
        "color": "#88c0a8",
        "alpha": 0.08,
    },
    "neuro_whitemater-1.stl": {
        "label": "White Matter",
        "color": "#e2d1ab",
        "alpha": 0.35,
    },
}

LEAD_FILES = {
    f"neuro_dorsal _roots_drg_leads-{i}.stl": {
        "label": f"DRG Lead Candidate {i}",
        "color": "#e34b4b",
        "alpha": 0.95,
    }
    for i in range(1, 5)
}


# ============================================================
# FILE HANDLING
# ============================================================

def read_stl_files(source):
    source = Path(source)

    if source.is_dir():
        for path in sorted(source.rglob("*")):
            if path.suffix.lower() == ".stl":
                yield path.name, path.read_bytes()

    elif source.is_file() and source.suffix.lower() == ".zip":
        with zipfile.ZipFile(source) as archive:
            for name in sorted(archive.namelist()):
                if name.lower().endswith(".stl"):
                    yield Path(name).name, archive.read(name)

    else:
        raise ValueError(
            "Input must be a ZIP archive or an extracted STL directory."
        )


def identify_component(filename, include_leads):
    """Identify STL component using actual RADO naming patterns."""

    # Actual archive filenames include prefixes such as:
    # T8-10 - neuro_CSF-1.STL

    name = filename.lower()

    for key, metadata in TISSUE_FILES.items():
        if name.endswith(key):
            return metadata

    if include_leads:
        for key, metadata in LEAD_FILES.items():
            if name.endswith(key):
                return metadata

    return None


def load_mesh(data):
    mesh = trimesh.load(
        io.BytesIO(data),
        file_type="stl",
        force="mesh",
        process=True,
    )

    if not isinstance(mesh, trimesh.Trimesh):
        raise ValueError("Invalid triangle mesh")

    if len(mesh.faces) == 0:
        raise ValueError("Mesh contains no triangles")

    return mesh


# ============================================================
# GEOMETRY UTILITIES
# ============================================================

def sample_surface(mesh, count, seed=419):
    """Return reproducibly sampled surface points."""

    rng = np.random.default_rng(seed)

    # Sampling vertices avoids failures on invalid triangles.
    vertices = mesh.vertices

    if len(vertices) <= count:
        return vertices.copy()

    indices = rng.choice(
        len(vertices),
        size=count,
        replace=False,
    )

    return vertices[indices]


def equal_3d_axes(ax, bounds):
    """Set equal spatial scaling across all three axes."""

    bounds = np.asarray(bounds, dtype=float)

    center = bounds.mean(axis=0)
    size = np.max(bounds[1] - bounds[0])

    if size <= 0:
        size = 1.0

    radius = size / 2

    ax.set_xlim(center[0] - radius, center[0] + radius)
    ax.set_ylim(center[1] - radius, center[1] + radius)
    ax.set_zlim(center[2] - radius, center[2] + radius)


# ============================================================
# MAIN VISUALIZATION
# ============================================================

def build_visualization(source, output, include_leads=False):

    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)

    components = []
    manifest = []
    missing = []

    expected = list(TISSUE_FILES)

    if include_leads:
        expected += list(LEAD_FILES)

    matched = set()

    print("\nLoading RADO-SCS anatomical structures...\n")

    for filename, data in read_stl_files(source):

        metadata = identify_component(
            filename,
            include_leads,
        )

        if metadata is None:
            continue

        try:
            mesh = load_mesh(data)

            points = sample_surface(
                mesh,
                MAX_POINTS_PER_COMPONENT,
            )

            components.append({
                "filename": filename,
                "label": metadata["label"],
                "color": metadata["color"],
                "alpha": metadata["alpha"],
                "points": points,
                "bounds": mesh.bounds,
            })

            manifest.append({
                "filename": filename,
                "component": metadata["label"],
                "vertices": int(len(mesh.vertices)),
                "faces": int(len(mesh.faces)),
                "watertight": bool(mesh.is_watertight),
                "bounds_raw": mesh.bounds.tolist(),
                "extents_raw": mesh.extents.tolist(),
                "units": "unverified",
            })

            for key in expected:
                if filename.lower().endswith(key):
                    matched.add(key)

            print(
                f"[OK] {metadata['label']}: "
                f"{len(mesh.vertices):,} vertices, "
                f"{len(mesh.faces):,} triangles"
            )

        except Exception as exc:
            print(f"[ERROR] {filename}: {exc}")

    missing = sorted(set(expected) - matched)

    if missing:
        print("\nMissing components:")
        for name in missing:
            print(f"  - {name}")

    if not components:
        raise RuntimeError(
            "No anatomical components matched the requested filenames."
        )

    # --------------------------------------------------------
    # SAVE MANIFEST
    # --------------------------------------------------------

    with (output / "focused_manifest.json").open(
        "w", encoding="utf-8"
    ) as file:
        json.dump(manifest, file, indent=2)

    # --------------------------------------------------------
    # CREATE 3D FIGURE
    # --------------------------------------------------------

    fig = plt.figure(figsize=(14, 10))

    ax = fig.add_subplot(111, projection="3d")

    # Draw larger, more transparent structures first.
    components.sort(
        key=lambda c: c["alpha"]
    )

    for component in components:

        points = component["points"]

        ax.scatter(
            points[:, 0],
            points[:, 1],
            points[:, 2],
            s=0.7,
            c=component["color"],
            alpha=component["alpha"],
            label=component["label"],
            depthshade=False,
            rasterized=True,
        )

    # Determine complete model bounds.
    global_min = np.min(
        [c["bounds"][0] for c in components],
        axis=0,
    )

    global_max = np.max(
        [c["bounds"][1] for c in components],
        axis=0,
    )

    equal_3d_axes(
        ax,
        np.array([global_min, global_max]),
    )

    ax.set_xlabel("Raw X")
    ax.set_ylabel("Raw Y")
    ax.set_zlabel("Raw Z")

    ax.set_title(
        "RADO-SCS Anatomical Model\n"
        "Spinal Cord Tissue Geometry",
        fontsize=15,
        fontweight="bold",
        pad=20,
    )

    ax.view_init(
        elev=18,
        azim=-65,
    )

    ax.legend(
        loc="upper left",
        bbox_to_anchor=(1.02, 1),
        fontsize=9,
        markerscale=3,
    )

    fig.text(
        0.5,
        0.025,
        "Source: RADO-SCS 3.0 | "
        "Raw STL coordinates; units not yet verified | "
        "Not a FEM or neural simulation",
        ha="center",
        fontsize=9,
        color="dimgray",
    )

    fig.subplots_adjust(
        right=0.80,
        bottom=0.08,
    )

    output_image = output / "focused_3d.png"

    fig.savefig(
        output_image,
        dpi=200,
        facecolor="white",
        bbox_inches="tight",
    )

    plt.close(fig)

    print("\n" + "=" * 55)
    print("RADO-SCS ANATOMICAL MODEL")
    print("=" * 55)
    print(f"Components loaded: {len(components)}")
    print(f"DRG lead candidates included: {include_leads}")
    print(f"Visualization: {output_image}")
    print(f"Manifest: {output / 'focused_manifest.json'}")
    print("=" * 55)

    print(
        "\nNOTE: This is a geometry visualization only. "
        "The next step is verifying anatomical regions, "
        "surface interfaces, and electrical boundary conditions."
    )


# ============================================================
# COMMAND LINE
# ============================================================

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Visualize selected RADO-SCS anatomical STL components."
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Path to RADO-SCS ZIP or extracted STL directory.",
    )

    parser.add_argument(
        "--output",
        default="outputs/rado/focus",
        help="Directory for generated figures and manifest.",
    )

    parser.add_argument(
        "--include-leads",
        action="store_true",
        help="Include the four DRG lead candidates.",
    )

    args = parser.parse_args()

    build_visualization(
        source=args.input,
        output=args.output,
        include_leads=args.include_leads,
    )
