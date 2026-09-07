"""Creates/removes the per-user Startup-folder shortcut for the MSI install.

WiX's declarative `<Shortcut>` on a component with an HKCU keypath resolves
the per-user Startup folder correctly at *install* time (in the installing
user's impersonated context) but NOT at *removal* time, where the standard
`RemoveShortcuts` action resolves the all-users Startup folder instead -
silently leaving the real per-user shortcut behind on uninstall. Owning both
create and delete here, and recording the exact path used at creation time,
sidesteps that mismatch entirely: removal just deletes a known absolute
path, with no folder resolution needed.

The marker file lives under `.runtime/`, not the registry, because the MSI
custom action that runs this at install time is impersonated as the
installing user (so per-user paths resolve correctly) but that user may not
hold HKLM write rights, whereas `.runtime/` is explicitly ACL'd for any
signed-in user to write (see installer/Components.wxs).
"""

from __future__ import annotations

import os
from pathlib import Path
import sys

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MARKER_FILE = REPOSITORY_ROOT / ".runtime" / "tray-startup-shortcut-path.txt"
SHORTCUT_NAME = "LuxTime Tray.lnk"


def _startup_folder() -> Path:
    return Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def install() -> int:
    import win32com.client

    shortcut_path = _startup_folder() / SHORTCUT_NAME
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortcut(str(shortcut_path))
    shortcut.TargetPath = str(REPOSITORY_ROOT / "python" / "pythonw.exe")
    shortcut.Arguments = "-m tray.main"
    shortcut.WorkingDirectory = str(REPOSITORY_ROOT)
    shortcut.Description = "LuxTime interactive system tray application"
    shortcut.Save()

    MARKER_FILE.parent.mkdir(parents=True, exist_ok=True)
    MARKER_FILE.write_text(str(shortcut_path), encoding="utf-8")
    return 0


def remove() -> int:
    if not MARKER_FILE.is_file():
        return 0
    shortcut_path = Path(MARKER_FILE.read_text(encoding="utf-8").strip())
    shortcut_path.unlink(missing_ok=True)
    MARKER_FILE.unlink(missing_ok=True)
    return 0


def main() -> int:
    verb = sys.argv[1] if len(sys.argv) > 1 else None
    if verb == "install":
        return install()
    if verb == "remove":
        return remove()
    print("Usage: startup_shortcut.py install|remove", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
