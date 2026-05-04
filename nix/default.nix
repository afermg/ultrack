{
  lib,
  pkgs,
  python3Packages,
  nahualSrc,
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
    # nahual recipe sourced from upstream flake input; built against our
    # local python3.13 so it uses the same zarr / numcodecs override scope.
    nahual = callPackage (nahualSrc + "/nix/nahual.nix") { };
    ultrack = callPackage ./ultrack.nix { };
  };
in
packages
