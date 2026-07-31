{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/20075955deac2583bb12f07151c2df830ef346b4";
    systems.url = "github:nix-systems/default";
    flake-utils.url = "github:numtide/flake-utils";
    flake-utils.inputs.systems.follows = "systems";
    nahual-flake.url = "github:afermg/nahual";
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
    ...
  } @ inputs:
    flake-utils.lib.eachDefaultSystem (
      system: let
        pkgs = import nixpkgs {
          inherit system;
          config = {
            allowUnfree = true;
            cudaSupport = true;
          };
        };
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
        python_with_pkgs = python.withPackages (pp: [
          ourPackages.nahual
          ourPackages.ultrack
        ]);
        runServer = pkgs.writeScriptBin "nahual-ultrack" ''
          #!${pkgs.bash}/bin/bash
          export PYTHONSAFEPATH=1
          exec ${python_with_pkgs}/bin/python ${self}/server.py \
            "''${1:-tcp://0.0.0.0:5555}"
        '';
        ultrackApp = {
          type = "app";
          program = "${runServer}/bin/nahual-ultrack";
        };
      in
        with pkgs; rec {
          formatter = pkgs.alejandra;
          packages =
            ourPackages
            // {default = ourPackages.ultrack;}
            // pkgs.lib.optionalAttrs pkgs.stdenv.hostPlatform.isLinux {
              oci-image = import ./nix/oci-image.nix {
                inherit pkgs;
                name = "ultrack";
                title = "Nahual Ultrack";
                description = "Ultrack cell tracking served through Nahual";
                source = "https://github.com/afermg/ultrack";
                revision = self.rev or self.dirtyRev or "unknown";
                server = runServer;
                entrypoint = ultrackApp.program;
              };
            };
          inherit python_with_pkgs;
          scripts.runServer = runServer;
          apps = rec {
            ultrack = ultrackApp;
            default = ultrack;
          };
          devShells.default = mkShell {
            packages = [
              python_with_pkgs
              pkgs.cudaPackages.cudatoolkit
              python.pkgs.tifffile
              python.pkgs.scikit-image
              python.pkgs.scikit-learn
              python.pkgs.pyyaml
            ];
            shellHook = ''
              export PYTHONSAFEPATH=1
            '';
          };
        }
    );
}
