"""Standalone smoke test for the ultrack Nahual wrap.

Loads ultrack the same way `server.py` does and runs the full track→export
pipeline on a tiny synthetic 2-D timelapse. Does NOT spin up the IPC server
— the goal here is to verify the dev shell + ultrack assembly without the
network plumbing.

Run from the repo root:
    nix develop --impure --command python basic_test.py
"""

import importlib.util
import os
import sys

# Drop the repo root from sys.path BEFORE importing ultrack — otherwise the
# in-tree `ultrack/` source dir shadows the nix-built package.
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p) not in {_HERE, ""}]

# server.py reads sys.argv[1] at import time; inject a placeholder so
# importing it from this file doesn't crash.
if len(sys.argv) < 2:
    sys.argv.append("ipc:///tmp/ultrack_basic_test.ipc")

import numpy  # noqa: E402

# Load `server.py` directly via importlib so we never need to put _HERE back
# on sys.path (which would re-trigger the ultrack source-dir shadow).
_spec = importlib.util.spec_from_file_location("server", os.path.join(_HERE, "server.py"))
server = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(server)
setup = server.setup


def _make_synthetic(n_t: int = 4, size: int = 128) -> numpy.ndarray:
    """Build a (T, 2, 1, Y, X) NCZYX stack with a single drifting blob.

    Channel 0: foreground probability. Channel 1: contour map.
    """
    rng = numpy.random.default_rng(0)
    yy, xx = numpy.meshgrid(numpy.arange(size), numpy.arange(size), indexing="ij")
    out = numpy.zeros((n_t, 2, 1, size, size), dtype=numpy.float32)
    for t in range(n_t):
        cy = size // 2 + 2 * t
        cx = size // 2 + 2 * t
        radius = 18.0
        dist = numpy.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
        # Foreground prob: high inside, low outside, with mild noise.
        fg = numpy.clip(1.0 - dist / radius, 0.0, 1.0)
        fg = fg + 0.02 * rng.standard_normal(fg.shape).astype(numpy.float32)
        fg = numpy.clip(fg, 0.0, 1.0)
        # Contour: ring around the boundary.
        ring = numpy.exp(-((dist - radius) ** 2) / (2.0 * 2.0**2))
        out[t, 0, 0] = fg
        out[t, 1, 0] = ring.astype(numpy.float32)
    return out


def main() -> None:
    size_max = 50_000
    cfg_overrides = {
        "segmentation": {"min_area": 50, "max_area": size_max},
        "linking": {"max_distance": 25.0, "max_neighbors": 5},
        "tracking": {
            "appear_weight": -0.001,
            "disappear_weight": -0.001,
            "division_weight": -1.0,  # discourage division on this toy
            "n_threads": 1,
        },
    }
    processor, info = setup(**cfg_overrides)
    print(f"setup: device={info['device']!r} cuda={info['torch_cuda_available']}")

    data = _make_synthetic()
    print(f"input shape: {data.shape} dtype={data.dtype}")
    out = processor(data)
    arr = out.cpu().numpy() if hasattr(out, "cpu") else out
    print(f"process: type={type(arr).__name__} shape={arr.shape} dtype={arr.dtype}")
    print(f"unique track ids: {sorted(numpy.unique(arr).tolist())[:10]} ...")


if __name__ == "__main__":
    main()
