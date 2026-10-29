# firefox-square-ui

Brings back square tabs, a square URL bar and square menus in Firefox's new rounded "Nova" design.

A small Python script adds the needed `userChrome.css` rules to every Firefox profile on your computer. It runs on Windows, macOS and Linux and needs no cloud sync or extra tools.

**Tested with Firefox 159.0 on Windows and macOS.** The Nova design first shipped in Firefox 157.

| OS | Status |
| --- | --- |
| Windows | Tested, works |
| macOS | Tested, works |
| Linux | Script tested on Ubuntu 26.04 (profile detection incl. Snap and Flatpak, apply, update, remove); not yet checked with a real Firefox window |

## What gets squared

- Tabs
- URL bar, search bar and the suggestion list
- Toolbar buttons (back, forward, reload, home, …)
- Hamburger menu and other panels
- Bookmark folders and context menus
- Buttons on the bookmarks toolbar
- Autofill popup for email, addresses and logins, including "Manage addresses"
- Tooltips and form validation hints
- Most other Nova elements, via the design system's radius tokens (round avatars and dots stay round)

## Requirements

- Firefox 157 or newer, started at least once so a profile exists
- Python 3.6 or newer
  - **Windows:** usually not preinstalled. Install it with `winget install Python.Python.3` or from the Microsoft Store.
  - **macOS / Linux:** usually already installed as `python3`.

## Installation

Download [`square_firefox.py`](square_firefox.py), or clone the repository:

```bash
git clone https://github.com/jnilsson/firefox-square-ui.git
```

## Usage

1. Quit Firefox completely.
2. Run the script:

   ```bash
   python3 square_firefox.py
   ```

   On Windows use `python square_firefox.py`, or simply double-click the file.
3. Start Firefox again.

Run the script once on every computer where you want square tabs. Running it again is safe: it replaces its own block instead of adding a second one, so you can also use it to update the rules.

### Undo

```bash
python3 square_firefox.py --remove
```

Then restart Firefox.

## How it works

For each profile listed in Firefox's `profiles.ini`, the script:

1. Adds a marked block of CSS to `chrome/userChrome.css`. Any rules you already have in that file are kept.
2. Adds `toolkit.legacyUserProfileCustomizations.stylesheets = true` to the profile's `user.js`, so Firefox loads `userChrome.css` at all.

Profile locations it looks in:

| OS | Location |
| --- | --- |
| Windows | `%APPDATA%\Mozilla\Firefox` |
| macOS | `~/Library/Application Support/Firefox` |
| Linux | `~/.mozilla/firefox`, `~/.config/mozilla/firefox`, Snap and Flatpak locations |

## Alternative without CSS

Firefox 157+ has a hidden switch that turns off the whole Nova redesign: open `about:config`, search for `browser.nova.enabled` and set it to `false`. This is unofficial and may be removed in a future version. This script only changes the corners and keeps the rest of the new design.

## Troubleshooting

- **Something is still round after an update:** Firefox may have renamed an element. Open the Browser Toolbox (`Ctrl+Shift+Alt+I`, or `Cmd+Opt+Shift+I` on macOS), pick the round element and add its ID or class to the `CSS` block at the top of the script. Then run the script again.
- **Nothing changed at all:** make sure Firefox was fully closed while the script ran and restarted afterwards.
- **"No Firefox profile found":** start Firefox once so it creates a profile, then run the script again.

## License

[CC0 1.0 Universal](LICENSE): dedicated to the public domain. Use, change and share it for any purpose, no attribution required.
