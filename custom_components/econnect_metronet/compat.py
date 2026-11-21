"""Schema validation library of the running Home Assistant.

`vol` is probatio on Home Assistant 2026.9 and later, and voluptuous before it, so the
schemas the integration builds are always the kind Home Assistant validates forms with.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import probatio as vol
else:
    try:
        import probatio as vol
    except ImportError:
        import voluptuous as vol

__all__ = ["vol"]
