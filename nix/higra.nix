{
  lib,
  buildPythonPackage,
  fetchurl,
  python,
  numpy,
  autoPatchelfHook,
  stdenv,
}:
buildPythonPackage rec {
  pname = "higra";
  version = "0.6.13";
  format = "wheel";

  # Pinned to the cp313 manylinux x86_64 wheel.
  src = fetchurl {
    url = "https://files.pythonhosted.org/packages/42/39/4af36b2460a080b4301fd9ca6c7fa8b97c96030a14bf1c928a2c07cd603f/higra-${version}-cp313-cp313-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl";
    sha256 = "sha256-s4JXzT+SKqrO15VjVD32TnMiOZQhYSMYZ+qTmPLpFho=";
  };

  nativeBuildInputs = [ autoPatchelfHook ];
  buildInputs = [ stdenv.cc.cc.lib ];

  dependencies = [ numpy ];

  pythonImportsCheck = [ "higra" ];

  meta = {
    description = "Hierarchical Graph Analysis";
    homepage = "https://github.com/higra/Higra";
    license = lib.licenses.cecill-c;
  };
}
