#!/usr/bin/env python3
"""End-to-end tracking against the Ultrack OCI container."""

import json
import os

os.environ.setdefault("NAHUAL_IPC_TIMEOUT_MS", "1800000")

import numpy as np
from nahual.process import dispatch_setup_process


def _synthetic(n_frames: int = 4, size: int = 96) -> np.ndarray:
    yy, xx = np.meshgrid(np.arange(size), np.arange(size), indexing="ij")
    data = np.zeros((n_frames, 2, 1, size, size), dtype=np.float32)
    for frame in range(n_frames):
        center = size // 2 + 2 * frame
        distance = np.sqrt((yy - center) ** 2 + (xx - center) ** 2)
        data[frame, 0, 0] = np.clip(1.0 - distance / 14.0, 0.0, 1.0)
        data[frame, 1, 0] = np.exp(-((distance - 14.0) ** 2) / 8.0)
    return data


def main() -> None:
    address = os.environ.get("NAHUAL_ADDRESS", "tcp://127.0.0.1:5555")
    device = os.environ.get("NAHUAL_DEVICE", "cpu")
    setup, process = dispatch_setup_process("ultrack")
    info = setup(
        {
            "device": device,
            "segmentation": {"min_area": 20, "max_area": 50000},
            "linking": {"max_distance": 25.0, "max_neighbors": 5},
            "tracking": {
                "appear_weight": -0.001,
                "disappear_weight": -0.001,
                "division_weight": -1.0,
                "n_threads": 1,
            },
        },
        address=address,
    )
    pixels = _synthetic()
    result = process(pixels, address=address)
    assert info["device"] == device, info
    assert result.shape == (4, 96, 96), result.shape
    assert np.issubdtype(result.dtype, np.integer), result.dtype
    assert result.max() > 0, "No tracks were produced"
    print(
        json.dumps(
            {
                "device": info["device"],
                "shape": list(result.shape),
                "track_ids": np.unique(result).tolist(),
            }
        )
    )


if __name__ == "__main__":
    main()
