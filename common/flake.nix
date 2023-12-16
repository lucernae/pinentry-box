{
  description = "Pinentry Box repo flake library";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    devshell.url = "github:numtide/devshell";
  };

  outputs = { self, devshell, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        # see https://github.com/nix-community/poetry2nix/tree/master#api for more functions and examples.
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ devshell.overlays.default ];
        };
      in
      {
        formatter = pkgs.nixpkgs-fmt;
        devShells.default = pkgs.devshell.mkShell {
          name = "pinentry-box-lib";
          commands = [
            {
              name = "pre-commit";
              package = pkgs.pre-commit;
            }
            {
              name = "pcr";
              help = "pre-commit run --all-files";
              command = "pre-commit run --all-files";
            }
          ];
        };
      });
}
