{
  lib,
  pkgs,
  python3Packages,
}:
let
  # Order matters: our package set (`packages`) wins over `python3Packages`
  # so that ultrack picks up our zarr-2.x and numcodecs-0.15.x overrides
  # rather than the nixpkgs zarr-3 / numcodecs-0.16 (which are API-
  # incompatible).
  callPackage = lib.callPackageWith (pkgs // python3Packages // packages);
  packages = {
    higra = callPackage ./higra.nix { };
    edt = callPackage ./edt.nix { };
    numcodecs = callPackage ./numcodecs.nix { };
    zarr = callPackage ./zarr.nix { };
    pynng = callPackage ./pynng.nix { };
    nahual = callPackage ./nahual.nix { };
    ultrack = callPackage ./ultrack.nix { };
  };
in
packages
