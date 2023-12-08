{
  description = "Application packaged using poetry2nix";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, poetry2nix }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        # see https://github.com/nix-community/poetry2nix/tree/master#api for more functions and examples.
        pkgs = nixpkgs.legacyPackages.${system};
        inherit (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; }) mkPoetryApplication mkPoetryEnv;
        inherit (pkgs) writeShellApplication;
      in
      {
        packages = {
          pinentry_box = mkPoetryEnv {
            projectDir = self;
            preferWheels = true;
            editablePackageSources = {
                pinentry_box = self;
            };
          };
          pinentry_box_cli = writeShellApplication {
            name = "pinentry_box";
            text = ''
            export PINENTRY_BOX_FALLBACK="${pkgs.pinentry_mac}/Applications/pinentry-mac.app/Contents/MacOS/pinentry-mac"
            stty sane
            ${self.packages.${system}.pinentry_box}/bin/pinentry_box
            '';
          };
          default = self.packages.${system}.pinentry_box;
        };

        formatter = nixpkgs.legacyPackages.${system}.nixpkgs-fmt;

        apps.default = {
          type = "app";
          program = "${self.packages.${system}.pinentry_box_cli}/bin/pinentry_box";
        };

        devShells.default = pkgs.mkShell {
          inputsFrom = [
            self.packages.${system}.pinentry_box
           ];
          packages = [
            pkgs.poetry
            # fallback pinentry to be used
            pkgs.pinentry_mac
           ];
          shellHook = ''
          export PINENTRY_BOX_FALLBACK="${pkgs.pinentry_mac}/Applications/pinentry-mac.app/Contents/MacOS/pinentry-mac"
          stty sane
          '';
        };
      });
}
