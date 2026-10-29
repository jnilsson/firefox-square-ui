#!/usr/bin/env python3
"""Brings back square tabs, URL bar and menus in Firefox's new "Nova" design.

Works on Windows, macOS and Linux and needs nothing but Python 3.
Adds a block to chrome/userChrome.css in every Firefox profile it finds and
enables userChrome.css loading via user.js. Your own rules in an existing
userChrome.css are kept.

Usage:
  python3 square_firefox.py           apply (run again to update)
  python3 square_firefox.py --remove  undo

Restart Firefox afterwards.
"""
import configparser
import os
import platform
import re
import sys
from pathlib import Path

BEGIN = "/* >>> firefox-square-ui (added automatically, do not edit) >>> */"
END = "/* <<< firefox-square-ui <<< */"
PREF_MARK = "// firefox-square-ui"
PREF_LINE = 'user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true); ' + PREF_MARK

CSS = """
:root {
  --tab-border-radius: 0 !important;
  --toolbarbutton-border-radius: 0 !important;
  --urlbar-border-radius: 0 !important;
  --panel-border-radius: 0 !important;
  --arrowpanel-border-radius: 0 !important;
  --arrowpanel-menuitem-border-radius: 0 !important;
}

/* Tabs */
.tab-background {
  border-radius: 0 !important;
}

/* URL bar, search bar and suggestion list */
#urlbar,
#urlbar *,
#urlbar-container,
#searchbar,
#searchbar *,
.urlbarView,
.urlbarView-row,
.urlbarView-row-inner {
  border-radius: 0 !important;
}

/* Hamburger menu and other panels */
panel,
panel::part(content),
.panel-arrowcontent,
panelview,
.panel-subview-body,
.subviewbutton,
.toolbaritem-combined-buttons > * {
  border-radius: 0 !important;
}

/* Bookmark folders and context menus */
menupopup,
menupopup::part(content),
menupopup::part(arrowscrollbox),
menu,
menuitem {
  border-radius: 0 !important;
}

/* Buttons on the bookmarks toolbar */
#PersonalToolbar toolbarbutton {
  border-radius: 0 !important;
}
"""


def firefox_roots():
    home = Path.home()
    system = platform.system()
    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        return [(Path(appdata) if appdata else home / "AppData" / "Roaming") / "Mozilla" / "Firefox"]
    if system == "Darwin":
        return [home / "Library" / "Application Support" / "Firefox"]
    xdg = Path(os.environ.get("XDG_CONFIG_HOME") or home / ".config")
    return [
        home / ".mozilla" / "firefox",
        xdg / "mozilla" / "firefox",
        home / "snap" / "firefox" / "common" / ".mozilla" / "firefox",
        home / ".var" / "app" / "org.mozilla.firefox" / ".mozilla" / "firefox",
        home / ".var" / "app" / "org.mozilla.firefox" / "config" / "mozilla" / "firefox",
    ]


def find_profiles():
    found = []
    for root in firefox_roots():
        ini = root / "profiles.ini"
        if not ini.is_file():
            continue
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(ini, encoding="utf-8")
        for section in parser.sections():
            if not section.startswith("Profile"):
                continue
            path = parser.get(section, "Path", fallback=None)
            if not path:
                continue
            relative = parser.get(section, "IsRelative", fallback="1") == "1"
            profile = (root / path) if relative else Path(path)
            if profile.is_dir() and profile not in found:
                found.append(profile)
    return found


def strip_block(text):
    pattern = r"\n*" + re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n?"
    return re.sub(pattern, "\n", text, flags=re.S).strip()


def read(path):
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def update_user_js(profile, enable):
    user_js = profile / "user.js"
    lines = [line for line in read(user_js).splitlines() if PREF_MARK not in line]
    if enable:
        lines.append(PREF_LINE)
    if lines:
        user_js.write_text("\n".join(lines) + "\n", encoding="utf-8")
    elif user_js.is_file():
        user_js.unlink()


def apply(profile):
    chrome = profile / "chrome"
    chrome.mkdir(exist_ok=True)
    css_file = chrome / "userChrome.css"
    own = strip_block(read(css_file))
    block = BEGIN + "\n" + CSS.strip() + "\n" + END + "\n"
    css_file.write_text((own + "\n\n" if own else "") + block, encoding="utf-8")
    update_user_js(profile, enable=True)


def remove(profile):
    css_file = profile / "chrome" / "userChrome.css"
    if css_file.is_file():
        own = strip_block(read(css_file))
        if own:
            css_file.write_text(own + "\n", encoding="utf-8")
        else:
            css_file.unlink()
    update_user_js(profile, enable=False)


def main():
    removing = "--remove" in sys.argv[1:]
    profiles = find_profiles()
    if not profiles:
        print("No Firefox profile found. Has Firefox been started on this computer at least once?")
        return 1
    for profile in profiles:
        try:
            remove(profile) if removing else apply(profile)
            print(("Removed from: " if removing else "Applied to: ") + str(profile))
        except OSError as error:
            print("Error in " + str(profile) + ": " + str(error))
    print("\nDone. Please quit Firefox completely and start it again.")
    return 0


if __name__ == "__main__":
    code = main()
    if platform.system() == "Windows":
        # Keeps the window open when the script was started by double-click
        try:
            input("\nPress Enter to exit...")
        except EOFError:
            pass
    sys.exit(code)
