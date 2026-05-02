{
  lib,
  buildPythonPackage,
  hatchling,
  numpy,
  pandas,
  scipy,
  scikit-image,
  numba,
  blosc2,
  zarr,
  numcodecs,
  toolz,
  fasteners,
  sqlalchemy,
  toml,
  pydantic,
  pydantic-settings,
  imagecodecs,
  imageio,
  pillow,
  cloudpickle,
  click,
  rich,
  tqdm,
  dask,
  networkx,
  psygnal,
  psycopg2,
  pyarrow,
  mip,
  higra,
  edt,
  torch,
  # Optional / lazy-imported by ultrack but still expected at runtime:
  matplotlib,
  seaborn,
  tifffile,
  # Testing
  pytest,
}:
buildPythonPackage {
  pname = "ultrack";
  version = "0.7.0.dev1";
  format = "pyproject";

  src = ./..;

  # ultrack pyproject pins `requires-python = ">=3.9,<3.13"`, but the code
  # is actually 3.13-compatible. Rewrite the pin so hatchling lets us
  # build under python3.13.
  postPatch = ''
    substituteInPlace pyproject.toml \
      --replace-fail 'requires-python = ">=3.9,<3.13"' 'requires-python = ">=3.9"'
  '';

  build-system = [ hatchling ];

  dependencies = [
    numpy
    pandas
    scipy
    scikit-image
    numba
    blosc2
    zarr
    numcodecs
    toolz
    fasteners
    sqlalchemy
    toml
    pydantic
    pydantic-settings
    imagecodecs
    imageio
    pillow
    cloudpickle
    click
    rich
    tqdm
    dask
    networkx
    psygnal
    psycopg2
    pyarrow
    mip
    higra
    edt
    torch
    matplotlib
    seaborn
    tifffile
  ];

  pythonImportsCheck = [
    "ultrack"
    "ultrack.core.main"
    "ultrack.core.tracker"
  ];

  # Skip the network-heavy & qt-heavy upstream test suite.
  doCheck = false;
  pythonRuntimeDepsCheck = false;
  dontCheckRuntimeDeps = true;

  meta = {
    description = "Large-scale multi-hypotheses cell tracking";
    homepage = "https://github.com/royerlab/ultrack";
    license = lib.licenses.bsd3;
  };
}
