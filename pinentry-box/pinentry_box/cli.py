#!/usr/bin/env python
import logging
import os.path

from pydantic import ValidationError

from pinentry_box import config
from pinentry_box.proxy_assuan_server import ProxyAssuanServer


def main():
    app_config = None
    config_path_lists = [
        os.path.curdir,
        os.path.join(os.path.abspath('~'), 'local')
    ]
    for cp in config_path_lists:
        try:
            app_config = config.AppConfig.model_yaml_file_validate(
                os.path.abspath(os.path.join(cp, '.pinentry-box.yaml'))
            )
        except FileNotFoundError:
            pass
        except ValidationError:
            pass
        finally:
            if app_config is not None:
                break

    if app_config is None:
        app_config = config.AppConfig.defaults()

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
        import pydevd_pycharm
        pydevd_pycharm.settrace(
            app_config.pinentry_box.pycharm_debug.host,
            port=app_config.pinentry_box.pycharm_debug.port,
            stdoutToServer=True,
            stderrToServer=True)

    server = ProxyAssuanServer(name='pinentry-box', fallback_server_program=pinentry_fallback)
    # to test something via debugger flow, use this to avoid IO blocking:
    # server.intake = io.BytesIO(b'BYE\n')
    server.run()


if __name__ == '__main__':
    main()
