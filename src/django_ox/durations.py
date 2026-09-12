"""
Duration options shared by the management commands.

`ox_prune --older-than` has always accepted `7d`, `24h`, `90m`, `45s` or a
plain number of seconds, while `ox_health --max-age` and `--worker-timeout`
took a bare float of seconds. Two commands from the same package therefore
answered differently to the same string: `--older-than 7d` worked and
`--max-age 7d` did not.

The parser lives here, outside the management commands, so both can import it
without one command reaching into another. `parse_duration` keeps the exact
forms it has always accepted, because it is the public surface of
`ox_prune --older-than`. `parse_seconds` is the wider door the health checks
need: it accepts the same forms plus a plain fractional number of seconds,
which is what they took before they took durations.
"""

from __future__ import annotations

import re
from datetime import timedelta

from django.core.management.base import CommandError

__all__ = ["DURATION_UNITS", "parse_duration", "parse_seconds"]

DURATION_UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400}

_DURATION = re.compile(r"(\d+)([smhd]?)")


def parse_duration(value: str) -> timedelta:
    """Parse '7d' / '24h' / '90m' / '45s' or a plain number of seconds."""
    match = _DURATION.fullmatch(value.strip())
    if match is None:
        raise CommandError(
            f"Invalid duration {value!r}; use forms like 7d, 24h, 90m, 45s, "
            "or a plain number of seconds."
        )
    number, unit = match.groups()
    return timedelta(seconds=int(number) * DURATION_UNITS[unit or "s"])


def parse_seconds(value: str) -> float:
    """
    Seconds from a duration form, or from a plain fractional number.

    This is the only loosening of the two: `ox_health --max-age` and
    `--worker-timeout` were `type=float`, so `120.5` has to keep working.
    Negative numbers still parse here and are rejected by the command's own
    threshold check, which is what reported them before.
    """
    text = value.strip()
    try:
        return parse_duration(text).total_seconds()
    except CommandError as duration_error:
        try:
            return float(text)
        except ValueError:
            raise duration_error from None
