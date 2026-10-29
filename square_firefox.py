#!/usr/bin/env python3
"""Brings back square (or less rounded) tabs, URL bar and menus in Firefox's new "Nova" design.

Works on Windows, macOS and Linux and needs nothing but Python 3.
Adds a block to chrome/userChrome.css (browser UI) and chrome/userContent.css
(about: pages such as about:preferences) in every Firefox profile it finds,
and enables loading them via user.js. Your own rules in existing files are
kept.

Usage:
  python3 square_firefox.py                         interactive menu
  python3 square_firefox.py --install [--radius N]  install or update, N px corners (default 0)
  python3 square_firefox.py --remove                undo

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
/* Nova design tokens most rounded elements are built from.
   --border-radius-circle is left alone so avatars and dots stay round. */
:root {
  --border-radius-xsmall: {R} !important;
  --border-radius-small: {R} !important;
  --border-radius-medium: {R} !important;
  --border-radius-large: {R} !important;
  --border-radius-xlarge: {R} !important;
  --popup-border-radius: {R} !important;
  --panel-menuitem-border-radius: {R} !important;
  --button-border-radius: {R} !important;
  --tooltip-border-radius: {R} !important;
  --tab-border-radius: {R} !important;
  --toolbarbutton-border-radius: {R} !important;
  --urlbar-border-radius: {R} !important;
  --panel-border-radius: {R} !important;
  --arrowpanel-border-radius: {R} !important;
  --arrowpanel-menuitem-border-radius: {R} !important;
}

/* Tabs */
.tab-background {
  border-radius: {R} !important;
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
  border-radius: {R} !important;
}

/* Hamburger menu and other panels */
panel,
panel::part(content),
.panel-arrowcontent,
panelview,
.panel-subview-body,
.subviewbutton,
.toolbaritem-combined-buttons > * {
  border-radius: {R} !important;
}

/* Bookmark folders and context menus */
menupopup,
menupopup::part(content),
menupopup::part(arrowscrollbox),
menu,
menuitem {
  border-radius: {R} !important;
}

/* Buttons on the bookmarks toolbar */
#PersonalToolbar toolbarbutton {
  border-radius: {R} !important;
}

/* Autofill popup for email, addresses and logins ("Manage addresses").
   The popup sets its own radius, and its rows round themselves inside a
   shadow root that only custom properties can reach. */
#PopupAutoComplete {
  --panel-border-radius: {R} !important;
  --popup-border-radius: {R} !important;
}

#PopupAutoComplete autocomplete-row-item {
  --row-item-border-radius: {R} !important;
  --button-border-radius: {R} !important;
  --border-radius-xsmall: {R} !important;
  --border-radius-small: {R} !important;
  --border-radius-medium: {R} !important;
  --border-radius-large: {R} !important;
  border-radius: {R} !important;
}

/* Tooltips and form validation hints */
tooltip,
#invalid-form-popup {
  border-radius: {R} !important;
}
"""

# about: pages are web pages, so userChrome.css does not reach them. Their
# cards, buttons and inputs are built from the same radius tokens, but
# components re-declare them on their own host element, so set them on every
# element rather than only on :root.
CONTENT_CSS = """
@-moz-document url-prefix("about:") {
  :root,
  * {
    --page-nav-button-border-radius: {R} !important;
    --page-nav-button-border-radius-focused: {R} !important;
    --input-border-radius: {R} !important;
    --input-search-border-radius: {R} !important;
    --urlbar-border-radius: {R} !important;
    --urlbar-inner-border-radius: {R} !important;
    --urlbarview-border-radius: {R} !important;
    --toolbarbutton-border-radius: {R} !important;
    --content-search-handoff-ui-border-radius: {R} !important;
    --border-radius-xsmall: {R} !important;
    --border-radius-small: {R} !important;
    --border-radius-medium: {R} !important;
    --border-radius-large: {R} !important;
    --border-radius-xlarge: {R} !important;
    --button-border-radius: {R} !important;
    --popup-border-radius: {R} !important;
    --panel-border-radius: {R} !important;
    --panel-menuitem-border-radius: {R} !important;
  }
}
"""

FILES = {"userChrome.css": CSS, "userContent.css": CONTENT_CSS}
MAX_RADIUS = 50


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


def parse_radius(text):
    """Turns "0", "4" or "4px" into a CSS length; raises ValueError otherwise."""
    value = text.strip().lower()
    if value.endswith("px"):
        value = value[:-2].strip()
    number = float(value)
    if not 0 <= number <= MAX_RADIUS:
        raise ValueError(text)
    return "0" if number == 0 else "%gpx" % number


def apply(profile, radius):
    chrome = profile / "chrome"
    chrome.mkdir(exist_ok=True)
    for name, css in FILES.items():
        css_file = chrome / name
        own = strip_block(read(css_file))
        block = BEGIN + "\n" + css.strip().replace("{R}", radius) + "\n" + END + "\n"
        css_file.write_text((own + "\n\n" if own else "") + block, encoding="utf-8")
    update_user_js(profile, enable=True)


def remove(profile):
    for name in FILES:
        css_file = profile / "chrome" / name
        if css_file.is_file():
            own = strip_block(read(css_file))
            if own:
                css_file.write_text(own + "\n", encoding="utf-8")
            else:
                css_file.unlink()
    update_user_js(profile, enable=False)


def ask(prompt):
    try:
        return input(prompt).strip()
    except EOFError:
        return None


def choose_interactively():
    """Shows the menu; returns ("install", radius), ("remove", None) or None to quit."""
    print("firefox-square-ui\n")
    print("  1) Install / update")
    print("  2) Remove")
    print("  3) Quit\n")
    while True:
        choice = ask("Choose an option [1-3]: ")
        if choice in (None, "3", "q"):
            return None
        if choice == "2":
            return "remove", None
        if choice == "1":
            break
        print("Please enter 1, 2 or 3.")
    print("\nCorner radius in pixels: 0 = fully square, Firefox's Nova default is about 8-16.")
    while True:
        answer = ask("Radius [0-%d, default 0]: " % MAX_RADIUS)
        if answer is None:
            return None
        try:
            return "install", parse_radius(answer or "0")
        except ValueError:
            print("Please enter a number from 0 to %d." % MAX_RADIUS)


def parse_args(args):
    """Returns the same shape as choose_interactively(), or "menu" without arguments."""
    if not args:
        return "menu"
    if "--remove" in args:
        return "remove", None
    radius = "0"
    if "--radius" in args:
        index = args.index("--radius")
        try:
            radius = parse_radius(args[index + 1])
        except (IndexError, ValueError):
            sys.exit("--radius needs a number from 0 to %d" % MAX_RADIUS)
    if "--install" in args or "--radius" in args:
        return "install", radius
    sys.exit("Unknown arguments. Use --install [--radius N], --remove, or no arguments for the menu.")


def main():
    action = parse_args(sys.argv[1:])
    profiles = find_profiles()
    if not profiles:
        print("No Firefox profile found. Has Firefox been started on this computer at least once?")
        return 1
    if action == "menu":
        action = choose_interactively()
        if action is None:
            print("Nothing changed.")
            return 0
    mode, radius = action
    print()
    for profile in profiles:
        try:
            if mode == "remove":
                remove(profile)
                print("Removed from: " + str(profile))
            else:
                apply(profile, radius)
                print("Applied (radius %s) to: %s" % (radius, profile))
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
