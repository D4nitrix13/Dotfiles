hl.unbind("SUPER + S")
hl.unbind("SUPER + SHIFT + S")
hl.unbind("SUPER + ALT + S")
hl.unbind("SUPER + CTRL + R")
hl.unbind("SUPER + SHIFT + CTRL + R")

o.bind("SUPER + CTRL + Q", "Logout", "/usr/bin/uwsm stop")
o.bind("SUPER + ALT + R", "Set reminder", "omarchy-reminder set")
o.bind("SUPER + SHIFT + ALT + R", "Clear reminders", "omarchy-reminder clear")
o.bind(
	"SUPER + CTRL + R",
	"Reload Hyprland and Waybar",
	"/usr/bin/hyprctl reload; /usr/bin/pkill waybar || true; /usr/bin/waybar >/dev/null 2>&1 & /usr/bin/waybar -c /home/d4nitrix13/.config/waybar/config-bottom.jsonc >/dev/null 2>&1 &"
)
o.bind("SUPER + S", "Full screenshot to disk and clipboard", "/home/d4nitrix13/Scripts/screenshot-full-clipboard")
o.bind(
	"SUPER + GRAVE",
	"Toggle scratchpad",
	hl.dsp.workspace.toggle_special("scratchpad")
)
o.bind(
	"SUPER + SHIFT + ALT + S",
	"Move window to scratchpad",
	hl.dsp.window.move({ workspace = "special:scratchpad", follow = false })
)
o.bind("SUPER + B", "Firefox", "/usr/bin/firefox")
o.bind("SUPER + RETURN", "Terminal", { omarchy = "terminal" })
o.bind("SUPER + ALT + RETURN", "Tmux", { omarchy = "terminal-tmux" })
o.bind("SUPER + SHIFT + RETURN", "Browser", { omarchy = "browser" })
o.bind("SUPER + SHIFT + F", "File manager", { omarchy = "nautilus" })
o.bind("SUPER + ALT + SHIFT + F", "File manager (cwd)", { omarchy = "nautilus-cwd" })
o.bind("SUPER + SHIFT + B", "Browser", { omarchy = "browser" })
o.bind("SUPER + SHIFT + ALT + B", "Browser (private)", { omarchy = "browser --private" })
o.bind("SUPER + SHIFT + M", "Music", { omarchy = "or-focus spotify" })
o.bind("SUPER + SHIFT + ALT + M", "Music TUI", { tui = "cliamp", focus = true })
o.bind("SUPER + SHIFT + N", "Editor", { omarchy = "editor" })
o.bind("SUPER + SHIFT + D", "Docker", { tui = "lazydocker" })
o.bind("SUPER + SHIFT + O", "Obsidian", { launch = "obsidian", focus = "^obsidian$" })
o.bind("SUPER + SHIFT + A", "MiniMax", { webapp = "https://agent.minimax.io/" })
o.bind("SUPER + SHIFT + Y", "YouTube", { webapp = "https://youtube.com/" })
o.bind("SUPER + SHIFT + ALT + G", "WhatsApp", { webapp = "https://web.whatsapp.com/", focus = true })
o.bind("SUPER + SHIFT + S", "Region with editor", "/home/d4nitrix13/Scripts/screenshot-region-editor")

hl.bind("SUPER + 6", hl.dsp.focus({ workspace = "6" }))
hl.bind("SUPER + 7", hl.dsp.focus({ workspace = "7" }))
hl.bind("SUPER + 8", hl.dsp.focus({ workspace = "8" }))
hl.bind("SUPER + 9", hl.dsp.focus({ workspace = "9" }))
hl.bind("SUPER + SHIFT + 6", hl.dsp.window.move({ workspace = "6", follow = true }))
hl.bind("SUPER + SHIFT + 7", hl.dsp.window.move({ workspace = "7", follow = true }))
hl.bind("SUPER + SHIFT + 8", hl.dsp.window.move({ workspace = "8", follow = true }))
hl.bind("SUPER + SHIFT + 9", hl.dsp.window.move({ workspace = "9", follow = true }))

-- Remove Omarchy default scratchpad bindings.
-- Remove Omarchy default reminder bindings.
-- Application bindings.
-- SUPER + CTRL + Q = Windows/Super + Ctrl + Q | Log out from the current session.
-- Keep reminders available with new shortcuts.
-- SUPER + CTRL + R = Windows/Super + Ctrl + R | Reload Hyprland and Waybar.
-- SUPER + S = Windows/Super + S | Full screenshot saved to ~/Images/Screenshots and clipboard.
-- SUPER + GRAVE = Windows/Super + ` | Toggles scratchpad visibility.
-- SUPER + SHIFT + ALT + S = Windows/Super + Shift + Alt + S | Moves focused window to scratchpad.
-- SUPER + B = Windows/Super + B | Launches Firefox.
-- SUPER = Windows/Super key | RETURN = Enter key | Launches the main terminal.
-- SUPER + ALT + RETURN = Windows/Super + Alt + Enter | Launches terminal with Tmux.
-- SUPER + SHIFT + RETURN = Windows/Super + Shift + Enter | Launches the default browser.
-- SUPER + SHIFT + F = Windows/Super + Shift + F | Launches the file manager.
-- SUPER + ALT + SHIFT + F = Windows/Super + Alt + Shift + F | Opens file manager in current working directory.
-- SUPER + SHIFT + B = Windows/Super + Shift + B | Launches the default browser.
-- SUPER + SHIFT + ALT + B = Windows/Super + Shift + Alt + B | Launches browser in private mode.
-- SUPER + SHIFT + M = Windows/Super + Shift + M | Opens or focuses Spotify.
-- SUPER + SHIFT + ALT + M = Windows/Super + Shift + Alt + M | Launches Music TUI / cliamp in terminal.
-- SUPER + SHIFT + N = Windows/Super + Shift + N | Launches the configured editor.
-- SUPER + SHIFT + D = Windows/Super + Shift + D | Launches LazyDocker TUI.
-- SUPER + SHIFT + G = Windows/Super + Shift + G | Launches or focuses Signal Desktop.
-- o.bind("SUPER + SHIFT + G", "Signal", { launch = "signal-desktop", focus = "^signal$" })
-- SUPER + SHIFT + O = Windows/Super + Shift + O | Launches or focuses Obsidian.
-- SUPER + SHIFT + W = Windows/Super + Shift + W | Launches Typora with Wayland IME enabled.
-- o.bind("SUPER + SHIFT + W", "Typora", { launch = "typora --enable-wayland-ime" })
-- SUPER + SHIFT + SLASH = Windows/Super + Shift + / | Launches 1Password.
-- o.bind("SUPER + SHIFT + SLASH", "Passwords", { launch = "1password" })
-- Web app bindings.
-- SUPER + SHIFT + A = Windows/Super + Shift + A | Opens MiniMax as a web app.
-- SUPER + SHIFT + ALT + A = Windows/Super + Shift + Alt + A | Opens Grok as a web app.
-- o.bind("SUPER + SHIFT + ALT + A", "Grok", { webapp = "https://grok.com" })
-- SUPER + SHIFT + C = Windows/Super + Shift + C | Opens HEY Calendar.
-- o.bind("SUPER + SHIFT + C", "Calendar", { webapp = "https://app.hey.com/calendar/weeks/" })
-- SUPER + SHIFT + E = Windows/Super + Shift + E | Opens HEY Email.
-- o.bind("SUPER + SHIFT + E", "Email", { webapp = "https://app.hey.com" })
-- SUPER + SHIFT + Y = Windows/Super + Shift + Y | Opens YouTube.
-- SUPER + SHIFT + ALT + G = Windows/Super + Shift + Alt + G | Opens or focuses WhatsApp Web.
-- SUPER + SHIFT + CTRL + G = Windows/Super + Shift + Ctrl + G | Opens or focuses Google Messages.
-- o.bind(
-- 	"SUPER + SHIFT + CTRL + G",
-- 	"Google Messages",
-- 	{ webapp = "https://messages.google.com/web/conversations", focus = true }
-- )
-- SUPER + SHIFT + P = Windows/Super + Shift + P | Opens or focuses Google Photos.
-- o.bind("SUPER + SHIFT + P", "Google Photos", { webapp = "https://photos.google.com/", focus = true })
-- SUPER + SHIFT + K = Windows/Super + Shift + K | Opens or focuses Google Maps.
-- Changed from SUPER + SHIFT + S so Flameshot can use S for screenshots.
-- o.bind("SUPER + SHIFT + K", "Google Maps", { webapp = "https://maps.google.com/", focus = true })
-- SUPER + SHIFT + X = Windows/Super + Shift + X | Opens X / Twitter.
-- o.bind("SUPER + SHIFT + X", "X", { webapp = "https://x.com/" })
-- SUPER + SHIFT + ALT + X = Windows/Super + Shift + Alt + X | Opens X post composer.
-- o.bind("SUPER + SHIFT + ALT + X", "X Post", { webapp = "https://x.com/compose/post" })
-- Screenshot bindings (Wayland-native: grim + slurp + swappy).
-- SUPER + SHIFT + S = Windows/Super + Shift + S | Region screenshot opened in swappy editor.
-- Extra workspaces 6-9.
-- SUPER + 6 = Windows/Super + 6 | Focuses workspace 6.
-- SUPER + 7 = Windows/Super + 7 | Focuses workspace 7.
-- SUPER + 8 = Windows/Super + 8 | Focuses workspace 8.
-- SUPER + 9 = Windows/Super + 9 | Focuses workspace 9.
-- Move focused window to workspaces 6-9.
-- SUPER + SHIFT + 6 = Windows/Super + Shift + 6 | Moves focused window to workspace 6 and follows it.
-- SUPER + SHIFT + 7 = Windows/Super + Shift + 7 | Moves focused window to workspace 7 and follows it.
-- SUPER + SHIFT + 8 = Windows/Super + Shift + 8 | Moves focused window to workspace 8 and follows it.
-- SUPER + SHIFT + 9 = Windows/Super + Shift + 9 | Moves focused window to workspace 9 and follows it.
-- Add extra bindings below.
-- Example:
-- SUPER + SHIFT + R = Windows/Super + Shift + R | Opens SSH connection in Alacritty.
-- o.bind("SUPER + SHIFT + R", "SSH", "alacritty -e ssh your-server")
-- Overwrite existing bindings with hl.unbind() first if needed.
-- Example:
-- SUPER + SPACE = Windows/Super + Space | Opens Omarchy menu.
-- hl.unbind("SUPER + SPACE")
-- o.bind("SUPER + SPACE", "Omarchy menu", "omarchy-menu")
-- Logitech MX Keys examples.
-- SUPER + SHIFT + S = Default Omarchy screenshot replaced by grim + slurp + swappy above.
-- SUPER + H = Windows/Super + H | Toggles voice typing / recording with voxtype.
-- o.bind("SUPER + H", nil, "voxtype record toggle")
-- SUPER + PERIOD = Windows/Super + . | Opens Walker symbols menu.
-- o.bind("SUPER + PERIOD", nil, { omarchy = "walker -m symbols" })
