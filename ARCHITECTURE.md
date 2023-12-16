# Architecture design

## Milestone v1

`pinentry-box`:
 - Use python to easily iterate and understand how Assuan protocol works
 - Swaps as `pinentry-program` in gpg-agent.conf, so that we know what gpg-agent send to the pinentry program
 - Dump/Log/Debug the protocol
 - Forward whatever gpg-agent send to the default pinentry program (`pinentry-mac` in MacOS)

`pinentry-bitwarden`:
 - For now, use config file and API key for the program to authenticate and decrypt the vault and username matching
 - Either implement using CLI or REST API
 - Use Rust, so we can easily make a CLI to test it (maybe Tauri App?)
 - Using API key, interact with existing bitwarden vault and retrieve the requested passphrase or PIN, depending on what the Assuan protocol sends

 `integration`:
 - Use Nix Darwin/NixOS module/flake to describe the integration. Well, basically swaps gpg-agent.conf `pinentry-program` config with `pinentry-box`, then generate config for `pinentry-box` to use `pinentry-bitwarden` and `pinentry-mac`.
 - Use Nix flake to integrate it with Git and VSCode config, so that signing commit can happen seamlessly.
