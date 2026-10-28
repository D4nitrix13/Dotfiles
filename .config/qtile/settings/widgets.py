"""Qtile widget bar configuration.

Defines the widgets used in the top and bottom bars of a custom Qtile desktop
environment. Typography and panel geometry come from `settings.metrics`, while
`widget_defaults` supplies the shared font, size, and padding to widgets that do
not require an intrinsically different size.

Attributes:
    primary_widgets: Widgets shown on the primary screen.
    secondary_widgets: Widgets shown on secondary screens.
    bottom_widgets: Widgets shown on the bottom bar.
    widget_defaults: Shared widget defaults exported to libqtile.
    extension_defaults: Shared extension defaults exported to libqtile.
"""

# -*- coding: utf-8 -*-
# Autor: Daniel Benjamin Perez Morales
# GitHub: https://github.com/D4nitrix13
# Gitlab: https://gitlab.com/D4nitrix13
# Correo electrónico: danielperezdev@proton.me

from os import listdir
from subprocess import CompletedProcess, check_output, run
from typing import Any, Dict, List, Union, cast

from libqtile import qtile, widget  # type: ignore
from libqtile.core.manager import Qtile

from . import metrics
from .path import interface_path
from .theme import colors

# Get the icons at https://www.nerdfonts.com/cheat-sheet (you need a Nerd Font)


def base(fg: str = "text", bg: str = "dark") -> Dict[str, Any]:
    """
    Returns a dictionary with foreground and background colors
    based on the current theme configuration.

    Parameters:
        fg (str): The key for the foreground color in the theme dictionary. Defaults to "text".
        bg (str): The key for the background color in the theme dictionary. Defaults to "dark".

    Returns:
        dict: A dictionary containing 'foreground' and 'background' keys with hex color values.
    """
    return dict(
        foreground=colors.get(fg) or "#0f101a", background=colors.get(bg) or "#0f101a"
    )


def network_interface() -> str:
    """Returns the network interface used by the network widget.

    The configured interface takes precedence. When it is missing or empty, the
    function falls back to the default route and then to the first non-loopback
    interface exposed by the kernel. None of these failures break configuration
    loading.

    Returns:
        str: The detected interface name, or an empty string when detection fails.
    """
    try:
        with open(
            file=interface_path,
            mode="r",
            encoding="utf-8",
        ) as interface_file:
            configured_interface: str = interface_file.read().strip()
        if configured_interface:
            return configured_interface
    except (OSError, UnicodeError):
        pass

    try:
        route: CompletedProcess[str] = run(
            args=["ip", "route", "get", "1.1.1.1"],
            capture_output=True,
            text=True,
            check=False,
        )
        if route.returncode == 0:
            route_tokens: List[str] = route.stdout.split()
            if "dev" in route_tokens:
                interface_index: int = route_tokens.index("dev")
                if interface_index + 1 < len(route_tokens):
                    detected_interface: str = route_tokens[interface_index + 1]
                    if detected_interface:
                        return detected_interface
    except (OSError, UnicodeError):
        pass

    try:
        network_interfaces: List[str] = listdir(path="/sys/class/net")
        for interface in network_interfaces:
            if interface != "lo":
                return interface
    except OSError:
        pass

    return ""


def separator() -> widget.Sep:
    """
    Creates a separator widget with transparent spacing.

    Returns:
        widget.Sep: A separator with no visible line, used to add padding between widgets.
    """
    return widget.Sep(**base(), linewidth=0, padding=5)


def icon(
    fg: str = "text",
    bg: str = "dark",
    fontsize: int = metrics.ICON_FONTSIZE,
    text: str = "?",
) -> widget.TextBox:
    """Creates a styled TextBox widget used as an icon with Nerd Font glyphs.

    Args:
        fg: The foreground color key from the theme.
        bg: The background color key from the theme.
        fontsize: Font size of the icon.
        text: The text or glyph to display.

    Returns:
        widget.TextBox: A TextBox configured as an icon with the specified styles.
    """
    return widget.TextBox(**base(fg, bg), fontsize=fontsize, text=text, padding=3)


def powerline(fg: str = "light", bg: str = "dark") -> widget.TextBox:
    """
    Creates a triangle-shaped separator using a Nerd Font icon, styled with the given theme colors.

    This widget simulates a powerline transition effect between sections of the bar.

    Parameters:
        fg (str): Foreground color key from the theme. Defaults to "light".
        bg (str): Background color key from the theme. Defaults to "dark".

    Returns:
        widget.TextBox: A TextBox widget displaying a triangular glyph with styling.
    """
    return widget.TextBox(
        **base(fg, bg),
        text="",  # Icon: nf-oct-triangle_left
        fontsize=metrics.POWERLINE_FONTSIZE,
        # El padding por defecto de TextBox es fontsize // 2. Con 56 pixels
        # serian 28 a cada lado y el separador mediria 111 pixels de los que
        # solo 23 son el triangulo: el resto es espacio vacio. A cero, el
        # separador se ajusta al glifo.
        padding=0,
    )


def workspaces() -> List[Union[widget.Sep, widget.GroupBox]]:
    """
    Creates a GroupBox widget to display workspaces, along with a separator.

    The GroupBox shows active, inactive, urgent, and focused workspace states
    using colors from the theme. It disables dragging and uses block highlights.

    Returns:
        list: A list containing a separator and a styled GroupBox widget.
    """
    return [
        separator(),
        widget.GroupBox(
            **base(fg="light"),
            fontsize=metrics.GROUP_FONTSIZE,
            margin_y=metrics.GROUP_MARGIN_Y,
            margin_x=0,
            padding_y=metrics.GROUP_PADDING_Y,
            padding_x=5,
            borderwidth=1,
            active=colors.get("active") or "#f1ffff",
            inactive=colors.get("inactive") or "#4c566a",
            rounded=False,
            highlight_method="block",
            urgent_alert_method="block",
            urgent_border=colors.get("urgent") or "#F07178",
            this_current_screen_border=colors.get("focus") or "#a151d3",
            this_screen_border=colors.get("grey") or "#353c4a",
            other_current_screen_border=colors.get("dark") or "#0f101a",
            other_screen_border=colors.get("dark") or "#0f101a",
            disable_drag=True,
        ),
    ]


primary_widgets: List[Any] = [
    *workspaces(),
    widget.Spacer(),
    # ------------ Displays the number of available system package updates ------------
    powerline(fg="color8", bg="dark"),
    icon(bg="color8", text=" "),  # Icon: nf-fa-download
    widget.CheckUpdates(
        fmt="{}",
        background=colors.get("color8") or "#ffd47e",
        colour_have_updates=colors.get("text") or "#0f101a",
        colour_no_updates=colors.get("text") or "#0f101a",
        no_update_string="0",
        display_format="{updates}",
        update_interval=1,
        custom_command="checkupdates",
        distro="Arch_checkupdates",
    ),
    # ------------ Displays and controls the system audio volume using PulseAudio ------------
    powerline(fg="color7", bg="color8"),
    icon(bg="color7", text=" "),  # Icon: nf-fa-volume_high
    widget.PulseVolume(
        **base(bg="color7"),
        channel="Master",
        mute_format="Muted",
        mouse_callbacks={"Button1": lambda: cast(Qtile, qtile).spawn("pavucontrol")},
        fmt="{}",
    ),
    # ------------ Shows current RAM usage, including used and total memory ------------
    powerline(fg="color6", bg="color7"),
    icon(bg="color6", text="󱐋"),  # Icon: nf-md-lightning_bolt
    widget.Memory(
        **base(bg="color6"),
        format="{MemUsed: .2f}{mm} /{MemTotal: .2f}{mm}",
        mouse_callbacks={
            "Button1": lambda: cast(Qtile, qtile).spawn("/bin/alacritty -e htop")
        },
        fmt="{}",
        update_interval=1,
    ),
    # ------------ Displays the current CPU usage as a percentage ------------
    powerline(fg="color5", bg="color6"),
    icon(bg="color5", text=" "),  # Icon: nf-oct-cpu
    widget.CPU(
        **base(bg="color5"),
        fmt="{}",
        update_interval=1,
    ),
    # ------------ Shows current network upload and download speeds ------------
    powerline(fg="color4", bg="color5"),
    icon(bg="color4", text=" "),  # Icon: nf-fa-feed
    widget.Net(
        **base(bg="color4"),
        fmt="{}",
        interface=network_interface(),
        update_interval=1,
    ),
    # ------------ Displays an icon representing the current window layout ------------
    powerline(fg="color3", bg="color4"),
    widget.CurrentLayout(
        **base(bg="color3"),
        scale=0.65,
        mode="icon",
    ),
    # ------------ Shows the name of the currently active layout ------------
    widget.CurrentLayout(
        **base(bg="color3"),
        padding=5,
        fmt="{}",
    ),
    # ------------ # Provides a system tray for app icons (e.g. volume, network) ------------
    powerline(fg="dark", bg="color3"),
    widget.Systray(
        fmt="{}",
        background=colors.get("dark") or "#0f101a",
        padding=5,
    ),
]

secondary_widgets: List[Any] = [
    # ------------ Workspace separator ------------
    *workspaces(),
    # ------------ Spacer to fill the space between widgets ------------
    separator(),
    # ------------ Displays an icon representing the current window layout ------------
    powerline(fg="color1", bg="dark"),
    widget.CurrentLayout(
        **base(bg="color1"),
        scale=0.65,
        mode="icon",
    ),
    # ------------ Shows the name of the currently active layout ------------
    widget.CurrentLayout(
        **base(bg="color1"),
        padding=5,
        fmt="{}",
    ),
    # ------------ Shows the current date and time in a customizable format ------------
    powerline(fg="color2", bg="color1"),
    widget.Clock(
        **base(bg="color2"),
        format="%A, %d of %B %Y - %I:%M:%S %p ",
    ),
    powerline(fg="dark", bg="color2"),
]

bottom_widgets: List[Any] = [
    # ------------ Displays the title of the currently focused window ------------
    widget.WindowName(
        **base(fg="focus"),
        padding=5,
        max_chars=195,
    ),
    # ------------ Displays custom text output by polling a shell command at intervals ------------
    powerline(fg="color2", bg="dark"),
    widget.GenPollText(
        **base(bg="color2"),
        func=lambda: check_output(
            args='printf "Arch Linux $(uname -r)"', shell=True, text=True
        ),
        padding=5,
        fmt="❤ {}",
        update_interval=86400,
    ),
    # ------------ Shows the current date and time in a customizable format ------------
    powerline(fg="color1", bg="color2"),
    icon(bg="color1", text="󰃰 "),  # Icon: nf-md-calendar_clock
    widget.Clock(
        **base(bg="color1"),
        format="%A, %d of %B %Y - %H:%M:%S %p ",
    ),
]


widget_defaults: Dict[str, Union[str, int]] = {
    "font": metrics.BAR_FONT,
    "fontsize": metrics.BAR_FONTSIZE,
    "padding": metrics.WIDGET_PADDING,
}
extension_defaults: Dict[str, Union[str, int]] = widget_defaults.copy()
