# Pinentry Box

Pinentry Box is a program to interface with GPG Agent. It is like a proxy that talks with GPG Agent and then forward via the Assuan protocol to the targeted pinentry program. Traditionally pinentry program is used to ask the PIN or passphrase. With Pinentry Box, we have some control in the middle layer to integrate with pinentry program that doesn't rely on GUI or TUI.

Well, basically I want to plug in pinentry integration with bitwarden as the secret vault. Pinentry Box can handle the configuration while pinentry-bitwarden will directly handle retrieving passphrase from bitwarden.

```mermaid
flowchart LR
    GPG-Agent --> pinentry-box
    pinentry-box --> pinentry-mac
    pinentry-box --> pinentry-bitwarden
    pinentry-mac --> MacOS Keychain
    pinentry-bitwarden --> Bitwarden Vault API/CLI
```

Notice that pinentry-box will filter which secret key can be retrieved from which vault.
So we can have a loop-back. 
For example, if your GPG passphrase is stored in Bitwarden, pinentry-box can try to retrieve it from bitwarden, but Bitwarden needs to be unlocked and can ask back to pinentry-box, in which it will ask MacOS Keychain.

This allows for more flexibility when integrating with different OS or environment as well.