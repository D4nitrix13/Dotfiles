"""
This script defines keybindings for various window management, application launching,
and hardware control in the Qtile window manager.

Keybindings are organized into different categories:
1. **Window Configurations**: Keybindings for switching windows, resizing windows, toggling floating mode, and changing layouts.
2. **Application Configurations**: Keybindings for launching common applications like browsers, file explorers, terminals, and menus.
3. **Hardware Configurations**: Keybindings for controlling volume and brightness using multimedia keys.

Each keybinding is represented by a list containing:
- Modifiers: A list of modifier keys (e.g., "mod4", "shift").
- Key: The key to be pressed (e.g., "j", "Tab", "Return").
- Commands: A list of actions to be executed when the keybinding is triggered.

This script uses `libqtile.config.Key` to bind keys to actions via `lazy` calls, which are delayed executions until the keys are pressed.

Parameters:
- mod (str): The modifier key (e.g., "mod4" or "mod1").
- key (Tuple[List[str], str, Any]): A tuple containing a list of modifier keys, the key to press, and the corresponding action(s).
- keys (List[Key]): A list of Key objects that define all the keybindings.

This configuration is intended to be used with the Qtile window manager to manage windows, applications, and system hardware.
"""

# Autor: Daniel Benjamin Perez Morales
# GitHub: https://github.com/D4nitrix13
# Gitlab: https://gitlab.com/D4nitrix13
# Correo electrónico: danielperezdev@proton.me

from typing import Any, List, Tuple

from libqtile.config import Key  # type: ignore
from libqtile.lazy import lazy  # type: ignore

from settings.path import home

mod: str = "mod4"
key: Tuple[List[str], "str", Any]

keys: List[Key] = [
    Key(
        key[0],  # Modifiers
        key[1],  # Key
        *key[2 : len(key) : 1],  # Commands
    )
    for key in [
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
        ([mod, "shift"], "f", lazy.spawn("/bin/thunar")),
        # Terminal
        ([mod], "Return", lazy.spawn("/bin/alacritty")),
        
        # Redshift
        # ([mod], "r", lazy.spawn("redshift -O 2400")),
        # ([mod, "shift"], "r", lazy.spawn("/bin/redshift -x")),

        # Screenshot With Scrot
        ([mod], "s", lazy.spawn(f"{home}/Scripts/screenshots-x11")),

        # Screenshot With Flameshot
        ([mod, "shift"], "s", lazy.spawn("/bin/flameshot gui")),

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
]
