use std::fmt::Error;
use std::future::Future;
use std::path::PathBuf;
use std::process::{Output, Stdio};

use sequoia_ipc::assuan;
use sequoia_ipc::assuan::Client;
use tokio::process::Command;

use crate::config::PinentryConfig;

pub struct PinentryBox {
    pub config: PinentryConfig,
    // pub proc: Option<Future<Output=Result<Output>>>,
    // pub proc: Option<BoxedProcResult>,
    // pub proc: Option<Box<dyn futures::Future<Output = io::Result<Output>>>>,
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
            let proc = Command::new(absolute_path.to_str().unwrap())
                .args(program_args_slices)
                .stdout(Stdio::piped())
                .stderr(Stdio::piped())
                .spawn();
            Ok(SocketServerState::Started(proc))
        }
    }

    pub fn connect(&self) -> impl Future<Output = sequoia_ipc::Result<Client>> + Sized {
        let client = assuan::Client::connect(self.config.socket_path.clone());
        client
    }
}

// /// AssuanServerCLI used as interface to communicate with pinentry CLI program,
// /// but using socket
// pub struct AssuanServerCLI {
//     pub server_path: PathBuf,
//     server_socket: PathBuf,
//     pub client: Pin<Box<dyn Future<Output = (sequoia_ipc::Result<assuan::Client>)>>>,
//     // proc: Child,
// }
//
// impl<'a> AssuanServerCLI {

// pub

// pub async fn new(server_path: PathBuf) -> Result<AssuanServerCLI, Error> {
//     let server_socket = match  {  }; NamedTempFile::new().unwrap().path().to_owned();
//     // let server_socket = PathBuf::from(
//     //     "/Users/recalune/WorkingDir/github/lucernae/pinentry-box/pinentry-box/.local.sock",
//     // );
//     // let socket_listener = UnixListener::bind(&server_socket).ok();
//     // let stream = UnixStream::connect(&server_socket).unwrap();
//     // approach 1
//     // let fd_in = stream.as_raw_fd();
//     // let fd_out = stream.as_raw_fd();
//     // let mut proc = Command::new(server_path)
//     //     .stdin(unsafe { Stdio::from_raw_fd(fd_in) })
//     //     .stdout(unsafe { Stdio::from_raw_fd(fd_out) })
//     //     .spawn()
//     //     .expect("unable to execute CLI");
//     // approach 2
//     // let socket_path_str = server_socket.to_str().unwrap();
//     // let server_path_str = server_path.to_str().unwrap();
//     // let arg = format!("cat < {socket_path_str} | {server_path_str} > {socket_path_str}");
//     // let mut proc = Command::new("bash")
//     //     .arg("-c")
//     //     .arg(arg)
//     //     .spawn()
//     //     .expect("unable to execute CLI");
//     let socket_path_str = server_socket.to_str().unwrap();
//     let server_path_str = server_path.to_str().unwrap();
//     let command_shell = format!("{server_path_str} --socket-path {socket_path_str} &");
//     let mut proc = Command::new(server_path_str)
//         .arg("--start-server")
//         // .arg("--help")
//         // .arg(command_shell)
//         // .arg("--socket-path")
//         // .arg(socket_path_str)
//         // .stdin(Stdio::null())
//         // .stdout(Stdio::null())
//         // .stderr(Stdio::null())
//         // .spawn()
//         .output();
//     // .expect("unable to execute CLI");
//     // let exit_status = proc.status;
//     // let output_str = std::str::from_utf8(proc.stdout.as_mut_slice()).unwrap();
//     // let err_str = std::str::from_utf8(proc.stderr.as_mut_slice()).unwrap();
//
//     if let mut response = proc.await.unwrap() {
//         eprintln!(
//             "< {:?}",
//             std::str::from_utf8(response.stdout.as_mut_slice())
//         );
//     }
//
//     // let proc = Command::new(server_path_str)
//     //     .arg("--socket-path")
//     //     .arg(socket_path_str)
//     //     .stdin(Stdio::null())
//     //     .stdout(Stdio::null())
//     //     .stderr(Stdio::null())
//     //     .spawn()
//     //     .expect("unable to execute CLI");
//     let client = assuan::Client::connect(server_socket.clone());
//     let inner = AssuanServerCLI {
//         server_path,
//         server_socket,
//         // socket_listener,
//         // client,
//         client: Box::pin(client),
//         // proc,
//     };
//     Ok(inner)
// }
// }
