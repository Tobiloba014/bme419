"""Load 21-node axon windows from the RADO archive."""
import io
from zipfile import ZipFile

import numpy as np


def read_fibers(archive, fiber_ids):
    with ZipFile(archive) as bundle:
        prefix = next(name for name in bundle.namelist()
                      if name.endswith("/AxonDiameters.npy")).rsplit("/", 1)[0]

        def array(name):
            return np.load(io.BytesIO(bundle.read(f"{prefix}/{name}.npy")))

        diameters = array("AxonDiameters").ravel()
        fibers = []
        for index in fiber_ids:
            coords = array(f"axon_{index}")
            # Center a 21-node window on the trajectory's middle node.
            middle = ((len(coords) - 1) // 22) * 11
            window = coords[middle - 110:middle + 111]
            if not np.isclose(diameters[index], 10) or window.shape != (221, 3):
                raise ValueError(f"Incompatible RADO axon {index}")
            fibers.append(window)
        return fibers
