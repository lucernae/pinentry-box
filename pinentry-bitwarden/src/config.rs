use bitwarden::client::client_settings::ClientSettings;
use expanduser::expanduser;
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug, JsonSchema)]
pub struct SecretsAPIConfig {
    /// When using Secrets API Access Token, the token will directly identify the account
    /// Access Token key name means it will look up GPG Agent to retrieve the secrets
    pub access_token_key: String,
    /// access_token is the actual secret that is going to be used to authenticate to Secrets Manager
    pub access_token: String,
    /// project_name
    pub project_name: String,
}

#[derive(Serialize, Deserialize, Debug, JsonSchema)]
pub struct VaultAPIConfig {}

#[derive(Serialize, Deserialize, Debug, JsonSchema)]
#[serde(default, rename_all = "camelCase", deny_unknown_fields)]
pub struct Config {
    /// Bitwarden API Client Settings config
    pub client_settings: ClientSettings,
    /// key config for Bitwarden Secrets Manager
    pub secrets: SecretsAPIConfig,
    /// key config for Bitwarden Vault Manager
    pub vault: VaultAPIConfig,
    pub pinentry: PinentryConfig,
}

#[derive(Serialize, Deserialize, Debug, JsonSchema)]
#[serde(default, rename_all = "camelCase", deny_unknown_fields)]
pub struct PinentryConfig {
    /// key config for pinentry app absolute or relative path
    pub program_path: String,
    /// key config for pinentry extra args
    pub program_args: String,
    // key config for socket path to access this pinentry server
    pub socket_path: String,
}

impl Default for Config {
    fn default() -> Self {
        Config {
            client_settings: ClientSettings::default(),
            secrets: SecretsAPIConfig {
                access_token_key: "pinentry-bitwarden-access-token".to_string(),
                access_token: "".to_string(),
                project_name: "pinentry-bitwarden".to_string(),
            },
            vault: VaultAPIConfig {},
            pinentry: PinentryConfig::default(),
        }
    }
}

impl Default for PinentryConfig {
    fn default() -> Self {
        PinentryConfig {
            program_path: "pinentry-box".to_string(),
            program_args: "--start-server".to_string(),
            socket_path: expanduser("~/.pinentry-box.sock")
                .unwrap()
                .to_str()
                .unwrap()
                .to_string(),
        }
    }
}
