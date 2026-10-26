"""Theme management for Qtile.

Loads the active color palette from the selected JSON theme file and exposes it
through the module-level `colors` mapping.

Attributes:
    colors: Active color definitions keyed by semantic theme names.
"""

# -*- coding: utf-8 -*-
# Autor: Daniel Benjamin Perez Morales
# GitHub: https://github.com/D4nitrix13
# Gitlab: https://gitlab.com/D4nitrix13
# Correo electrónico: danielperezdev@proton.me

# Theming for Qtile

from io import TextIOWrapper
from json import dump, load
from os import path
from typing import Any

from .path import qtile_path


def load_theme() -> Any:
    """
    Loads the current Qtile theme configuration from a JSON file.

    This function checks for a configuration file (`config.json`) in the user's Qtile path.
    If it exists, it reads the selected theme name from it. If not, it creates the file
    and sets the default theme to "material-ocean".

    It then attempts to load the corresponding theme JSON file from the `themes/` directory.
    Raises an exception if the theme file does not exist.

    Returns:
        dict: A dictionary containing the theme's color definitions.

    Raises:
        Exception: If the specified theme file does not exist.
    """
    theme: str = "material-ocean"
    config: str = path.join(qtile_path, "config.json")
    f: TextIOWrapper

    if path.isfile(path=config):
        with open(file=config) as f:
            theme = load(fp=f).get("theme") or "material-ocean"

    else:
        with open(file=config, mode="w") as f:
            dump(obj=dict(theme="material-ocean"), fp=f, indent=4)

    theme_file: str = path.join(qtile_path, "themes", f"{theme}.json")
    if not path.isfile(path=theme_file):
        raise Exception(f'"{theme_file}" does not exist')

    with open(file=path.join(theme_file)) as f:
        return load(fp=f)


colors: Any = load_theme()
