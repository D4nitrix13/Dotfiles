"""Keybinding configuration for the Qtile window manager.

Declares the global modifier key, a typed table of keybindings and the flat
list of ``Key`` objects that Qtile consumes.

The bindings are organized into three categories:

1. **Window configuration**: navigation, resizing, floating, shuffling,
   layout switching and window management.
2. **Application configuration**: launchers for the browser, editor,
   terminal, file manager and other daily tools.
3. **Hardware configuration**: multimedia keys for volume and brightness.

Every row of the table is a ``(modifiers, key, command)`` tuple where
``modifiers`` is a list of modifier names, ``key`` is the key name and
``command`` is a ``LazyCall`` that is only evaluated when the key is pressed.

Attributes:
    mod (str): The global modifier key, ``"mod4"`` in this configuration.
    KeyBinding (type): Alias describing a single row of the binding table.
    bindings (List[KeyBinding]): The typed keybinding table.
    keys (List[Key]): The flat list of ``Key`` objects consumed by Qtile.
"""

# Autor: Daniel Benjamin Perez Morales
# GitHub: https://github.com/D4nitrix13
# Gitlab: https://gitlab.com/D4nitrix13
# Correo electrónico: danielperezdev@proton.me

from typing import List, Tuple

from libqtile.config import Key
from libqtile.lazy import LazyCall, lazy

from .path import home

mod: str = "mod4"

KeyBinding = Tuple[List[str], str, LazyCall]

bindings: List[KeyBinding] = [
    # ------------ Window Configs ------------
    # Switch between windows in current stack pane
    ([mod], "j", lazy.layout.down()),
    ([mod], "k", lazy.layout.up()),
    ([mod], "h", lazy.layout.left()),
    ([mod], "l", lazy.layout.right()),
    # Change window sizes (MonadTall)
    ([mod, "shift"], "l", lazy.layout.grow()),
    ([mod, "shift"], "h", lazy.layout.shrink()),
    # Toggle floating
    ([mod], "f", lazy.window.toggle_floating()),
    # Move windows up or down in current stack
    ([mod, "shift"], "j", lazy.layout.shuffle_down()),
    ([mod, "shift"], "k", lazy.layout.shuffle_up()),

    # Lock the screen using i3lock-color
    ([mod, "shift"], "x", lazy.spawn("%s/Scripts/lock" % home)),
    # Toggle between different layouts as defined below
    ([mod], "Tab", lazy.next_layout()),
    # Kill window
    ([mod], "w", lazy.window.kill()),
    # Restart Qtile
    ([mod, "control"], "r", lazy.restart()),
    ([mod, "control"], "q", lazy.shutdown()),
    ([mod], "r", lazy.spawncmd()),
    # Switch window focus to other pane(s) of stack
    ([mod], "m", lazy.layout.next()),
    # Swap panes of split stack
    ([mod, "shift"], "space", lazy.layout.rotate()),
    # ------------ App Configs ------------
    # Menu / application launcher
    ([mod], "space", lazy.spawn("/bin/rofi -show drun")),
    # Window Nav
    ([mod, "shift"], "m", lazy.spawn("/bin/rofi -show window")),
    # Browser
    ([mod], "b", lazy.spawn("/bin/firefox")),
    # Vscode
    ([mod], "v", lazy.spawn("/bin/code")),
    # Burp Suite
    ([mod, "shift"], "b", lazy.spawn("/bin/burpsuite")),
    # Obsidian
    ([mod, "shift"], "o", lazy.spawn("/bin/obsidian")),
    # Obs
    ([mod], "o", lazy.spawn("/bin/obs")),
    # Caido
    ([mod], "c", lazy.spawn("/bin/caido")),
    # Discord
    ([mod], "d", lazy.spawn("/bin/discord")),
    # Gimp
    ([mod], "g", lazy.spawn("/bin/gimp")),
    # Nvim
    ([mod], "n", lazy.spawn("/bin/alacritty -e /bin/nvim")),
    # File Explorer
    ([mod, "shift"], "f", lazy.spawn("/bin/nautilus")),
    # Terminal
    ([mod], "Return", lazy.spawn("/bin/alacritty")),

    # Redshift
    # ([mod], "r", lazy.spawn("redshift -O 2400")),
    # ([mod, "shift"], "r", lazy.spawn("/bin/redshift -x")),

    # Screenshot With Scrot
    ([mod], "s", lazy.spawn(f"{home}/Scripts/screenshots-x11")),

        # Screenshot with interactive region selection
        ([mod, "shift"], "s", lazy.spawn(f"{home}/Scripts/screenshot-region")),

    # ([mod, "shift"], "s", lazy.spawn("/bin/scrot -s")),
    # ------------ Hardware Configs ------------
    # Volume
    (
        [],
        "XF86AudioLowerVolume",
        lazy.spawn("/bin/pactl set-sink-volume @DEFAULT_SINK@ -5%"),
    ),
    (
        [],
        "XF86AudioRaiseVolume",
        lazy.spawn("/bin/pactl set-sink-volume @DEFAULT_SINK@ +5%"),
    ),
    (
        [],
        "XF86AudioMute",
        lazy.spawn("/bin/pactl set-sink-mute @DEFAULT_SINK@ toggle"),
    ),
    # Brightness
    ([], "XF86MonBrightnessUp", lazy.spawn("/bin/brightnessctl set +10%")),
    ([], "XF86MonBrightnessDown", lazy.spawn("/bin/brightnessctl set 10%-")),
]

keys: List[Key] = [
    Key(
        key[0],  # Modifiers
        key[1],  # Key
        *key[2:],  # Commands
    )
    for key in bindings
]
