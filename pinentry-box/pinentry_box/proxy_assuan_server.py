import logging
import os
import subprocess
import tempfile
import time
from typing import Optional, Generator

import assuan
from assuan import Response
from assuan.common import VarText

from pinentry_box import config
from pinentry_box.config import AppConfig

log = logging.getLogger(__name__)


class ProxyAssuanServer(assuan.AssuanServer):
    """A Proxy Assuan Server that essentially echo the exchange in stdout
    then forward the exchange to another Assuan Server
    """

    def __init__(self, app_config: config.AppConfig = None, fallback_server_program=None, with_sleep=False, with_sleep_duration=0.5, **kwargs):
        self.config = app_config
        if self.config is None:
            self.config = AppConfig.defaults()
        self.fallback_server_program = fallback_server_program
        self.with_sleep = with_sleep
        self.with_sleep_duration = with_sleep_duration
        self._start_fallback_server()

        super().__init__(**kwargs)
        self._register_fallback_command(assuan.Request(command='HELP'), override=True)
        self._register_fallback_command(assuan.Request(command='OPTION'), override=True)
        self._register_fallback_command(assuan.Request(command='END'), override=True)
        self._register_fallback_command(assuan.Request(command='CANCEL'), override=True)

    def _wait_for_fallback_output(self):
        if self.with_sleep:
            time.sleep(self.with_sleep_duration)
        return

    def _read_fallback_output_until_ok(self):
        responses = self._read_fallback_responses()
        for response in responses:
            if response.message.strip() == 'OK':
                return
        self.stop = True

    def _start_fallback_server(self):
        """Start pinentry fallback program in the background

        This program needs to be kept alive during the exchange until client send us BYE.
        The reason being the program might store some state in memory during the exchange as security best practice.
        """
        self.fallback_fifo_in = tempfile.mktemp()
        self.fallback_fifo_out = tempfile.mktemp()
        os.mkfifo(self.fallback_fifo_in)

        # We rely on shell redirection because I'm not able to make it work with native python API via named pipe
        # self.fallback_fifo_out is just simple file, not a pipe
        self.fallback_popen = subprocess.Popen(
            f'{self.fallback_server_program}<{self.fallback_fifo_in}>{self.fallback_fifo_out}',
            shell=True,
        )

        # read from our pinentry fallback program until we got the first OK, otherwise go BYE
        while True:
            try:
                self.fallback_stream_fifo_in = open(self.fallback_fifo_in, "w")
                self.fallback_stream_fifo_out = open(self.fallback_fifo_out, "rb")
                log.info(f'pinentry fallback output file: {self.fallback_stream_fifo_out}')

                # we do flush because popen will block until we mark the pipe that someone is writing
                self.fallback_stream_fifo_in.flush()
                self._wait_for_fallback_output()
                self._read_fallback_output_until_ok()
                break
            except OSError as e:
                log.info(e)
                time.sleep(5)

    def _handle_bye(self, arg: str) -> Generator['Response', None, None]:
        """BYE command requires us to close fallback server and our own proxy server"""
        for _ in super()._handle_bye(arg):
            pass
        self.disconnect()
        try:
            self.fallback_stream_fifo_in.write('BYE\n')
            self.fallback_stream_fifo_in.flush()
            self._wait_for_fallback_output()
            self._read_fallback_output_until_ok()
            self.fallback_stream_fifo_in.close()
            self.fallback_stream_fifo_out.close()
            self.fallback_popen.terminate()
        except Exception as e:
            log.info(exc_info=e)
        self.stop = True
        yield assuan.Response('OK', 'closing proxy connection')

    def _read_fallback_responses(self):
        output = b''
        while output == b'':
            while chunk := self.fallback_stream_fifo_out.read():
                output += chunk
            self._wait_for_fallback_output()
        # output can be multiple lines of assuan responses
        responses = []
        for line in output.decode('utf-8').split('\n'):
            if len(line) == 0:
                continue
            response = assuan.Response()
            response_string = assuan.common.encode(line)
            response.from_bytes(assuan.common.to_bytes(response_string))
            responses.append(response)
        return responses

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
                    parameter_string = parameters
                encoded_parameters = assuan.common.encode(parameter_string)
                assuan_input = f'{request.command} {encoded_parameters}'.strip()
                log.info(f'PC: {assuan_input}')

                self.fallback_stream_fifo_in.write(assuan_input)
                self.fallback_stream_fifo_in.write('\n')
                self.fallback_stream_fifo_in.flush()

                responses = self._read_fallback_responses()
                assuan_output = ''
                for r in responses:
                    parameter_string = ''
                    if parameters is not None:
                        parameter_string = parameters
                    encoded_parameters = assuan.common.encode(parameter_string)
                    # masked the secret
                    if self.config.pinentry_box.log_getpin_redacted and r.message == 'D' and request.command.lower() == 'getpin':
                        encoded_parameters = '[REDACTED]'
                    assuan_output += f'{r.message} {encoded_parameters}\n'
                log.info(f'PS: {assuan_output}')
                return responses

            setattr(self, f"_handle_{request.command.lower()}", handle_func)

    def _handle_request(self, request: assuan.Request) -> None:
        # dump what the request is
        log.info(f'Handle Request: {request.command} {assuan.common.to_str(request.parameters)}')
        # lazy register handle function to the fallback assuan server
        self._register_fallback_command(request)
        super()._handle_request(request)
