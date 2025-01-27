{
  description = "Application packaged using poetry2nix";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    devshell.url = "github:numtide/devshell";

    # flake in subdirectory
    common.url = "path:../common";
  };

  outputs = { self, devshell, nixpkgs, flake-utils, common, poetry2nix }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        # see https://github.com/nix-community/poetry2nix/tree/master#api for more functions and examples.
        pkgs = nixpkgs.legacyPackages.${system};
        inherit (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; }) mkPoetryApplication mkPoetryEnv;
        inherit (pkgs) writeShellApplication;
      in
      {
        packages = {
          # this package is the base poetry package/environment that will be reused in this flake
          pinentry_box = mkPoetryEnv
            {
              projectDir = self;
              preferWheels = true;
              editablePackageSources = {
                pinentry_box = self;
              };
            } // {
            meta = {
              description = "Pinentry forwarder program";
              mainProgram = "pinentry-box";
            };
          };
          # pinentry-mac CLI
          pinentry_mac = writeShellApplication {
            name = "pinentry-mac";
            text = ''
              exec "${pkgs.pinentry_mac}/Applications/pinentry-mac.app/Contents/MacOS/pinentry-mac" "$@"
            '';
            meta = pkgs.pinentry_mac.meta;
          };
          pinentry_fallback = if pkgs.stdenv.isDarwin then self.packages.${system}.pinentry_mac else self.packages.${system}.pinentry;
          # the standalone CLI to be exposed
          pinentry_box_cli_with_env = writeShellApplication {
            name = "pinentry-box";
            text =
              let
                pinentry_fallback = self.packages.${system}.pinentry_fallback;
              in
              ''
                export PINENTRY_BOX__FALLBACK="${pinentry_fallback}/bin/${pinentry_fallback.meta.mainProgram}"
                stty sane
                exec "${self.packages.${system}.pinentry_box}/bin/pinentry-box" "$@"
              '';
          };
          pinentry_box_cli = writeShellApplication {
            name = "pinentry-box";
            text =
              let
                pinentry_fallback = self.packages.${system}.pinentry_fallback;
              in
              ''
                exec "${self.packages.${system}.pinentry_box}/bin/pinentry-box" "$@"
              '';
          };
          default = self.packages.${system}.pinentry_box;
        };

        formatter = nixpkgs.legacyPackages.${system}.nixpkgs-fmt;

        apps.default = {
          type = "app";
          program = "${self.packages.${system}.pinentry_box_cli}/bin/pinentry-box";
        };

        devShells.native = pkgs.mkShell {
          inputsFrom = [
            self.packages.${system}.pinentry_box
          ];
          packages = [
            pkgs.poetry
            pkgs.pre-commit
            # fallback pinentry-mac
            self.packages.${system}.pinentry_fallback
          ];
          shellHook =
            let
              pinentry_fallback = self.packages.${system}.pinentry_fallback;
            in
            ''
              export PINENTRY_BOX__FALLBACK="${pinentry_fallback}/bin/${pinentry_fallback.meta.mainProgram}"
              stty sane
            '';
        };

        devShells.devshell =
          let
            pkgs = import nixpkgs {
              inherit system;
              overlays = [ devshell.overlays.default ];
            };
          in
          pkgs.devshell.mkShell {
            name = "pinentry-box";
            commands = [
              {
                name = "pinentry-box";
                package = self.packages.${system}.pinentry_box;
              }
              {
                name = "pinentry-mac";
                package = self.packages.${system}.pinentry_mac;
              }
            ] ++ (builtins.filter (v: v.name != "menu") common.devShells.${system}.default.config.commands);
            env = [
              {
                name = "PINENTRY_BOX__FALLBACK";
                value =
                  let
                    pinentry_fallback = self.packages.${system}.pinentry_fallback;
                  in
                  "${pinentry_fallback}/bin/${pinentry_fallback.meta.mainProgram}";
              }
            ];
          };
        devShells.default = self.devShells.${system}.devshell;
      });
}
