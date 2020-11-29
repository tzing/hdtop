"""Collection of all exception classes
"""


class HdtopException(Exception):
    """Based type for all exceptions"""


class ConfigValueError(HdtopException, ValueError):
    """Config value is not allowed."""

    def __str__(self) -> str:
        msg = f"Invalid configuration value: {self.args[0]}"

        if len(self.args) == 2:
            expected = self.args[1]
            msg += ". Expected values: %s" % ", ".join(expected)

        return msg


class MissingConfigurationError(ConfigValueError):
    """Config is required but not found"""

    def __str__(self) -> str:
        wanted_key = self.args[0]
        return f"Config `{wanted_key}` is required. Use `hdtop config {wanted_key} <value>` to set one."
