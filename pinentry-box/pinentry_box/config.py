import logging
import os.path
import re
import shutil
from pathlib import Path
from typing import List, Annotated, Optional, Any, Tuple

import yaml
from pydantic import BaseModel, AfterValidator, FilePath, NewPath, ValidationError


def _executable_path_validator(v: str) -> str:
    if shutil.which(v, os.X_OK) is None:
        raise ValueError("path is not executable or not found")
    return v


def _regexp_validator(v: str) -> str:
    try:
        re.compile(v)
    except Exception as e:
        raise e
    return v


def _log_level(v: int | str) -> int:
    if isinstance(v, int):
        return v

    match v.lower():
        case "critical":
            return logging.CRITICAL
        case "error":
            return logging.ERROR
        case "debug":
            return logging.DEBUG
        case "warning":
            return logging.WARNING
        case "info":
            return logging.INFO
    return logging.ERROR


ExecutablePath = Annotated[str, FilePath, AfterValidator(_executable_path_validator)]
Regexp = Annotated[str, AfterValidator(_regexp_validator)]


class ForwardCondition(BaseModel):
    title: Regexp
    desc: Regexp
    prompt: Regexp
    keyinfo: Regexp


class ForwardRule(BaseModel):
    program: ExecutablePath
    condition: List[ForwardCondition]


class PycharmDebug(BaseModel):
    enable: bool
    port: int
    host: str


class PinentryBoxConfig(BaseModel):
    log_level: Annotated[int | str, AfterValidator(_log_level)]
    log_file: FilePath | NewPath
    log_getpin_redacted: bool
    fallback: ExecutablePath
    pycharm_debug: PycharmDebug
    socket_server_path: Path


class AppConfig(BaseModel):
    pinentry_box: PinentryBoxConfig
    forwards: Optional[List[ForwardRule]]

    @classmethod
    def model_yaml_file_validate(cls, yaml_file, **kwargs):
        with open(yaml_file, "r") as f:
            data = yaml.load(f, yaml.Loader)
            app_config = cls.model_validate(data)
            return app_config

    @classmethod
    def defaults(cls):
        # custom override from env
        # later on, can be a generic function
        pinentry_box__fallback = os.getenv('PINENTRY_BOX__FALLBACK', 'pinentry-mac')
        pinentry_box__pycharm_debug__enable = os.getenv('PINENTRY_BOX__PYCHARM_DEBUG__ENABLE', False)
        if pinentry_box__pycharm_debug__enable == '1':
            pinentry_box__pycharm_debug__enable = True
        return AppConfig(
            pinentry_box=PinentryBoxConfig(
                log_level=logging.ERROR,
                log_file='/tmp/.pinentry-box',
                log_getpin_redacted=True,
                fallback=pinentry_box__fallback,
                socket_server_path=os.path.expanduser('~/.pinentry-box.sock'),
                pycharm_debug=PycharmDebug(
                    enable=pinentry_box__pycharm_debug__enable,
                    port=6113,
                    host='localhost',
                )
            ),
            forwards=[],
        )

def load_config(write_default_config: bool = True) -> Tuple[AppConfig, bool]:
    """
    Load application configuration from predefined paths.

    Args:
        write_default_config: If True and no config file is found, write default config

    Returns:
        Tuple containing:
        - The loaded AppConfig object
        - A boolean indicating whether a config file was found
    """
    app_config = None
    home_dir_config_path = os.path.join(os.path.expanduser('~'), '.config')
    config_path_lists = [
        os.path.curdir,
        home_dir_config_path
    ]
    config_file_found = False

    # Try to load config from different paths
    for cp in config_path_lists:
        try:
            app_config = AppConfig.model_yaml_file_validate(
                os.path.abspath(os.path.join(cp, '.pinentry-box.yaml'))
            )
            config_file_found = True
        except FileNotFoundError:
            pass
        except ValidationError:
            pass
        finally:
            if app_config is not None:
                break

    # Fall back to defaults if no config is found
    if app_config is None:
        app_config = AppConfig.defaults()

    # Write default config if requested and no config file was found
    if write_default_config and not config_file_found:
        try:
            with open(os.path.join(home_dir_config_path, '.pinentry-box.yaml'), 'w') as f:
                yaml.dump(app_config.dict(), f)
        except Exception as e:
            logging.warning(f"Failed to write default config: {e}")

    return app_config, config_file_found
