"""Mouse bindings for the Qtile window manager.

Configures the drag and click actions that let the user move, resize and
raise floating windows with the mouse.

Mouse actions:

- Dragging with ``Button1`` moves the window to a floating position.
- Dragging with ``Button3`` resizes the floating window.
- Clicking with ``Button2`` brings the window to the front.

Attributes:
    mouse (List[Union[Drag, Click]]): The mouse actions bound to buttons
        and modifiers.
"""

# Autor: Daniel Benjamin Perez Morales
# GitHub: https://github.com/D4nitrix13
# Gitlab: https://gitlab.com/D4nitrix13
# Correo electrónico: danielperezdev@proton.me

from typing import List, Union

from libqtile.config import Click, Drag
from libqtile.lazy import lazy

from .keys import mod

mouse: List[Union[Drag, Click]] = [
    Drag(
        [mod],  # Modifiers
        "Button1",  # Button
        lazy.window.set_position_floating(),  # Commands
        start=lazy.window.get_position(),  # Start
    ),
    Drag(
        [mod],  # Modifiers
        "Button3",  # Button
        lazy.window.set_size_floating(),  # Commands
        start=lazy.window.get_size(),  # Start
    ),
    Click(
        [mod],  # Modifiers
        "Button2",  # Button
        lazy.window.bring_to_front(),  # Commands
    ),
]
