"""Qtile screen and bar configuration.

Builds the panel layout and detects active connected outputs so Qtile creates one
screen configuration for each monitor.

Attributes:
    screens: Screen configurations exported to the main Qtile configuration.
"""

# Autor: Daniel Benjamin Perez Morales
# GitHub: https://github.com/D4nitrix13
# Gitlab: https://gitlab.com/D4nitrix13
# Correo electrónico: danielperezdev@proton.me

from re import fullmatch
from subprocess import PIPE, CompletedProcess, run
from typing import Any, List

from libqtile.bar import Bar
from libqtile.config import Screen
from libqtile.log_utils import logger

from .metrics import BAR_SIZE
from .theme import colors
from .widgets import bottom_widgets, primary_widgets, secondary_widgets


def status_bar(widgets: List[Any]) -> Bar:
    """Creates a Qtile bar using the provided widget list.

    Args:
        widgets: Widgets displayed in the bar.

    Returns:
        Bar: The configured Qtile bar.
    """
    return Bar(
        widgets=widgets,
        size=BAR_SIZE,
        opacity=0.92,
        background=colors.get("dark") or "#0f101a",
    )


# Primary screen configuration.
screens: List[Screen] = [
    Screen(top=status_bar(primary_widgets), bottom=status_bar(widgets=bottom_widgets))
]


def count_connected_monitors() -> int:
    """Counts connected outputs that have an active geometry.

    Returns:
        int: The number of active connected outputs, or one when xrandr fails.
    """
    command: CompletedProcess[str] = run(
        args="xrandr --query",
        shell=True,
        stdout=PIPE,
        stderr=PIPE,
        text=True,
        check=False,
    )
    if command.returncode != 0:
        logger.error(
            f"Failed counting monitors using xrandr --query:\n{command.stderr}"
        )
        return 1

    geometry_pattern: str = r"[0-9]+x[0-9]+\+[0-9]+\+[0-9]+"
    monitor_count: int = 0
    for line in command.stdout.splitlines():
        fields: List[str] = line.split()
        if len(fields) < 2 or fields[1] != "connected":
            continue
        for field in fields[2:]:
            if fullmatch(pattern=geometry_pattern, string=field):
                monitor_count += 1
                break
    return monitor_count


connected_monitors: int = count_connected_monitors()

if connected_monitors > 1:
    # Add one secondary screen configuration for each extra monitor.
    _: int
    for _ in range(1, connected_monitors, 1):
        screens.append(Screen(top=status_bar(secondary_widgets)))
