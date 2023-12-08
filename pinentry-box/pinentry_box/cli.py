#!/usr/bin/env python
import io
import logging
import os.path
import assuan

from pinentry_box.proxy_assuan_server import ProxyAssuanServer


def default_gpg_socket_location():
    return os.path.expanduser('~/.gnupg/S.gpg-agent')


def client_debug():
    client = assuan.AssuanClient(name='pinentry-box')
    try:
        socket_location = default_gpg_socket_location()
        print(socket_location)
        client.connect(socket_location)
        r = assuan.Request(command='HELP')
        responses, data = client.make_request(request=r, response=True)
        print(responses)
        print(data)
        for r in responses:
            print(r)
    finally:
        client.disconnect()


def main():
    log_level = logging.DEBUG
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    logging.basicConfig(filename='/tmp/pinentry-box.log', filemode='w', level=log_level)
    logging.getLogger(__name__).setLevel(logging.CRITICAL)
    logging.getLogger('assuan').setLevel(log_level)
    logging.info('test logging')
    pinentry_mac_program = 'pinentry-mac'
    pinentry_fallback = os.getenv('PINENTRY_BOX_FALLBACK', pinentry_mac_program)
    logging.info(f'Using pinentry fallback: {pinentry_fallback}')

    pycharm_debug_mode = os.getenv('PYCHARM_DEBUG_MODE', '0')
    logging.info(f'Using debug mode: {pycharm_debug_mode}')
    if pycharm_debug_mode == '1':
        import pydevd_pycharm
        pydevd_pycharm.settrace('localhost', port=6113, stdoutToServer=True, stderrToServer=True)

    server = ProxyAssuanServer(name='pinentry-box', fallback_server_program=pinentry_fallback)
    # to test something via debugger flow, use this to avoid IO blocking:
    # server.intake = io.BytesIO(b'BYE\n')
    server.run()


if __name__ == '__main__':
    main()
