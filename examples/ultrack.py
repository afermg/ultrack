"""
This example uses a server within the environment defined on
`https://github.com/afermg/ultrack.git`.

Run the server first:
    nix run github:afermg/ultrack -- ipc:///tmp/ultrack.ipc

Ultrack tracks segmented objects across time using an ILP-based linker
(CBC/CLP solver) on top of a candidate-segmentation hierarchy. The
underlying torch detection nets can run on GPU when invoked, but the
core tracking step itself is CPU-bound — that is by design, not a
limitation of the wrap.

Input contract: 5-D `(T, C, Z, Y, X)` numpy array of probability /
foreground maps over time. Output: `(T, Z, Y, X)` int32 instance label
volume with consistent IDs across frames.
"""

import numpy

from nahual.process import dispatch_setup_process

# Not in nahual's built-in registry — pass the signature explicitly.
setup, process = dispatch_setup_process("ultrack", signature=("dict", "numpy"))
address = "ipc:///tmp/ultrack.ipc"

# %% Load the tracker server-side.
parameters = {
    # Optional ultrack config dict; defaults are reasonable for the toy.
    "segmentation": {"min_area": 50, "max_area": 50_000},
    "linking": {"max_distance": 25.0, "max_neighbors": 5},
    "tracking": {
        "appear_weight": -0.001,
        "disappear_weight": -0.001,
        "division_weight": -1.0,
    },
}
response = setup(parameters, address=address)
print(response)

# %% Define custom data — toy 4-frame timelapse with one moving blob.
numpy.random.seed(seed=42)
T, Z, Y, X = 4, 1, 128, 128
data = numpy.zeros((T, 1, Z, Y, X), dtype=numpy.float32)
for t in range(T):
    cx = 30 + 5 * t
    cy = 30 + 5 * t
    data[t, 0, 0, cy - 8:cy + 8, cx - 8:cx + 8] = 0.9 + 0.1 * numpy.random.random((16, 16))

result = process(data, address=address)
print("shape:", result.shape, "dtype:", result.dtype)
print("unique track ids:", sorted(numpy.unique(result).tolist())[:10])
# Expected: shape (T, Z, Y, X) int32, with 1-2 distinct IDs.
