# Ultrack Nahual OCI image

Build the reproducible archive and load it into Podman or Docker:

```console
nix build .#oci-image
podman load < result                         # or: docker load < result
```

The image is tagged `nahual/ultrack:local` and listens on TCP port 5555.
Ultrack's segmentation hierarchy, linking, ILP solve, and label export run in a
writable temporary directory inside the container.

```console
podman run --rm -p 5555:5555 nahual/ultrack:local
```

CPU operation is the normal path because the ILP solver is CPU-bound. Optional
torch operations can see NVIDIA GPUs with Podman's `--device
nvidia.com/gpu=all` or Docker's `--gpus all`. With Nahual and NumPy installed
on the host, run the full synthetic tracking pipeline with:

```console
NAHUAL_DEVICE=cpu python oci/smoke_test.py
```

The input contract is `(T, 2, Z, Y, X)`: foreground probabilities in channel 0
and contours in channel 1. The output contains stable integer track IDs.
