import logging
import subprocess
import traceback
from typing import Optional, Generator

import assuan
from assuan.common import VarText
from assuan import common, Request, Response, AssuanError

log = logging.getLogger(__name__)


class ProxyAssuanServer(assuan.AssuanServer):
    """A Proxy Assuan Server that essentially echo the exhange in stdout
    then forward the exchange to another Assuan Server
    """

    def __init__(self, fallback_server_program=None, **kwargs):
        self.fallback_server_program = fallback_server_program
        self.fallback_popen = subprocess.Popen(
            [self.fallback_server_program],
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
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
                    parameter_string = parameters
                encoded_parameters = assuan.common.encode(parameter_string)
                assuan_input = f'{request.command} {encoded_parameters}\n'
                log.info(f'PC: {assuan_input}')
                p = subprocess.Popen(
                    [self.fallback_server_program],
                    shell=True,
                    stdout=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                # p = self.fallback_popen
                # p.stdin.write(assuan.common.to_bytes(assuan_input))
                # p.stdin.flush()
                # output, err = '',''
                # while p.poll() is None:
                #     output = p.stdout.read()
                #     err = p.stderr.read()
                output, err = p.communicate(input=assuan.common.to_bytes(assuan_input), timeout=86400)
                if err is not None and len(err) != 0:
                    log.error(f'PE: {err}')
                log.info(f'PS: {output}')
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

            setattr(self, f"_handle_{request.command.lower()}", handle_func)

    def _handle_requests(self) -> None:
        self.__send_response(Response('OK', 'Your orders please'))
        if self.outtake:
            self.outtake.flush()
            while not self.stop:
                line = self.intake.readline() if self.intake else None
                if not line:
                    break  # EOF
                if len(line) > common.LINE_LENGTH:
                    raise AssuanError(message='Line too long')
                if not line.endswith(b'\n'):
                    log.info("C: %r", line)
                    self.__send_error_response(
                        AssuanError(message='Invalid request')
                    )
                    continue
                line = line.rstrip()  # remove the trailing newline
                log.info("C: %r", line)
                request = Request()
                try:
                    request.from_bytes(line)
                except AssuanError as err:
                    self.__send_error_response(err)
                    continue
                self._handle_request(request)

    def _handle_request(self, request: assuan.Request) -> None:
        # dump what the request is
        log.info(f'Handle Request: {request.command} {assuan.common.to_str(request.parameters)}')
        # lazy register handle function to the fallback assuan server
        self._register_fallback_command(request)

        try:
            handle = getattr(self, f"_handle_{request.command.lower()}")
        except AttributeError:
            log.warning('unknown command: %s', request.command)
            self.__send_error_response(AssuanError(message='Unknown command'))
            return

        try:
            responses = handle(request.parameters)
            for response in responses:
                self.__send_response(response)
        except AssuanError as err:
            self.__send_error_response(err)
        except Exception:
            log.error(
                'exception while executing %s:\n%s',
                handle,
                traceback.format_exc().rstrip(),
            )
            self.__send_error_response(
                AssuanError(message='Unspecific Assuan server fault')
            )
        return

    def __send_error_response(self, error: AssuanError) -> None:
        """For internal use by ``._handle_requests()``."""
        self.__send_response(common.error_response(error))

    def __send_response(self, response: assuan.Response) -> None:
        """For internal use by ``._handle_requests()``."""
        # rstring = str(response)
        log.info('S: %s', response)
        if self.outtake:
            self.outtake.write(bytes(response))
            self.outtake.write(b'\n')
            try:
                self.outtake.flush()
            except BrokenPipeError:
                log.info(f'PS: {response}')
                if not self.stop:
                    raise
            except IOError:
                if not self.stop:
                    raise
        else:
            raise Exception('no outtake message provided')