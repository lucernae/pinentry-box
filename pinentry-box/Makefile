

run-pinentry-box:
	direnv exec . poetry run python pinentry_box/cli.py

build:
	nix build .

reset-gpg-agent:
	gpgconf --kill gpg-agent

test-sign:
	direnv exec . bash -c 'gpg --trust-model always --encrypt --sign --armor -r "$${EMAIL}" -o tmp/testfile.txt.asc testfile.txt'

tail-log:
	tail -f /tmp/pinentry-box.log -n 100