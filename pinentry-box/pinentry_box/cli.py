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
    logging.getLogger(__name__).setLevel(log_level)
    logging.getLogger('assuan').setLevel(log_level)
    logging.info('test logging')
    pinentry_mac_program = '/nix/store/ckc8kwsqjzgigwak9q1jkag4axv2c2mm-pinentry-mac-1.1.1.1/Applications/pinentry-mac.app/Contents/MacOS/pinentry-mac'
    pinentry_fallback = os.getenv('PINENTRY_BOX_FALLBACK', pinentry_mac_program)
    logging.info(f'Using pinentry fallback: {pinentry_fallback}')
    server = ProxyAssuanServer(name='pinentry-box', fallback_server_program=pinentry_fallback)
    # to test something via debugger flow, use this to avoid IO blocking:
    # server.intake = io.BytesIO(b'BYE\n')
    server.run()

if __name__ == '__main__':
    main()
