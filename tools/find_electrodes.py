
import csv
import json
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MANIFEST = PROJECT_ROOT / "outputs" / "rado" / "geometry_manifest.csv"

with open(MANIFEST, encoding="utf-8") as f:
    meshes = list(csv.DictReader(f))

def vector(row, key):
    return np.array(json.loads(row[key]), dtype=float)

epidural = next(
    r for r in meshes
    if "neuro_epiduralspace-1.stl" in r["file"].lower()
)

epi_min = vector(epidural, "bounds_min_raw")
epi_max = vector(epidural, "bounds_max_raw")

# Preliminary screening only; STL coordinates still need unit verification.
MARGIN = 5.0
MAX_EXTENT = 25.0

candidates = []

for row in meshes:
    if row["status"] != "ok":
        continue

    name = row["file"].split("/")[-1]
    lower = name.lower()

    if "neuro_epiduralspace-1.stl" in lower:
        continue

    bounds_min = vector(row, "bounds_min_raw")
    bounds_max = vector(row, "bounds_max_raw")
    dimensions = vector(row, "extents_raw")

    # Minimum AABB-to-AABB separation along each axis.
    separation = np.maximum(
        np.maximum(epi_min - bounds_max, bounds_min - epi_max),
        0.0,
    )

    distance = np.linalg.norm(separation)

    if distance <= MARGIN and max(dimensions) <= MAX_EXTENT:
        candidates.append((distance, name, dimensions))

candidates.sort(key=lambda item: item[0])

print(f"\nFound {len(candidates)} spatial candidates:\n")

for distance, name, size in candidates:
    print(name)
    print(f"  Bounding-box distance: {distance:.3f}")
    print(f"  Dimensions: {np.round(size, 3)}")
