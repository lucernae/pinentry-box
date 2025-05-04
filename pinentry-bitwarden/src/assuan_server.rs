use anyhow::Result;
use fork;
use sequoia_gpg_agent::assuan;
use std::fmt::Error;
use std::future::Future;
use std::path::PathBuf;
use std::process::Stdio;
use tokio::process::Command;

use crate::config::{Config, PinentryConfig};

pub struct PinentryBox {
    pub config: PinentryConfig,
    // pub proc: Option<Future<Output=Result<Output>>>,
    // pub proc: Option<BoxedProcResult>,
    // pub proc: Option<Box<dyn futures::Future<Output = io::Result<Output>>>>,
}

pub struct PinentryBitwarden {
    pub config: Config,
    pinentry_box: PinentryBox,
}

pub enum SocketServerState<T> {
    Started(T),
    Ready,
}

// type BoxedProcResult = std::future::Future<Output = io::Result<Output>>;

impl PinentryBox {
    pub fn new(config: PinentryConfig) -> Self {
        PinentryBox { config }
        // check socket exists, if not then initiate connections
        // if PathBuf::from(&config.socket_path).exists() {
        //     Ok(PinentryBox { config, proc: None })
        // } else {
        //     let absolute_path = which::which(&config.program_path).unwrap();
        //     let program_args_slices = (&config.program_args).split_whitespace();
        //     let proc = Command::new(absolute_path.to_str().unwrap())
        //         .args(program_args_slices)
        //         .output();
        //     let proc = Some(Box::new(async { proc.await.unwrap() }));
        //     // let proc = Some(Bproc);
        //     Ok(PinentryBox { config, proc })
        // }
        // let proc = Some(PathBuf::from(&config.socket_path))
        //     // .map(|pb| Box::pin("a"));
        //     .map(|pb| match pb.exists() {
        //         true => None,
        //         false => {
        //             let absolute_path = which::which(&config.program_path).unwrap();
        //             let program_args_slices = (&config.program_args).split_whitespace();
        //             let proc = Command::new(absolute_path.to_str().unwrap())
        //                 .args(program_args_slices)
        //                 .output();
        //             Some(Box::pin(&proc))
        //         }
        //     })
        //     .unwrap();
        // let pinentry_box = PinentryBox { config, proc };
        // Ok(pinentry_box)
    }

    pub async fn start_socket_server(
        &self,
        // ) -> Result<SocketServerState<impl Future<Output = std::io::Result<Output>> + Sized>, Error>
    ) -> Result<SocketServerState<std::io::Result<tokio::process::Child>>, Error> {
        // check socket exists, if not then initiate connections
        if PathBuf::from(self.config.socket_path.as_str()).exists() {
            Ok(SocketServerState::Ready)
        } else {
            let absolute_path = which::which(self.config.program_path.as_str()).unwrap();
            let program_args_slices = (self.config.program_args.as_str()).split_whitespace();
            // Use the daemon function to properly detach the process
            if let Ok(fork::Fork::Child) = fork::daemon(false, false) {
                let _ = Command::new(absolute_path.to_str().unwrap())
                    .args(program_args_slices)
                    .stdin(Stdio::null())
                    .stdout(Stdio::null())
                    .stderr(Stdio::null())
                    .spawn();

                // Exit the child process after spawning the daemon
                std::process::exit(0);
            }

            // The parent process continues here
            // We can create a fake child result since the actual process is now running as a daemon
            // This allows the API to remain compatible with existing code
            let proc = Command::new("true").spawn();

            Ok(SocketServerState::Started(proc))
        }
    }

    pub fn connect(
        &self,
    ) -> impl Future<Output = Result<sequoia_gpg_agent::assuan::Client, sequoia_gpg_agent::Error>>
    {
        let client = assuan::Client::connect(self.config.socket_path.clone());
        client
    }
}

// /// A no GUI implementation of pinentry that directly requests secret from Bitwarden Vault or Secrets
// impl PinentryBitwarden {
//     pub fn new(config: Config) -> Self {
//         // Initialize bitwarden CLI client and secrets client from config
//         // initialize pinentry-box client
//         PinentryBitwarden {}
//     }
//
//     pub fn connect(&self) {
//         // connect to pinentry-box socket
//         // connect to bitwarden CLI and retrieve session key
//         // connect to bitwarden secrets
//     }
//
//     pub async fn start_server_daemon_mode(self) -> Result<()> {
//         let socket_path = PathBuf::from(&self.config.socket_path);
//         if socket_path.exists() {
//             std::fs::remove_file(&socket_path)?;
//         }
//         let server = Arc::new(self);
//         let mut assuan_server = Server::new(socket_path)?;
//         Ok(())
//     }
// }
