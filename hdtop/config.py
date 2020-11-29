"""Configuration proceeding
"""
import argparse
import configparser
import logging
import os
import pathlib
import typing

import hdtop.const


__all__ = ["get_configs", "get_config", "set_config"]

logger = logging.getLogger("hdtop.config")

_configs = None


def setup_argparse():
    """Setup arg parse for cli."""
    parser = argparse.ArgumentParser()
    parser.set_defaults(action="config", func=cli_handle_config)

    parser.add_argument(
        "key",
        choices=[
            "%s.%s" % (section, key)
            for section, key, _, _ in hdtop.const.DEFAULT_CONFIGS
        ],
        help="Config key to get/set",
    )
    parser.add_argument(
        "value",
        nargs="?",
        help="Get config value if this value is set. Or set value when given.",
    )

    return parser


def cli_handle_config(args: "argparse.Namespace"):
    """Main function on action is config"""
    section, name = args.key.split(".", 1)

    if not args.value:  # query value
        # get value
        value = get_config(section, name)

        # show
        if value:
            print(value)
        else:
            print("<unset>")

        return 0

    else:  # set value
        if set_config(section, name, args.value):
            return 0
        else:
            return 1


def get_config_filename():
    """Get config filename. Expected: $XDG_CACHE_HOME/hdtop/hdtop.conf"""
    config_home = os.environ.get("XDG_CONFIG_HOME", "$HOME/.config")
    config_home = os.path.expandvars(config_home)
    config_home = os.path.expanduser(config_home)

    filename = (
        pathlib.Path(config_home).resolve()
        / hdtop.const.PROG_NAME
        / (hdtop.const.PROG_NAME + ".conf")
    )

    return filename


def get_configs() -> dict:
    """Get complete configuration dict. Read config from XDG_CACHE_HOME if not
    loaded."""
    global _configs
    if _configs:
        return _configs

    # read config
    reader = configparser.ConfigParser()
    reader.read(get_config_filename())

    # build dict and set default
    configs = {}

    for section, key, type_, default in hdtop.const.DEFAULT_CONFIGS:
        value = reader.get(section, key, fallback=default)
        if value is not default:
            value = type_(value)
        configs.setdefault(section, {}).setdefault(key, value)

    _configs = configs
    return configs


def get_config(section, name):
    """Get config value."""
    return get_configs()[section][name]


def set_config(section, name, value) -> bool:
    """Set config value."""
    global _configs
    if not _configs:
        get_configs()

    # check type and set value
    _, _, expect_type, _ = next(
        filter(
            lambda x: x[:2] == (section, name),
            hdtop.const.DEFAULT_CONFIGS,
        )
    )
    try:
        _configs[section][name] = expect_type(value)

    except hdtop.exception.ConfigValueError as e:
        logger.error(e)
        return False

    except ValueError:
        logger.error(
            "Type convert error: expect %s for %s.%s, input= %s",
            expect_type.__name__,
            section,
            name,
            value,
        )
        return False

    # write config file
    writer = configparser.ConfigParser()
    for section, values in _configs.items():
        writer.add_section(section)
        for key, value in values.items():
            if value is None:
                continue
            writer.set(section, key, str(value))

    filename = get_config_filename()
    filename.parent.mkdir(exist_ok=True)
    with open(filename, "w") as fp:
        writer.write(fp)

    return True
