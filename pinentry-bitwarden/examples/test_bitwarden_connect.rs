use bitwarden::secrets_manager::secrets::{SecretGetRequest, SecretIdentifiersByProjectRequest};
use bitwarden::{
    auth::login::AccessTokenLoginRequest,
    client::client_settings::{ClientSettings, DeviceType},
    error::Result,
    Client,
};
use dotenv;
use std::env;
use uuid::Uuid;

#[tokio::test]
async fn test_bitwarden_connect() -> Result<()> {
    // load environment from dotenv from .local.env
    dotenv::from_filename(".local.env").ok();
    // Or set your own values
    let settings = ClientSettings {
        identity_url: "https://identity.bitwarden.com".to_string(),
        api_url: "https://api.bitwarden.com".to_string(),
        user_agent: "Bitwarden Rust-SDK".to_string(),
        device_type: DeviceType::SDK,
    };
    let mut client = Client::new(Some(settings));

    // Before we operate, we need to authenticate with a token
    let access_token = dotenv::var("PINENTRY_BITWARDEN__SECRETS__ACCESS_TOKEN").unwrap_or_default();
    let token = AccessTokenLoginRequest {
        access_token: String::from(access_token),
    };
    client.auth().login_access_token(&token).await.unwrap();
    let test_secret_id = env::var("TEST_SECRET_ID").unwrap_or_default();
    let secret_request = SecretGetRequest {
        id: Uuid::parse_str(test_secret_id.as_str()).unwrap(),
    };
    println!(
        "Stored secrets: {:#?}",
        client.secrets().get(&secret_request).await.unwrap().value
    );
    let project_id = env::var("TEST_PROJECT_ID").unwrap_or_default();
    for k in client
        .secrets()
        .list_by_project(&SecretIdentifiersByProjectRequest {
            project_id: Uuid::parse_str(project_id.as_str()).unwrap(),
        })
        .await
        .unwrap()
        .data
    {
        println!("Stored secrets: id:{:#?} key:{:#?}", k.id, k.key);
        let secret_value = client
            .secrets()
            .get(&SecretGetRequest { id: k.id })
            .await
            .unwrap();
        println!("Stored secrets: {:#?}", secret_value.value);
    }
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
