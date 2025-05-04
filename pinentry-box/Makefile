.PHONY: build run-pinentry-box reset-gpg-agent kill-pinentry-box test-sign tail-log run-pinentry-box-server-debug-mode

run-pinentry-box:
	direnv exec . poetry run python pinentry_box/cli.py

run-pinentry-box-server-daemon-mode:
	pinentry-box --start-server --start-daemon

run-pinentry-box-server-mode:
	pinentry-box --start-server

run-pinentry-box-server-debug-mode:
	PINENTRY_BOX__PYCHARM_DEBUG__ENABLE=1 pinentry-box --start-server --start-daemon

build:
	nix build .

reset-gpg-agent:
	gpgconf --kill gpg-agent

kill-pinentry-box:
	@if [ -f ~/.pinentry-box.pid ]; then \
		if kill -0 $$(cat ~/.pinentry-box.pid) 2>/dev/null; then \
			kill -TERM $$(cat ~/.pinentry-box.pid); \
		else \
			echo "Process not running"; \
			rm ~/.pinentry-box.pid; \
		fi; \
	else \
		echo "PID file not found"; \
	fi

test-sign:
	direnv exec . bash -c 'gpg --trust-model always --encrypt --sign --armor -r "$${EMAIL}" -o tmp/testfile.txt.asc testfile.txt'

tail-log:
	tail -f /tmp/.pinentry-box -n 100

socat-help:
	echo "HELP" | socat - UNIX-CONNECT:$${HOME}/.pinentry-box.sock

socat-getpin:
	echo "GETPIN" | socat - UNIX-CONNECT:$${HOME}/.pinentry-box.sock

socat-end:
	echo "END" | socat - UNIX-CONNECT:$${HOME}/.pinentry-box.sock

socat-bye:
	echo "BYE" | socat - UNIX-CONNECT:$${HOME}/.pinentry-box.sock

socat-quit:
	echo "QUIT" | socat - UNIX-CONNECT:$${HOME}/.pinentry-box.sock

socat:
	socat - UNIX-CONNECT:$${HOME}/.pinentry-box.sock
