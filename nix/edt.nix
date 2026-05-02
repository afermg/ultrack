{
  lib,
  buildPythonPackage,
  fetchurl,
  numpy,
  autoPatchelfHook,
  stdenv,
}:
buildPythonPackage rec {
  pname = "edt";
  version = "3.1.1";
  format = "wheel";

  # Pinned to the cp313 manylinux x86_64 wheel.
  src = fetchurl {
    url = "https://files.pythonhosted.org/packages/c0/16/35778deac2353ed385e81bda4dfd2eefcc1c0c1e1c083f4cb39ef0025d18/edt-${version}-cp313-cp313-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl";
    sha256 = "sha256-tGS9i7bhTt/Af4wTgnAERrwgorUh7ElPPeH9XSBHHPM=";
  };

  nativeBuildInputs = [ autoPatchelfHook ];
  buildInputs = [ stdenv.cc.cc.lib ];

  dependencies = [ numpy ];

  pythonImportsCheck = [ "edt" ];

  meta = {
    description = "Multi-label Euclidean distance transforms";
    homepage = "https://github.com/seung-lab/euclidean-distance-transform-3d";
    license = lib.licenses.gpl3Plus;
  };
}
