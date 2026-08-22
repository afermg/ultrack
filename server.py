"""Nahual server for Ultrack.

Ultrack (royerlab/ultrack) is a multi-hypothesis cell tracking framework. It
takes per-frame foreground probability maps + contour maps and solves an ILP
to produce a track-aware label volume.

Wire contract for this server:
    - Input is a 5-D numpy array shaped (T, C, Z, Y, X) where C == 2.
      Channel 0 = foreground probability, channel 1 = contour map. Z may be
      1 for 2-D timelapses (it is squeezed away before handing to ultrack).
    - Output is a numpy array of integer track IDs shaped (T, Z, Y, X) for
      3-D inputs or (T, Y, X) for 2-D inputs.

GPU situation: ultrack's segmentation / contour smoothing optionally runs on
GPU through cupy + cucim when present. The ILP solver (`mip` by default,
`gurobipy` if installed) is CPU-bound. The Nahual env reports `device`
truthfully — `cuda:0` if torch sees a GPU (used for the optional flow
estimator + cupy-backed image ops), else `cpu`.

Run with:
    nix run --impure . -- ipc:///tmp/ultrack.ipc
or:
    python server.py ipc:///tmp/ultrack.ipc
"""

import sys
import tempfile
from functools import partial
from typing import Any, Callable

import numpy
import pynng
import torch
import trio
from nahual.server import responder

# server.py captures argv[1] at import time; basic_test.py injects a
# placeholder before importing this module.
address = sys.argv[1]


def _make_config(device: int | None, ultrack_config: dict[str, Any]):
    """Build a MainConfig from a nested-dict overrides spec.

    Accepts the canonical ultrack TOML layout, e.g.
        {
          "data": {"working_dir": "/tmp/ultrack_run"},
          "segmentation": {"min_area": 100, "max_area": 100000},
          "linking": {"max_distance": 25.0, "max_neighbors": 5},
          "tracking": {"appear_weight": -0.1, "division_weight": -0.1,
                       "disappear_weight": -0.1, "n_threads": 1},
        }
    """
    from ultrack import MainConfig

    config = MainConfig()
    if not ultrack_config:
        return config

    alias_map = {
        "data": "data_config",
        "segmentation": "segmentation_config",
        "linking": "linking_config",
        "tracking": "tracking_config",
    }
    for key, sub in ultrack_config.items():
        attr = alias_map.get(key, key)
        target = getattr(config, attr, None)
        if target is None or not isinstance(sub, dict):
            continue
        for sub_key, value in sub.items():
            if hasattr(target, sub_key):
                setattr(target, sub_key, value)
    return config


def setup(
    device: int | None = None,
    working_dir: str | None = None,
    overwrite: bool = True,
    sigma: float | None = None,
    segment_kwargs: dict[str, Any] | None = None,
    link_kwargs: dict[str, Any] | None = None,
    solve_kwargs: dict[str, Any] | None = None,
    **ultrack_config: Any,
) -> tuple[Callable, dict]:
    """Configure the ultrack pipeline and return (processor_partial, info_dict).

    Parameters
    ----------
    device : int | None
        Preferred GPU index for torch / cupy ops. Falls back to CPU when CUDA
        is unavailable.
    working_dir : str | None
        Base directory for ultrack's SQLite database + intermediate zarrs.
        A fresh tempdir is created per request when None.
    overwrite : bool
        If True (default), the working_dir database is wiped per call.
    sigma : float | None
        Gaussian smoothing applied when converting label inputs to contours.
        Forwarded to `ultrack.track`.
    segment_kwargs, link_kwargs, solve_kwargs : dict | None
        Optional keyword overrides forwarded to `ultrack.track`.
    **ultrack_config :
        Section-keyed overrides for `MainConfig` (`data`, `segmentation`,
        `linking`, `tracking`). See `_make_config`.
    """
    if device is None:
        device = 0
    if torch.cuda.is_available():
        torch_device = torch.device(int(device))
        device_str = f"cuda:{int(device)}"
    else:
        torch_device = torch.device("cpu")
        device_str = "cpu"

    base_config = _make_config(device, ultrack_config)
    if working_dir is not None:
        base_config.data_config.working_dir = working_dir

    info = {
        "device": device_str,
        "torch_cuda_available": bool(torch.cuda.is_available()),
        "working_dir": working_dir,
        "overwrite": bool(overwrite),
        "sigma": sigma,
        "config": base_config.model_dump(by_alias=True, mode="json"),
    }

    processor = partial(
        process,
        config=base_config,
        torch_device=torch_device,
        sigma=sigma,
        overwrite=overwrite,
        segment_kwargs=segment_kwargs or {},
        link_kwargs=link_kwargs or {},
        solve_kwargs=solve_kwargs or {},
    )
    return processor, info


def process(
    pixels: numpy.ndarray,
    config,
    torch_device,
    sigma: float | None,
    overwrite: bool,
    segment_kwargs: dict[str, Any],
    link_kwargs: dict[str, Any],
    solve_kwargs: dict[str, Any],
) -> numpy.ndarray:
    """Run ultrack on a 5-D NCZYX foreground/contour stack.

    The input must be (T, 2, Z, Y, X). Channel 0 is the foreground
    probability map, channel 1 is the contour map. The Z dimension is
    squeezed when it has size 1 so that ultrack runs in 2-D mode.

    Returns an integer label volume of shape (T, Z, Y, X) (3-D) or (T, Y, X)
    (2-D), where each unique non-zero ID corresponds to a track.
    """
    from ultrack import track, tracks_to_zarr
    from ultrack.core.export.tracks_layer import to_tracks_layer

    if pixels.ndim != 5:
        raise ValueError(
            f"Expected 5-D NCZYX input, got shape {pixels.shape}"
        )
    n_t, n_c, n_z, n_y, n_x = pixels.shape
    if n_c != 2:
        raise ValueError(
            f"Expected channel dim of 2 (foreground, contours), got C={n_c}"
        )

    foreground = pixels[:, 0]
    contours = pixels[:, 1]
    if n_z == 1:
        foreground = foreground[:, 0]
        contours = contours[:, 0]

    # Each call gets a fresh working dir so the SQLite state from previous
    # calls doesn't contaminate this one. The dict-driven `working_dir` from
    # setup() takes precedence when supplied.
    using_tempdir = False
    if config.data_config.working_dir in (None, ".", ""):
        tmp = tempfile.mkdtemp(prefix="ultrack_run_")
        config.data_config.working_dir = tmp
        using_tempdir = True

    try:
        track(
            config,
            foreground=foreground.astype(numpy.float32),
            contours=contours.astype(numpy.float32),
            sigma=sigma,
            overwrite="all" if overwrite else "none",
            segment_kwargs=segment_kwargs,
            link_kwargs=link_kwargs,
            solve_kwargs=solve_kwargs,
        )
        tracks_df, _ = to_tracks_layer(config)
        segments = tracks_to_zarr(config, tracks_df=tracks_df)
        result = numpy.asarray(segments[:]).astype(numpy.int32)
    finally:
        if using_tempdir:
            import shutil
            shutil.rmtree(config.data_config.working_dir, ignore_errors=True)

    return result


async def main():
    with pynng.Rep0(listen=address, recv_timeout=300_000) as sock:
        print(f"ultrack server listening on {address}", flush=True)
        async with trio.open_nursery() as nursery:
            nursery.start_soon(partial(responder, setup=setup), sock)


if __name__ == "__main__":
    try:
        trio.run(main)
    except KeyboardInterrupt:
        pass
