{
  inputs = {
    naersk.url = "github:nix-community/naersk/master";
    #    naersk.url = "github:lucernae/nix-community-naersk/master";
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    utils.url = "github:numtide/flake-utils";
    rust-overlay.url = "github:oxalica/rust-overlay";
    devshell.url = "github:numtide/devshell";

    # flake subdir
    common.url = "github:lucernae/pinentry-box?dir=common";
  };

  outputs = { self, nixpkgs, utils, devshell, common, naersk, rust-overlay, ... }:
    utils.lib.eachDefaultSystem (system:
      let
        overlays = [ (import rust-overlay) devshell.overlays.default ];
        pkgs = import nixpkgs {
          inherit system;
          overlays = overlays;
        };
        rustVersion = pkgs.rust-bin.stable.latest.default.override {
          extensions = [ "rust-src" ];
        };
        naersk-lib = pkgs.callPackage naersk {
          cargo = rustVersion;
          rustc = rustVersion;
        };
      in
      {
        packages.default = naersk-lib.buildPackage {
          src = ./.;
          singleStep = true;
          nativeBuildInputs = with pkgs; [
            pkg-config
            libgpg-error.dev
          ];
          buildInputs = with pkgs; [
            rustVersion
          ] ++ (with pkgs;
            lib.optionals stdenv.isDarwin (with darwin.apple_sdk; [
              frameworks.CoreServices
              frameworks.CoreFoundation
              frameworks.SystemConfiguration
            ])
          );
        };

        formatter = common.formatter.${system};

        app.default = self.packages.${system}.default;

        devShells.native = with pkgs; mkShell {
          nativeBuildInputs = [
            pkg-config
            libgpg-error
          ];
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
          DEVSHELL_DIR = "${rustVersion}";
        };

        devShells.devshell = pkgs.devshell.mkShell {
          name = "pinentry-bitwarden-shell";
          commands = [
            #            {
            #              name = "pinentry-bitwarden";
            #              package = self.packages.${system}.default;
            #            }
          ] ++ (builtins.filter (v: v.name != "menu") common.devShells.${system}.default.config.commands);
          packages = with pkgs; [
            rustVersion
            pkg-config

            # we uses .dev output because numtide/devshell usually only exported .out only
            # for building library, we need .dev output.
            libgpg-error.dev
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
            {
              name = "PKG_CONFIG_PATH";
              # can just use $DEVSHELL_DIR/lib/pkgconfig but dunno how to refer it at build time.
              # we use the store paths instead
              value = "${pkgs.libgpg-error.dev}/lib/pkgconfig";
            }
          ];
        };
        devShells.default = self.devShells.${system}.devshell;
      });
}
