"""Workspace groups and workspace keybindings for the Qtile window manager.

Defines the nine workspaces of the configuration, each one identified by a
single Nerd Font glyph, and the keybindings that drive the workspace switcher:

1. Switch to a workspace (``Mod`` + ``[1-9]``).
2. Send the focused window to a workspace (``Mod`` + ``Shift`` + ``[1-9]``).

The glyphs are rendered by the ``GroupBox`` widget of the panel, which already
applies its own horizontal padding, so the group names only carry the icon
itself.

Dependencies:

- A Nerd Font must be installed for the glyphs to display correctly.
- :mod:`settings.keys` must provide ``keys`` (``List[Key]``) and ``mod``.

Attributes:
    groups (List[Group]): The configured workspaces, in display order.
"""

# Autor: Daniel Benjamin Perez Morales
# GitHub: https://github.com/D4nitrix13
# Gitlab: https://gitlab.com/D4nitrix13
# Correo electrónico: danielperezdev@proton.me

from typing import List

from libqtile.config import Group, Key
from libqtile.lazy import lazy

from .keys import keys, mod

# Get the icons at https://www.nerdfonts.com/cheat-sheet (you need a Nerd Font)
# Icons:

# 󰈹 -> nf-md-firefox
#  -> nf-dev-vscode
#  -> nf-dev-terminal
# 󱍙 -> nf-md-folder_music
# 󰈙 -> nf-md-file_document
#  -> nf-fa-image
#  -> nf-dev-docker
#  -> nf-seti-config
# 󰌨 -> nf-md-layers

groups: List[Group] = [
    Group(name=g)
    for g in ["󰈹", "", "", "󱍙", "󰈙", "", "", "", "󰌨"]
]


def workspace_keys() -> List[Key]:
    """Builds the keybindings that drive the workspace switcher.

    Every workspace receives two bindings: one that focuses the workspace and
    one that moves the focused window to it.

    Returns:
        List[Key]: The workspace keybindings, in workspace order.
    """
    bindings: List[Key] = []

    for index, group in enumerate(iterable=groups, start=1):
        current_key: str = str(index)
        bindings.extend(
            [
                # Switch to workspace N
                Key(
                    [mod],  # Modifiers
                    current_key,  # Key
                    lazy.group[group.name].toscreen(),  # Commands
                ),
                # Send window to workspace N
                Key(
                    [mod, "shift"],  # Modifiers
                    current_key,  # Key
                    lazy.window.togroup(group.name),  # Commands
                ),
            ]
        )

    return bindings


# libqtile consumes a single flat list of bindings, so the workspace bindings
# are appended to the shared one.
keys.extend(workspace_keys())
