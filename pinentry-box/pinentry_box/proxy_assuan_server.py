import logging
import subprocess
from typing import Optional, Generator

import assuan
from assuan.common import VarText

log = logging.getLogger(__name__)


class ProxyAssuanServer(assuan.AssuanServer):
    """A Proxy Assuan Server that essentially echo the exhange in stdout
    then forward the exchange to another Assuan Server
    """

    def __init__(self, fallback_server_program=None, **kwargs):
        self.fallback_server_program = fallback_server_program
        super().__init__(**kwargs)
        self._register_fallback_command(assuan.Request(command='HELP'), override=True)
        self._register_fallback_command(assuan.Request(command='OPTION'), override=True)

    def _handle_bye(self, arg: str) -> Generator['Response', None, None]:
        """BYE command requires us to close fallback server and our own proxy server"""
        for response in super()._handle_bye(arg):
            yield response
        self.disconnect()
        yield assuan.Response('OK', 'closing proxy connection')

    def _register_fallback_command(self, request: assuan.Request, override=False):
        try:
            handle = getattr(self, f"_handle_{request.command.lower()}")
            if override:
                raise AttributeError()
        except AttributeError:
            log.warning('registering new command to fallback server: %s', request.command)

            def handle_func(parameters: Optional[VarText] = None):
                # convert parameters and command again to plaintext assuan request
                parameter_string = ''
                if parameters is not None:
                    parameter_string = assuan.common.to_str(parameters)
                assuan_input = f'{request.command} {parameter_string}\n'
                log.info(assuan_input)
                p = subprocess.Popen(
                    [self.fallback_server_program],
                    stdout=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    stderr=subprocess.PIPE)
                output, err = p.communicate(input=assuan.common.to_bytes(assuan_input))
                log.error(err)
                log.info(output)
                # output can be multiple lines of assuan responses
                responses = []
                for line in output.decode('utf-8').split('\n'):
                    if len(line) == 0:
                        continue
                    response = assuan.Response()
                    response.from_bytes(assuan.common.to_bytes(line))
                    log.info(response)
                    responses.append(response)
                return responses

            setattr(self, f"_handle_{request.command.lower()}", handle_func)

    def _handle_request(self, request: assuan.Request) -> None:
        # dump what the request is
        log.info(f'{request.command} {assuan.common.to_str(request.parameters)}')
        # lazy register handle function to the fallback assuan server
        self._register_fallback_command(request)
        super()._handle_request(request)
