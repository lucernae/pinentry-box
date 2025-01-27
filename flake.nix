{
  description = "Application packaged using poetry2nix";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    devshell.url = "github:numtide/devshell";

    # flake in the subdirectory
    common = {
      #      url = "git+file:.?dir=common";
      #        path = "./common";
      #        url = "file:./common";
      url = "path:./common";
    };
    pinentry-box = {
      #      url = "git+file:.?dir=pinentry-box";
      #        path = "./pinentry-box";
      #        url = "file:./pinentry-box";
      url = "path:./pinentry-box";
    };
  };

  outputs = { self, devshell, nixpkgs, flake-utils, common, pinentry-box }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        # see https://github.com/nix-community/poetry2nix/tree/master#api for more functions and examples.
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ devshell.overlays.default ];
        };
      in
      {
        packages = pinentry-box.packages.${system};
        formatter = pkgs.nixpkgs-fmt;
        devShells.default = pkgs.devshell.mkShell {
          name = "pinentry-box";
          commands = [
          ] ++ (builtins.filter (v: v.name != "menu") common.devShells.${system}.default.config.commands);
        };
      });
}
