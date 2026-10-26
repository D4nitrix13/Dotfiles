"""
Qtile Configuration File

This file contains the main configuration for the Qtile window manager.
It sets up the startup script, window settings, key bindings, layouts,
mouse behavior, and other aspects of the Qtile environment.

Modules:
- groups: Defines the workspaces for Qtile.
- keys: Sets up key bindings and modifier keys.
- layouts: Configures layouts and floating windows.
- mouse: Configures mouse behavior.
- path: Contains the path for specific scripts.
- screens: Defines screen setups and appearance.
- widgets: Sets up Qtile widgets and their defaults.

Functions:
- autostart: Runs the autostart.sh script once after Qtile starts.
"""


# Qtile Config File
# http://www.qtile.org/

# Autor: Daniel Benjamin Perez Morales
# GitHub: https://github.com/D4nitrix13
# Gitlab: https://gitlab.com/D4nitrix13
# Correo electrónico: danielperezdev@proton.me

from os import path
from subprocess import call
from typing import List

from libqtile import hook
from libqtile.config import Rule

from settings.groups import groups  # noqa: F401
from settings.keys import keys, mod  # noqa: F401
from settings.layouts import floating_layout, layouts  # noqa: F401
from settings.mouse import mouse  # noqa: F401
from settings.path import qtile_path
from settings.screens import screens  # noqa: F401
from settings.widgets import extension_defaults, widget_defaults  # noqa: F401


@hook.subscribe.startup_once
def autostart() -> None:
    """
    Runs the autostart.sh script once after Qtile starts.
    """
    call(args=[path.join(qtile_path, "autostart.sh")])
    return None


@hook.subscribe.startup
def script_on_reboot() -> None:
    """
    Runs the autostart.sh script every time Qtile restarts.
    """
    call(args=[path.join(qtile_path, "restart.sh")])
    return None


main: None = None
dgroups_key_binder: None = None
dgroups_app_rules: List[Rule] = []
follow_mouse_focus: bool = True
bring_front_click: bool = False
cursor_warp: bool = False
auto_fullscreen: bool = True
focus_on_window_activation: str = "smart"

# XXX: Gasp! We're lying here. In fact, nobody really uses or cares about this
# string besides java UI toolkits; you can see several discussions on the
# mailing lists, GitHub issues, and other WM documentation that suggest setting
# this string if your java app doesn't work correctly. We may as well just lie
# and say that we're a working one by default.
#
# We choose LG3D to maximize irony: it is a 3D non-reparenting WM written in
# java that happens to be on java's whitelist.
wmname = "LG3D"
