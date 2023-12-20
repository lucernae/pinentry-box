/// Connects to and sends commands to gpg-agent.

use std::path::PathBuf;

use clap::CommandFactory;
use clap::FromArgMatches;
use clap::Parser;

use futures::StreamExt;

use sequoia_ipc as ipc;
use crate::ipc::gnupg::{Context, Agent};

use sequoia_openpgp as openpgp;
use openpgp::Result;

/// Defines the CLI.
#[derive(Parser, Debug)]
#[clap(
name = "gpg-agent-client",
about = "Connects to and sends commands to gpg-agent.",
)]
pub struct Cli {
    #[clap(
    long,
    value_name = "PATH",
    env = "GNUPGHOME",
    help = "Use this GnuPG home directory, default: $GNUPGHOME",
    )]
    homedir: Option<PathBuf>,

    #[clap(
    long,
    value_name = "commands",
    help = "Commands to send to the server",
    required = true,
    )]
    commands: Vec<String>,
}

fn main() -> Result<()> {
    let version = format!(
        "{} (sequoia-openpgp {}, using {})",
        env!("CARGO_PKG_VERSION"),
        sequoia_openpgp::VERSION,
        sequoia_openpgp::crypto::backend());
    let cli = Cli::command().version(version);
    let matches = Cli::from_arg_matches(&cli.get_matches())?;

    let ctx = if let Some(homedir) = matches.homedir {
        Context::with_homedir(homedir)?
    } else {
        Context::new()?
    };

    let rt = tokio::runtime::Runtime::new().unwrap();
    rt.block_on(async {
        let mut agent = Agent::connect(&ctx).await.unwrap();

        for command in matches.commands {
            eprintln!("> {}", command);
            agent.send(command).unwrap();
            while let Some(response) = agent.next().await {
                eprintln!("< {:?}", response);
            }
        }
    });

    Ok(())
}
