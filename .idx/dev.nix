{ pkgs, ... }: {
  channel = "stable-24.05";

  packages = [
    pkgs.python311
    pkgs.python311Packages.pip
  ];

  idx = {
    workspace = {
      onCreate = {
        default.openFiles = [ "README.md" "SETUP.md" ];
      };
    };
    previews = {
      enable = true;
      previews = {
        web = {
          command = [ "python" "-m" "http.server" "3000" "--directory" "dashboard" ];
          manager = "web";
        };
      };
    };
  };
}
