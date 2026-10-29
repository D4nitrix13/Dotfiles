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
# Twenty-eight pixels makes the regular bar text fill the panel: the Pango
# layout is 33 pixels tall, which leaves 3 pixels of slack in a 36-pixel bar.
# Sixteen pixels was sized for the 30-pixel bar this panel used to have.
BAR_FONTSIZE: int = 28
# Thirty-six pixels fits the workspace group: 25 + 2*2 + 2*1 + 2*2 = 35 pixels.
BAR_SIZE: int = 36
# Twenty-five pixels keeps the workspace labels readable at a glance.
GROUP_FONTSIZE: int = 25
# Two pixels adds vertical breathing room while preserving the bar height budget.
GROUP_PADDING_Y: int = 2
# Two pixels centers the group and leaves space for its one-pixel border.
GROUP_MARGIN_Y: int = 2
# Twenty-nine pixels balances the Nerd Font icons against the 28-pixel text.
# Those glyphs carry more internal whitespace, so they need a point more.
ICON_FONTSIZE: int = 29
# Thirty pixels makes the separator triangle fill the panel height: the
# powerline glyph (U+E0B2) inks at 118 percent of its font size, so 30 pixels
# yields a 36-pixel-tall triangle. The previous octicon triangle (U+EB6F)
# only inked 53 percent and carried 16-pixel side bearings that rendered as
# visible gaps between the triangle and its segment.
POWERLINE_FONTSIZE: int = 30
# One pixel adds minimal spacing without increasing the effective text height.
WIDGET_PADDING: int = 1
