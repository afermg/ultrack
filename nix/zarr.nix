{
  lib,
  buildPythonPackage,
  fetchurl,
  asciitree,
  numpy,
  fasteners,
  numcodecs,
}:
buildPythonPackage rec {
  pname = "zarr";
  version = "2.18.7";
  format = "wheel";

  src = fetchurl {
    url = "https://files.pythonhosted.org/packages/5e/d8/9ffd8c237b3559945bb52103cf0eed64ea098f7b7f573f8d2962ef27b4b2/zarr-${version}-py3-none-any.whl";
    sha256 = "sha256-rD3EAz6a5OnXteJ8l+o+rxADzAoH8BC9g9UTS/jEsiM=";
  };

  dependencies = [
    asciitree
    numpy
    fasteners
    numcodecs
  ];

  pythonImportsCheck = [ "zarr" ];

  pythonRuntimeDepsCheck = false;
  dontCheckRuntimeDeps = true;

  meta = {
    description = "Chunked, compressed N-dimensional arrays (v2 API for ultrack)";
    homepage = "https://github.com/zarr-developers/zarr-python";
    license = lib.licenses.mit;
  };
}
