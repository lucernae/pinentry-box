#!/usr/bin/env python
import logging
import os.path
import signal
import socket
import sys

import assuan
import click
import yaml

from pinentry_box import config
from pinentry_box.proxy_assuan_server import ProxyAssuanServer


def cleanup_daemon(socket_path, pid_file):
    """Clean up daemon resources"""
    try:
        if os.path.exists(socket_path):
            os.remove(socket_path)
        if os.path.exists(pid_file):
            os.remove(pid_file)
    except Exception as e:
        logging.error(f"Error during cleanup: {e}")

def signal_handler(signum, frame, socket_path, pid_file):
    """Handle termination signals"""
    logging.info(f"Received signal {signum}, shutting down...")
    cleanup_daemon(socket_path, pid_file)
    sys.exit(0)

@click.command()
@click.option('--socket-path', help='Unix Socket to start server mode')
@click.option('--start-server/--start-shell', default=False, help='Start pinentry as socket server mode')
@click.option('--start-daemon/--no-start-daemon', default=False, help='Start pinentry as socket server in daemon mode')
def main(socket_path=None, start_server=False, start_daemon=False):
    app_config, config_file_found = config.load_config()

    logging.basicConfig(
        filename=app_config.pinentry_box.log_file,
        filemode='w',
        level=logging.ERROR)
    logging.getLogger('root').setLevel(logging.ERROR)
    logging.getLogger().setLevel(app_config.pinentry_box.log_level)
    logging.info(f'Logging level: {app_config.pinentry_box.log_level}')
    logging.info(f'config: {app_config.json()}')
    pinentry_fallback = os.getenv('PINENTRY_BOX__FALLBACK', app_config.pinentry_box.fallback)
    logging.info(f'Using pinentry fallback: {pinentry_fallback}')

    # to test something via debugger flow, use this to avoid IO blocking:
    # server.intake = io.BytesIO(b'BYE\n')
    if not start_server:

        run_debug_server(app_config)

        server = ProxyAssuanServer(
            name='pinentry-box',
            app_config=app_config,
            fallback_server_program=pinentry_fallback)
        server.run()
    else:
        socket_path = socket_path or str(app_config.pinentry_box.socket_server_path)
        pid_file = os.path.join(os.path.dirname(socket_path), '.pinentry-box.pid')

        if start_daemon:
            if os.path.exists(socket_path) or os.path.exists(pid_file):
                print(f'Socket path {socket_path} or pid file {pid_file} already exists, exiting...')
                sys.exit(1)
            # First fork
            pid = os.fork()
            if pid > 0:
                # Exit first parent
                return

            # Decouple from parent environment
            os.chdir('/')
            os.setsid()
            os.umask(0)

            # Second fork
            pid = os.fork()
            if pid > 0:
                # Exit from second parent
                sys.exit(0)

            # Close all file descriptors
            for fd in range(0, 3):
                try:
                    os.close(fd)
                except OSError:
                    pass

            # Redirect standard file descriptors
            sys.stdout.flush()
            sys.stderr.flush()

            with open(os.devnull, 'r') as f:
                os.dup2(f.fileno(), sys.stdin.fileno())
            with open(app_config.pinentry_box.log_file, 'a+') as f:
                os.dup2(f.fileno(), sys.stdout.fileno())
                os.dup2(f.fileno(), sys.stderr.fileno())

            # Write PID file
            with open(pid_file, 'w') as f:
                f.write(str(os.getpid()))

            # Register signal handlers
            signal.signal(signal.SIGTERM, lambda signum, frame: signal_handler(signum, frame, socket_path, pid_file))
            signal.signal(signal.SIGINT, lambda signum, frame: signal_handler(signum, frame, socket_path, pid_file))

        run_debug_server(app_config)
        try:
            os.remove(socket_path)
        except FileNotFoundError:
            pass
        unix_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        unix_socket.bind(socket_path)
        unix_socket.listen(1)
        server = assuan.AssuanSocketServer(
            name='pinentry-box',
            socket=unix_socket,
            server=ProxyAssuanServer,
            listen_to_quit=True,
            app_config=app_config,
            fallback_server_program=pinentry_fallback,
        )
        print(f'D {socket_path}')
        print(f'OK Server started with socket')
        try:
            server.run()
        finally:
            try:
                os.remove(socket_path)
            except FileNotFoundError:
                pass
            if start_daemon:
                cleanup_daemon(socket_path, pid_file)


def run_debug_server(app_config):
    pycharm_debug_mode = os.getenv('PINENTRY_BOX__PYCHARM_DEBUG__ENABLE', app_config.pinentry_box.pycharm_debug.enable)
    if pycharm_debug_mode == '1' or pycharm_debug_mode == True:
        pycharm_debug_mode = True
    else:
        pycharm_debug_mode = False
    logging.info(f'Using debug mode: {pycharm_debug_mode}')
    if pycharm_debug_mode:
        try:
            import pydevd_pycharm
            pydevd_pycharm.settrace(
                app_config.pinentry_box.pycharm_debug.host,
                port=app_config.pinentry_box.pycharm_debug.port,
                stdoutToServer=True,
                stderrToServer=True)
        except Exception:
            # bypass if there are no debug server
            pass


if __name__ == '__main__':
    main()
