# -*- coding: utf-8 -*-
"""Lucent: customise Kodi's power dialog (DialogButtonMenu.xml).

RunScript(special://skin/scripts/powermenu.py)         open the editor
RunScript(special://skin/scripts/powermenu.py,reset)   remove own buttons and show all of Kodi's again

Stored in skin settings, read by DialogButtonMenu.xml:
  Skin.HasSetting(lucent.pm.hide.<key>)                hide one of Kodi's own buttons
  Skin.String(lucent.pm.cN.label / .action)  N=1..6    own buttons, shown at the top
"""
import sys

import xbmc
import xbmcgui

import menu   # reuse the action picker of the menu editor (its main() only runs when started directly)

NCUSTOM = 6
HEADING = "Lucent"
_NL = xbmc.getLanguage(xbmc.ISO_639_1) == "nl"

# key, Kodi string id (the same labels the dialog shows)
STANDARD = [("quit", 13012), ("off", 13016), ("sleep", 13011), ("reboot", 13013),
            ("logoff", 20126), ("inhibit", 13017), ("settings", 5)]

T = {
    "title": ("Power menu", "Afsluitmenu"),
    "kodi": ("Kodi's own buttons", "Knoppen van Kodi"),
    "add": ("+ Add your own button", "+ Eigen knop toevoegen"),
    "reset": ("Restore the standard power menu", "Standaard afsluitmenu herstellen"),
    "reset_q": ("Remove your own buttons and show all of Kodi's buttons again?",
                "Je eigen knoppen verwijderen en alle knoppen van Kodi weer tonen?"),
    "shown": ("shown", "zichtbaar"),
    "hidden": ("hidden", "verborgen"),
    "own": ("your own button", "eigen knop"),
    "full": ("You can add at most {0} buttons.", "Je kunt maximaal {0} knoppen toevoegen."),
    "name": ("Name of the button", "Naam van de knop"),
    "rename": ("Name", "Naam"),
    "action": ("When clicked", "Bij klikken"),
    "up": ("Move up", "Omhoog"),
    "down": ("Move down", "Omlaag"),
    "remove": ("Remove this button", "Deze knop verwijderen"),
    "nowidgets": ("That option only works in the side menu.", "Die optie werkt alleen in het zijmenu."),
}


def tr(key, *args):
    text = T[key][1 if _NL else 0]
    return text.format(*args) if args else text


def get(name):
    return xbmc.getInfoLabel(f"Skin.String({name})")


def put(name, value):
    value = (value or "").replace('"', "'")
    if value:
        xbmc.executebuiltin(f'Skin.SetString({name},"{value}")')
    else:
        xbmc.executebuiltin(f"Skin.Reset({name})")


def hidden(key):
    return xbmc.getCondVisibility(f"Skin.HasSetting(lucent.pm.hide.{key})")


def customs():
    """Own buttons as a list of (label, action), in order, without gaps."""
    out = []
    for n in range(1, NCUSTOM + 1):
        action = get(f"lucent.pm.c{n}.action")
        if action:
            out.append((get(f"lucent.pm.c{n}.label") or action, action))
    return out


def save(items):
    for n in range(1, NCUSTOM + 1):
        label, action = items[n - 1] if n <= len(items) else ("", "")
        put(f"lucent.pm.c{n}.label", label)
        put(f"lucent.pm.c{n}.action", action)
    xbmc.sleep(100)


def pick():
    action, info = menu.pick_action()
    if action == menu.SHOW_WIDGETS:
        xbmcgui.Dialog().ok(HEADING, tr("nowidgets"))
        return None, None
    return action, (info[0] if info else "")


def edit_custom(index):
    while True:
        items = customs()
        if index >= len(items):
            return
        label, action = items[index]
        options = [f"{tr('rename')}: {label}", f"{tr('action')}: {menu.describe_action(action, label)}",
                   tr("up"), tr("down"), tr("remove")]
        choice = xbmcgui.Dialog().select(label, options)
        if choice < 0:
            return
        if choice == 0:
            name = menu.keyboard(tr("name"), label)
            if name:
                items[index] = (name, action)
        elif choice == 1:
            new, _name = pick()
            if new:
                items[index] = (label, new)
        elif choice == 2 and index > 0:
            items[index - 1], items[index] = items[index], items[index - 1]
            index -= 1
        elif choice == 3 and index < len(items) - 1:
            items[index + 1], items[index] = items[index], items[index + 1]
            index += 1
        elif choice == 4:
            del items[index]
            save(items)
            return
        save(items)


def editor():
    while True:
        items = customs()
        labels, kinds = [], []
        for n, (label, _action) in enumerate(items):
            labels.append(f"{label}  ·  {tr('own')}")
            kinds.append(("custom", n))
        labels.append(tr("add"))
        kinds.append(("add", None))
        for key, sid in STANDARD:
            state = tr("hidden") if hidden(key) else tr("shown")
            labels.append(f"{tr('kodi')} · {xbmc.getLocalizedString(sid)}: {state}")
            kinds.append(("std", key))
        labels.append(tr("reset"))
        kinds.append(("reset", None))
        choice = xbmcgui.Dialog().select(tr("title"), labels)
        if choice < 0:
            return
        kind, value = kinds[choice]
        if kind == "custom":
            edit_custom(value)
        elif kind == "add":
            if len(items) >= NCUSTOM:
                xbmcgui.Dialog().ok(HEADING, tr("full", NCUSTOM))
                continue
            action, name = pick()
            if not action:
                continue
            name = menu.keyboard(tr("name"), name or "")
            if name:
                items.append((name, action))
                save(items)
        elif kind == "std":
            xbmc.executebuiltin(f"Skin.ToggleSetting(lucent.pm.hide.{value})")
            xbmc.sleep(100)
        elif kind == "reset" and xbmcgui.Dialog().yesno(HEADING, tr("reset_q")):
            reset()


def reset():
    save([])
    for key, _sid in STANDARD:
        xbmc.executebuiltin(f"Skin.Reset(lucent.pm.hide.{key})")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        reset()
    else:
        editor()
