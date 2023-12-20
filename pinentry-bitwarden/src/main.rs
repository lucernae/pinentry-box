use bitwarden::secrets_manager::secrets::SecretGetRequest;
use bitwarden::{
    auth::login::AccessTokenLoginRequest,
    client::client_settings::{ClientSettings, DeviceType},
    error::Result,
    Client,
};
use std::env;
use uuid::Uuid;

#[tokio::test]
async fn test() -> Result<()> {
    // Or set your own values
    let settings = ClientSettings {
        identity_url: "https://identity.bitwarden.com".to_string(),
        api_url: "https://api.bitwarden.com".to_string(),
        user_agent: "Bitwarden Rust-SDK".to_string(),
        device_type: DeviceType::SDK,
    };
    let mut client = Client::new(Some(settings));

    // Before we operate, we need to authenticate with a token
    let access_token = env::var("PINENTRY_BITWARDEN__SECRETS__ACCESS_TOKEN").unwrap_or_default();
    let token = AccessTokenLoginRequest {
        access_token: String::from(access_token),
    };
    client.auth().login_access_token(&token).await.unwrap();
    let secret_request = SecretGetRequest {
        id: Uuid::parse_str(env::var("TEST_SECRET_ID").unwrap_or_default().as_str()).unwrap(),
    };
    println!(
        "Stored secrets: {:#?}",
        client.secrets().get(&secret_request).await.unwrap().value
    );
    Ok(())

    // let org_id = SecretIdentifiersRequest { organization_id: Uuid::parse_str("00000000-0000-0000-0000-000000000000").unwrap() };
    // println!("Stored secrets: {:#?}", client.secrets().list(&org_id).await.unwrap());
    // Ok(())
}

fn main() {
    println!("Hello World");
}
