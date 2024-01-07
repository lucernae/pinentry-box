#!/usr/bin/env python
import logging
import os.path
import socket

import assuan
import click
import yaml

from pydantic import ValidationError

from pinentry_box import config
from pinentry_box.proxy_assuan_server import ProxyAssuanServer


@click.command()
@click.option('--socket-path', help='Unix Socket to start server mode')
@click.option('--start-server/--start-shell', default=False, help='Start pinentry as socket server mode')
def main(socket_path=None, start_server=False):
    app_config = None
    home_dir_config_path = os.path.join(os.path.expanduser('~'), '.config')
    config_path_lists = [
        os.path.curdir,
        home_dir_config_path
    ]
    config_file_found = False
    for cp in config_path_lists:
        try:
            app_config = config.AppConfig.model_yaml_file_validate(
                os.path.abspath(os.path.join(cp, '.pinentry-box.yaml'))
            )
            config_file_found = True
        except FileNotFoundError:
            pass
        except ValidationError:
            pass
        finally:
            if app_config is not None:
                break

    if app_config is None:
        app_config = config.AppConfig.defaults()

    # write config
    if not config_file_found:
        with open(os.path.join(home_dir_config_path, '.pinentry-box.yaml'), 'w') as f:
            yaml.dump(app_config.dict(), f)

    logging.basicConfig(
        filename=app_config.pinentry_box.log_file,
        filemode='w',
        level=app_config.pinentry_box.log_level)
    logging.getLogger().setLevel(app_config.pinentry_box.log_level)
    pinentry_fallback = os.getenv('PINENTRY_BOX__FALLBACK', app_config.pinentry_box.fallback)
    logging.info(f'Using pinentry fallback: {pinentry_fallback}')

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
    # to test something via debugger flow, use this to avoid IO blocking:
    # server.intake = io.BytesIO(b'BYE\n')
    if not start_server:

        server = ProxyAssuanServer(
            name='pinentry-box',
            app_config=app_config,
            fallback_server_program=pinentry_fallback)
        server.run()
    else:
        socket_path = socket_path or str(app_config.pinentry_box.socket_server_path)
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
            app_config=app_config,
            fallback_server_program=pinentry_fallback,
        )
        print(f'D {socket_path}')
        print(f'OK Server started with socket')
        server.run()


if __name__ == '__main__':
    main()
