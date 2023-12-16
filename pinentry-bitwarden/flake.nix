{
  inputs = {
    naersk.url = "github:nix-community/naersk/master";
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    utils.url = "github:numtide/flake-utils";
    rust-overlay.url = "github:oxalica/rust-overlay";
    devshell.url = "github:numtide/devshell";

    # flake subdir
    common.url = "git+file:..?dir=common";
  };

  outputs = { self, nixpkgs, utils, devshell, common, naersk, rust-overlay, ... }:
    utils.lib.eachDefaultSystem (system:
      let
        overlays = [ (import rust-overlay) devshell.overlays.default ];
        pkgs = import nixpkgs {
          inherit system;
          overlays = overlays;
        };
        rustVersion = pkgs.rust-bin.stable.latest.default.override { extensions = [ "rust-src" ]; };
        naersk-lib = pkgs.callPackage naersk { };
      in
      {
        packages.default = naersk-lib.buildPackage {
          src = ./.;
          buildInputs = [
          ] ++ (with pkgs;
            lib.optionals stdenv.isDarwin (with darwin.apple_sdk; [
              frameworks.CoreServices
              frameworks.CoreFoundation
              frameworks.SystemConfiguration
            ])
          );
        };
        formatter = common.formatter.${system};
        devShells.native = with pkgs; mkShell {
          buildInputs = [
            rustVersion
          ] ++ (
            lib.optionals stdenv.isDarwin (with darwin.apple_sdk; [
              frameworks.CoreServices
              frameworks.CoreFoundation
              frameworks.SystemConfiguration
            ])
          );
          RUST_SRC_PATH = rustPlatform.rustLibSrc;
          RUST_BACKTRACE = 1;
        };


        devShells.devshell = pkgs.devshell.mkShell {
          name = "pinentry-bitwarden-shell";
          commands = [
            {
              name = "pinentry-bitwarden";
              package = self.packages.${system}.default;
            }
          ] ++ (builtins.filter (v: v.name != "menu") common.devShells.${system}.default.config.commands);
          packages = [
            rustVersion
          ] ++ (with pkgs;
            lib.optionals stdenv.isDarwin (with darwin.apple_sdk; [
              frameworks.CoreServices
              frameworks.CoreFoundation
              frameworks.SystemConfiguration
            ])
          );
          env = [
            {
              name = "RUST_SRC_PATH";
              value = pkgs.rustPlatform.rustLibSrc;
            }
            {
              name = "RUST_BACKTRACE";
              value = 1;
            }
          ];
        };
        devShells.default = self.devShells.${system}.devshell;
      });
}
