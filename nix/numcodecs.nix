{
  lib,
  buildPythonPackage,
  fetchurl,
  numpy,
  deprecated,
  autoPatchelfHook,
  stdenv,
  zlib,
}:
buildPythonPackage rec {
  pname = "numcodecs";
  version = "0.15.1";
  format = "wheel";

  # zarr 2.18 still expects the v1.x numcodecs API; v0.16 is incompatible.
  # Pinned to the cp313 manylinux x86_64 wheel.
  src = fetchurl {
    url = "https://files.pythonhosted.org/packages/fa/91/d96999b41e3146b6c0ce6bddc5ad85803cb4d743c95394562c2a4bb8cded/numcodecs-${version}-cp313-cp313-manylinux_2_17_x86_64.manylinux2014_x86_64.whl";
    sha256 = "sha256-Hf3qSmcQggXt/OmcHLbNYhNDvHq7fhagQclmd2kg594=";
  };

  nativeBuildInputs = [ autoPatchelfHook ];
  buildInputs = [ stdenv.cc.cc.lib zlib ];

  dependencies = [ numpy deprecated ];

  pythonRuntimeDepsCheck = false;
  dontCheckRuntimeDeps = true;

  pythonImportsCheck = [ "numcodecs" ];

  meta = {
    description = "Buffer compression and transformation codecs";
    homepage = "https://github.com/zarr-developers/numcodecs";
    license = lib.licenses.mit;
  };
}
