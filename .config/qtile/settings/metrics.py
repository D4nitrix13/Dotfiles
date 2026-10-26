"""Single source of truth for Qtile panel typography and geometry.

The constants keep the bar font, widget defaults, and GroupBox geometry in one
place so panel changes cannot drift between modules.

Attributes:
    BAR_FONT: Pango font description used by the default panel text.
    BAR_FONTSIZE: Font size used by widgets that inherit the panel defaults.
    BAR_SIZE: Height of the panel in pixels.
    GROUP_FONTSIZE: Font size used by the workspace GroupBox.
    GROUP_PADDING_Y: Vertical padding inside the workspace GroupBox.
    GROUP_MARGIN_Y: Vertical margin around the workspace GroupBox.
    ICON_FONTSIZE: Font size used by standalone Nerd Font icons.
    POWERLINE_FONTSIZE: Font size used by powerline separator triangles.
    WIDGET_PADDING: Padding inherited by widgets using the panel defaults.
"""

# -*- coding: utf-8 -*-
# Autor: Daniel Benjamin Perez Morales
# GitHub: https://github.com/D4nitrix13
# Gitlab: https://gitlab.com/D4nitrix13
# Correo electrónico: danielperezdev@proton.me

# The panel uses Nerd Font glyphs, and this installed family provides Bold Italic.
BAR_FONT: str = "Ubuntu Nerd Font Bold Italic"
# Sixteen pixels keeps regular bar text legible without crowding adjacent widgets.
BAR_FONTSIZE: int = 16
# Thirty-six pixels fits the workspace group: 25 + 2*2 + 2*1 + 2*2 = 35 pixels.
BAR_SIZE: int = 36
# Twenty-five pixels keeps the workspace labels readable at a glance.
GROUP_FONTSIZE: int = 25
# Two pixels adds vertical breathing room while preserving the bar height budget.
GROUP_PADDING_Y: int = 2
# Two pixels centers the group and leaves space for its one-pixel border.
GROUP_MARGIN_Y: int = 2
# Seventeen pixels balances Nerd Font icons against 16-pixel regular text.
ICON_FONTSIZE: int = 17
# Matching the bar height lets the powerline triangle fill the complete panel.
POWERLINE_FONTSIZE: int = BAR_SIZE
# One pixel adds minimal spacing without increasing the effective text height.
WIDGET_PADDING: int = 1
