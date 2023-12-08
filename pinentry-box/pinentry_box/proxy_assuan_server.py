import io
import logging
import os
import subprocess
import sys
import tempfile
import time
import traceback
from typing import Optional, Generator

import assuan
from assuan import common, Request, Response, AssuanError
from assuan.common import VarText

log = logging.getLogger(__name__)


class ProxyAssuanServer(assuan.AssuanServer):
    """A Proxy Assuan Server that essentially echo the exhange in stdout
    then forward the exchange to another Assuan Server
    """

    def __init__(self, fallback_server_program=None, **kwargs):
        self.fallback_server_program = fallback_server_program
        self.fallback_fifo_in = tempfile.mktemp()
        self.fallback_fifo_out = tempfile.mktemp()
        self.fallback_fifo_err = tempfile.mktemp()
        os.mkfifo(self.fallback_fifo_in)
        # os.mkfifo(self.fallback_fifo_out)
        # os.mkfifo(self.fallback_fifo_err)

        def _opener(path, flags):
            return os.open(path, flags | os.O_NONBLOCK)

        # perform read to unblock write fifo
        # fifo_in = open(self.fallback_fifo_in, "rb", opener=_opener)
        # fifo_in.read()

        # self.fallback_stream_fifo_out: io.BytesIO = open(self.fallback_fifo_out, "rb", opener=_opener)
        # self.fallback_stream_fifo_err: io.BytesIO = open(self.fallback_fifo_err, "rb", opener=_opener)
        # self.fallback_stream_fifo_in: io.BytesIO = open(self.fallback_fifo_in, "w", opener=_opener)

        # self.fallback_popen = subprocess.Popen(
        #     [self.fallback_server_program],
        #     stdout=self.fallback_stream_fifo_out,
        #     stderr=self.fallback_stream_fifo_err,
        #     stdin=self.fallback_stream_fifo_in,
        # )
        # self.fallback_popen = subprocess.Popen(
        #     f'{self.fallback_server_program}<{self.fallback_fifo_in}>{self.fallback_fifo_out}',
        #     # stdout=subprocess.PIPE,
        #     # stderr=subprocess.PIPE,
        #     shell=True,
        # )
        #
        # # self.fallback_popen = subprocess.Popen(
        # #     [self.fallback_server_program],
        # #     stdout=subprocess.PIPE,
        # #     stderr=subprocess.PIPE,
        # #     stdin=subprocess.PIPE,
        # # )
        #
        # while True:
        #     try:
        #         self.fallback_stream_fifo_in = open(self.fallback_fifo_in, "w", opener=_opener)
        #         break
        #     except OSError as e:
        #         log.info(e)
        #         time.sleep(5)

        self._start_fallback_server()

        super().__init__(**kwargs)
        self._register_fallback_command(assuan.Request(command='HELP'), override=True)
        self._register_fallback_command(assuan.Request(command='OPTION'), override=True)

    def connect(self) -> None:
        """Connect to the GPG Agent."""
        if not self.intake:
            log.info('read from stdin')
            self.intake = sys.stdin.buffer
        if not self.outtake:
            log.info('write to stdout')
            self.outtake = sys.stdout.buffer
        # self.reconnect_outtake()

    def reconnect_outtake(self):
        fileno = sys.stdout.fileno()
        encoding = sys.stdout.encoding
        line_buffering = sys.stdout.line_buffering
        sys.stdout = io.TextIOWrapper(open(fileno, 'wb'), encoding=encoding, line_buffering=True)
        self.outtake = sys.stdout.buffer

    def _handle_getpin(self, parameters):
        # convert parameters and command again to plaintext assuan request
        parameter_string = ''
        if parameters is not None:
            parameter_string = parameters
        encoded_parameters = assuan.common.encode(parameter_string)
        assuan_input = f'GETPIN {encoded_parameters}'.strip()
        assuan_input = f'{assuan_input}\n'
        log.info(f'PC: {assuan_input}')
        # p = subprocess.Popen(
        #     [self.fallback_server_program],
        #     shell=True,
        #     stdout=subprocess.PIPE,
        #     stdin=subprocess.PIPE,
        #     stderr=subprocess.PIPE,
        # )
        # p = self.fallback_popen
        # p.stdin.write(assuan.common.to_bytes(assuan_input))
        # p.stdin.flush()
        # p.wait()
        # output = p.stdout.read()
        # err = p.stderr.read()
        # output, err = '', ''
        # while p.poll() is None:
        #     output = p.stdout.read()
        #     err = p.stderr.read()
        # output, err = p.communicate(input=assuan.common.to_bytes(assuan_input), timeout=86400)
        # output, err = p.communicate(timeout=86400)
        # if self.fallback_popen.poll() is not None:
        #     self._start_fallback_server()

        self.fallback_stream_fifo_in.write(assuan_input)
        self.fallback_stream_fifo_in.flush()

        # def _opener(path, flags):
        #     return os.open(path, flags | os.O_NONBLOCK)

        # with open(self.fallback_fifo_out, 'rb', opener=_opener) as outs:
        #     output = outs.read()
        # with open(self.fallback_fifo_err, 'rb', opener=_opener) as errs:
        #     err = errs.read()

        time.sleep(0.5)
        output = b''
        while chunk := self.fallback_stream_fifo_out.read():
            output += chunk

        err = None
        # err = self.fallback_stream_fifo_err.read()
        # p = self.fallback_popen
        # p.stdin.write(assuan.common.to_bytes(assuan_input))
        # p.stdin.flush()
        # output = p.stdout.read()
        # err = p.stderr.read()

        if err is not None and len(err) != 0:
            log.error(f'PE: {err}')
        if output is None:
            output = b''
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

    def _handle_setkeyinfo(self, parameters):
        # convert parameters and command again to plaintext assuan request
        parameter_string = ''
        if parameters is not None:
            parameter_string = parameters
        encoded_parameters = assuan.common.encode(parameter_string)
        assuan_input = f'SETKEYINFO {encoded_parameters}'.strip()
        assuan_input = f'{assuan_input}\n'
        log.info(f'PC: {assuan_input}')
        # p = subprocess.Popen(
        #     [self.fallback_server_program],
        #     shell=True,
        #     stdout=subprocess.PIPE,
        #     stdin=subprocess.PIPE,
        #     stderr=subprocess.PIPE,
        # )
        # p = self.fallback_popen
        # p.stdin.write(assuan.common.to_bytes(assuan_input))
        # p.stdin.flush()
        # p.wait()
        # output = p.stdout.read()
        # err = p.stderr.read()
        # output, err = '', ''
        # while p.poll() is None:
        #     output = p.stdout.read()
        #     err = p.stderr.read()
        # output, err = p.communicate(input=assuan.common.to_bytes(assuan_input), timeout=86400)
        # output, err = p.communicate(timeout=86400)
        # if self.fallback_popen.poll() is not None:
        #     self._start_fallback_server()

        self.fallback_stream_fifo_in.write(assuan_input)
        self.fallback_stream_fifo_in.flush()

        # def _opener(path, flags):
        #     return os.open(path, flags | os.O_NONBLOCK)

        # with open(self.fallback_fifo_out, 'rb', opener=_opener) as outs:
        #     output = outs.read()
        # with open(self.fallback_fifo_err, 'rb', opener=_opener) as errs:
        #     err = errs.read()

        time.sleep(0.5)
        output = b''
        while chunk := self.fallback_stream_fifo_out.read():
            output += chunk

        err = None
        # err = self.fallback_stream_fifo_err.read()
        # p = self.fallback_popen
        # p.stdin.write(assuan.common.to_bytes(assuan_input))
        # p.stdin.flush()
        # output = p.stdout.read()
        # err = p.stderr.read()

        if err is not None and len(err) != 0:
            log.error(f'PE: {err}')
        if output is None:
            output = b''
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

    def _handle_getinfo(self, parameters):
        # convert parameters and command again to plaintext assuan request
        parameter_string = ''
        if parameters is not None:
            parameter_string = parameters
        encoded_parameters = assuan.common.encode(parameter_string)
        assuan_input = f'GETINFO {encoded_parameters}'.strip()
        assuan_input = f'{assuan_input}\n'
        log.info(f'PC: {assuan_input}')
        # p = subprocess.Popen(
        #     [self.fallback_server_program],
        #     shell=True,
        #     stdout=subprocess.PIPE,
        #     stdin=subprocess.PIPE,
        #     stderr=subprocess.PIPE,
        # )
        # p = self.fallback_popen
        # p.stdin.write(assuan.common.to_bytes(assuan_input))
        # p.stdin.flush()
        # p.wait()
        # output = p.stdout.read()
        # err = p.stderr.read()
        # output, err = '', ''
        # while p.poll() is None:
        #     output = p.stdout.read()
        #     err = p.stderr.read()
        # output, err = p.communicate(input=assuan.common.to_bytes(assuan_input), timeout=86400)
        # output, err = p.communicate(timeout=86400)
        # if self.fallback_popen.poll() is not None:
        #     self._start_fallback_server()

        self.fallback_stream_fifo_in.write(assuan_input)
        self.fallback_stream_fifo_in.flush()

        # def _opener(path, flags):
        #     return os.open(path, flags | os.O_NONBLOCK)

        # with open(self.fallback_fifo_out, 'rb', opener=_opener) as outs:
        #     output = outs.read()
        # with open(self.fallback_fifo_err, 'rb', opener=_opener) as errs:
        #     err = errs.read()

        time.sleep(0.5)
        output = b''
        while chunk := self.fallback_stream_fifo_out.read():
            output += chunk

        err = None
        # err = self.fallback_stream_fifo_err.read()
        # p = self.fallback_popen
        # p.stdin.write(assuan.common.to_bytes(assuan_input))
        # p.stdin.flush()
        # output = p.stdout.read()
        # err = p.stderr.read()

        if err is not None and len(err) != 0:
            log.error(f'PE: {err}')
        if output is None:
            output = b''
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

    def _start_fallback_server(self):

        def _opener(path, flags):
            return os.open(path, flags | os.O_NONBLOCK)

        self.fallback_popen = subprocess.Popen(
            f'{self.fallback_server_program}<{self.fallback_fifo_in}>{self.fallback_fifo_out}',
            # stdout=subprocess.PIPE,
            # stderr=subprocess.PIPE,
            shell=True,
        )

        # self.fallback_popen = subprocess.Popen(
        #     [self.fallback_server_program],
        #     stdout=subprocess.PIPE,
        #     stderr=subprocess.PIPE,
        #     stdin=subprocess.PIPE,
        # )

        while True:
            try:
                self.fallback_stream_fifo_in = open(self.fallback_fifo_in, "w")
                self.fallback_stream_fifo_out = open(self.fallback_fifo_out, "rb")
                log.info(self.fallback_stream_fifo_out)
                self.fallback_stream_fifo_in.flush()
                time.sleep(0.5)
                while chunk := self.fallback_stream_fifo_out.read():
                    log.info(chunk)
                # self.fallback_stream_fifo_err = open(self.fallback_fifo_err, "rb")
                break
            except OSError as e:
                log.info(e)
                time.sleep(5)


    def _handle_bye(self, arg: str) -> Generator['Response', None, None]:
        """BYE command requires us to close fallback server and our own proxy server"""
        for response in super()._handle_bye(arg):
            yield response
        self.disconnect()
        self.fallback_popen.terminate()
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
                assuan_input = f'{request.command} {encoded_parameters}'.strip()
                assuan_input = f'{assuan_input}\n'
                log.info(f'PC: {assuan_input}')
                # p = subprocess.Popen(
                #     [self.fallback_server_program],
                #     shell=True,
                #     stdout=subprocess.PIPE,
                #     stdin=subprocess.PIPE,
                #     stderr=subprocess.PIPE,
                # )
                # p = self.fallback_popen
                # p.stdin.write(assuan.common.to_bytes(assuan_input))
                # p.stdin.flush()
                # p.wait()
                # output = p.stdout.read()
                # err = p.stderr.read()
                # output, err = '', ''
                # while p.poll() is None:
                #     output = p.stdout.read()
                #     err = p.stderr.read()
                # output, err = p.communicate(input=assuan.common.to_bytes(assuan_input), timeout=86400)
                # output, err = p.communicate(timeout=86400)
                # if self.fallback_popen.poll() is not None:
                #     self._start_fallback_server()

                self.fallback_stream_fifo_in.write(assuan_input)
                self.fallback_stream_fifo_in.flush()

                # def _opener(path, flags):
                #     return os.open(path, flags | os.O_NONBLOCK)

                # with open(self.fallback_fifo_out, 'rb', opener=_opener) as outs:
                #     output = outs.read()
                # with open(self.fallback_fifo_err, 'rb', opener=_opener) as errs:
                #     err = errs.read()

                time.sleep(0.5)
                output = b''
                while chunk := self.fallback_stream_fifo_out.read():
                    output += chunk

                err = None
                # err = self.fallback_stream_fifo_err.read()
                # p = self.fallback_popen
                # p.stdin.write(assuan.common.to_bytes(assuan_input))
                # p.stdin.flush()
                # output = p.stdout.read()
                # err = p.stderr.read()

                if err is not None and len(err) != 0:
                    log.error(f'PE: {err}')
                if output is None:
                    output = b''
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
                self.reconnect_outtake()
                self.__send_response(response)
                # log.info(f'PS: {response}')
                # if not self.stop:
                #     raise
            except IOError:
                if not self.stop:
                    raise
        else:
            raise Exception('no outtake message provided')
