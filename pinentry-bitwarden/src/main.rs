use std::env;
use std::fs::File;
use std::io::{BufReader, BufWriter};
use std::path::PathBuf;

use directories::BaseDirs;
use futures::StreamExt;
use sequoia_ipc::gnupg::{Agent, Context};

use crate::config::Config;

pub mod config;

const CONFIG_FILENAME: &str = ".pinentry-bitwarden.yaml";

fn main() {
    let pinentry_config = get_config();
    // connect to GPG Agent
    let gnupghome = match env::var("GNUPGHOME") {
        Ok(homedir) => homedir,
        Err(_) => panic!("GPG Home Dir environment variable not found"),
    };
    let ctx = Context::with_homedir(gnupghome).unwrap();
    let rt = tokio::runtime::Runtime::new().unwrap();
    rt.block_on(async {
        let mut agent = Agent::connect(&ctx).await.unwrap();
        agent.send("HELP").unwrap();
        while let Some(response) = agent.next().await {
            eprintln!("< {:?}", response);
        }
    });
}

fn get_config() -> config::Config {
    let mut pinentry_config = Config::default();
    // config file priority:
    let home_config_file: PathBuf = BaseDirs::new()
        .map(|bd| bd.home_dir().join(CONFIG_FILENAME))
        .iter()
        .map(|pb| match pb.try_exists() {
            Ok(false) => {
                let file = File::create(pb.as_path()).unwrap();
                let writer = BufWriter::new(file);
                serde_yaml::to_writer(writer, &pinentry_config).unwrap();
                pb.clone()
            }
            _ => pb.clone(),
        })
        .next()
        .unwrap();
    let config_paths = [
        env::current_dir().unwrap().join(CONFIG_FILENAME),
        home_config_file,
    ];
    for pb in config_paths {
        if !pb.exists() {
            continue;
        }
        let file = File::open(pb.as_path()).unwrap();
        let reader = BufReader::new(file);
        pinentry_config = serde_yaml::from_reader(reader).ok().unwrap();
    }
    pinentry_config
}
