
kill-pinentry-box-daemon:
	kill -TERM $$(cat $${HOME}/.pinentry-box.pid)

socat:
	socat - UNIX-CONNECT:$${HOME}/.pinentry-box.sock

socat-gpg:
	socat - UNIX-CONNECT:$${GNUPGHOME}/S.gpg-agent
