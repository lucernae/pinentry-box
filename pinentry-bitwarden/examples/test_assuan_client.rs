use std::fs::remove_file;
use std::future::Future;
use std::io::BufReader;
use std::os::macos::raw::stat;
use std::path::{Path, PathBuf};

use clap::CommandFactory;
use clap::FromArgMatches;
use clap::Parser;

use crate::ipc::assuan::Client;
use futures::{StreamExt, TryFuture};
use sequoia_ipc as ipc;

use openpgp::Result;
use pinentry_bitwarden::assuan_server::{PinentryBox, SocketServerState};
use pinentry_bitwarden::config::PinentryConfig;
use sequoia_ipc::assuan::Response;
use sequoia_openpgp as openpgp;
use tokio::io::AsyncReadExt;
use tokio::net::UnixStream;

/// Defines the CLI.
#[derive(Parser, Debug)]
#[clap(
    name = "assuan-client",
    about = "Connects to and sends commands to assuan servers."
)]
pub struct Cli {
    #[clap(long, value_name = "PATH", help = "Server to connect to")]
    server: PathBuf,

    #[clap(
        long,
        value_name = "COMMAND",
        help = "Commands to send to the server",
        required = true
    )]
    commands: Vec<String>,
}

fn main() -> Result<()> {
    let version = format!(
        "{} (sequoia-openpgp {}, using {})",
        env!("CARGO_PKG_VERSION"),
        sequoia_openpgp::VERSION,
        sequoia_openpgp::crypto::backend()
    );
    let cli = Cli::command().version(version);
    let matches = Cli::from_arg_matches(&cli.get_matches())?;

    let rt = tokio::runtime::Runtime::new().unwrap();
    rt.block_on(async {
        let mut pinentry_box_config = PinentryConfig::default();
        let pinentry_box = PinentryBox::new(pinentry_box_config);
        while let state = pinentry_box.start_socket_server().await.unwrap() {
            match state {
                // SocketServerState::Started(_) => {
                //     break;
                // }
                SocketServerState::Started(proc) => {
                    // let mut client = pinentry_box.connect().await.unwrap();
                    // client.send("HELP").unwrap();
                    // let mut proc = proc.await.unwrap();
                    // let mut proc = proc.unwrap().wait_with_output().await.unwrap();
                    let mut proc = proc.unwrap();
                    let mut output_str = String::new();
                    proc.stdout
                        .take()
                        .unwrap()
                        .read_to_string(&mut output_str)
                        .await
                        .unwrap();
                    // let mut err_str = String::new();
                    // proc.stderr
                    //     .take()
                    //     .unwrap()
                    //     .read_to_string(&mut err_str)
                    //     .await
                    //     .unwrap();
                    // let exit_status = proc.status;
                    // let output_str =
                    // std::str::from_utf8(proc.stdout.take().unwrap().).unwrap();
                    // proc.stdout.take().unwrap().read_to_string()
                    // let err_str =
                    //     std::str::from_utf8(proc.stderr.take().unwrap().as_mut_slice()).unwrap();
                    println!("S: {:?}", output_str);
                    // println!("S-Err: {:?}", err_str);
                    // let exit_status = proc.status;
                    // let output_str = std::str::from_utf8(proc.stdout.as_mut_slice()).unwrap();
                    // let err_str = std::str::from_utf8(proc.stderr.as_mut_slice()).unwrap();
                    // println!("S: {:?}", output_str);
                    // println!("S-Err: {:?}", err_str);
                    break;
                }
                SocketServerState::Ready => {
                    // test socket connect. if it fails, remove the socket.
                    match pinentry_box.connect().await {
                        Ok(mut client) => {
                            client.send("BYE").unwrap();
                            break;
                        }
                        Err(err) => {
                            eprintln!("S-Err: {:?}", err);
                            remove_file(PathBuf::from(pinentry_box.config.socket_path.clone()))
                                .unwrap()
                        }
                    }
                }
            }
        }
        let mut client = pinentry_box.connect().await.unwrap();
        for command in matches.commands {
            eprintln!("> {}", command);
            client.send(command).unwrap();
            while let Some(response) = client.next().await {
                eprintln!("< {:?}", response);
            }
        }
        client.send("GETINFO pid").unwrap();
        while let Some(response) = client.next().await {
            match response {
                Ok(Response::Data { ref partial }) => {
                    println!("S: {:?}", std::str::from_utf8(partial.as_slice()))
                }
                Err(_) => {}
                _ => {}
            }
            println!("S: {:?}", response)
        }
        client.send("BYE").unwrap();
        while let Some(response) = client.next().await {
            println!("S: {:?}", response)
        }
    });

    Ok(())
}
