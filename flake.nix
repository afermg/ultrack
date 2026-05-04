{
  inputs = {
    # Pin to the same nixpkgs commit cellpose / trackastra use — its
    # python312-torch-2.x-cuda derivation is in the nixos-unstable cache.
    # Bumping to head means rebuilding torch (~hours) for our flake.
    nixpkgs.url = "github:NixOS/nixpkgs/20075955deac2583bb12f07151c2df830ef346b4";
    systems.url = "github:nix-systems/default";
    flake-utils.url = "github:numtide/flake-utils";
    flake-utils.inputs.systems.follows = "systems";
    nahual-flake.url = "github:afermg/nahual";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      systems,
      ...
    }@inputs:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs {
          system = system;
          config = {
            allowUnfree = true;
            # GPU is required for the optional cupy / torch ops; the ILP
            # solver itself is CPU-bound.
            cudaSupport = true;
          };
        };
        # ultrack pyproject pins python <3.13, but its actual code is
        # 3.13-compatible. We override the requires-python check below in
        # ./nix/ultrack.nix and use python313 because nixpkgs' python313-
        # torch derivation already has a cached triton on this nixpkgs pin
        # (python312 would force a fresh triton compile).
        # We further override numba so its 10+-min pytest suite is skipped
        # when our custom dep set forces it to be rebuilt. Without this,
        # `nix develop` can take >30 min on a contended host because
        # numba's pytestCheckPhase compiles llvm tests serially.
        python = pkgs.python313.override {
          packageOverrides = pyfinal: pyprev: {
            numba = pyprev.numba.overridePythonAttrs (_: {
              doCheck = false;
              doInstallCheck = false;
              pytestCheckPhase = "true";
              installCheckPhase = "true";
            });
          };
        };

        ourPackages = pkgs.callPackage ./nix {
          python3Packages = python.pkgs;
          nahualSrc = inputs.nahual-flake;
        };
      in
      with pkgs;
      rec {
        formatter = pkgs.alejandra;

        packages = ourPackages // {
          default = ourPackages.ultrack;
        };

        apps.default =
          let
            python_with_pkgs = python.withPackages (pp: [
              ourPackages.nahual
              ourPackages.ultrack
            ]);
            runServer = pkgs.writeScriptBin "runserver.sh" ''
              #!${pkgs.bash}/bin/bash
              ${python_with_pkgs}/bin/python ${self}/server.py ''${@:-"ipc:///tmp/ultrack.ipc"}
            '';
          in
          {
            type = "app";
            program = "${runServer}/bin/runserver.sh";
          };

        devShells = {
          default =
            let
              python_with_pkgs = python.withPackages (pp: [
                ourPackages.nahual
                ourPackages.ultrack
                pp.tifffile
                pp.scikit-image
                pp.scikit-learn
                pp.pyyaml
              ]);
            in
            mkShell {
              packages = [
                python_with_pkgs
                pkgs.cudaPackages.cudatoolkit
              ];
              shellHook = ''
                export PYTHONPATH=${python_with_pkgs}/${python_with_pkgs.sitePackages}:$PYTHONPATH
              '';
            };
        };
      }
    );
}
