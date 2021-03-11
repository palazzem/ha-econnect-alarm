"""Helper methods to reuse common logic across econnect_alarm module."""


def parse_areas_config(config, raises=False):
    """Parse area config that is represented as a comma separated value.

    Usage:
        parse_areas_config("3,4")  # Returns [3, 4]

    Args:
        config: The string that is stored in the configuration registry.
        raises: If set `True`, raises exceptions if they happen
    Raises:
        ValueError: If given config is not a list of integers
        AttributeError: If given config is `None` object
    Returns:
        A Python list with integers representing areas ID, such as `[3, 4]`,
        or `None` if invalid.
    """
    try:
        return [int(x) for x in config.split(",")]
    except (ValueError, AttributeError) as err:
        if raises:
            raise err
        return None
