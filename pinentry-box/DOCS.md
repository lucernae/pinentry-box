# Pinentry Box Documentation

## Installing Pinentry Box

**Not Yet Implemented**

### Via Nix Flake

```shell
nix profile install github:lucernae/pinentry-box?dir=pinentry_box
```

I have no idea at the moment on how I should package the binary for arbitrary OS and environment, other than using Nix.

## Configuration files

**Not Yet Implemented**

Since mostly Pinentry Box is designed to be used as proxy to another Pinentry,
it should support configuration files.

Global configuration files are stored in: `~/.local/.pinentry-box.yaml`.

We will support YAML for now, but supporting TOML should be straightforward later.

In a contextual execution, Pinentry Box will try to detect configuration in the current working directory `.pinentry-box.yaml`.

Current file structure

```yaml
pinentry_box:
  log_level: ERROR # default log level for pinentry_box module
  log_file: /tmp/.pinentry-box # default location for the log file
  log_getpin_redacted: true # mask the getpin value logs to not reveal the secret
  fallback: pinentry-mac # fallback program of the pinentry
  pycharm_debug: # for PyCharm debugging
    enable: false #
    port: 6113
    host: localhost
forwards:
  - program:
    # conditions is a map of regexp matcher
    # if conditions is fulfilled then the pinentry program of `program` is going to be executed
    # each condition is a list of regexp
    conditions:
      title:
      desc:
      prompt:
      keyinfo:
```

## Environment vars

**Not Yet Implemented**

variable format is just following config file structures with the rules:

1. Var name all caps
2. Nesting uses double underscores
3. Array indices were enclosed by double underscores

Environment vars values takes precedences over config files.

## Let GPG agent uses pinentry-box

In the `~/.gnupg/gpg-agent.conf` add:

```text
pinentry-program pinentry-box
```
