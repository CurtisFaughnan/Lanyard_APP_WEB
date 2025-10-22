{ pkgs }: {
  deps = [
    pkgs.python313
    pkgs.python313Packages.pip
    pkgs.python313Packages.setuptools
    pkgs.python313Packages.wheel
  ];
  env = {
    PYTHONPATH = ".";
  };
  shellHook = ''
    pip install -r requirements.txt > /dev/null
  '';
}
