"""Native Windows prompts used by the interactive tray."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
from typing import Literal

LockedTaskAction = Literal["resume", "stop", "skip"]

RESUME_BUTTON = 1001
STOP_BUTTON = 1002
SKIP_BUTTON = 1003

TDF_ALLOW_DIALOG_CANCELLATION = 0x0008
TDF_USE_COMMAND_LINKS = 0x0010
TDF_SIZE_TO_CONTENT = 0x01000000
TDN_CREATED = 0
HWND_TOPMOST = -1
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002

_CALLBACK_FACTORY = getattr(ctypes, "WINFUNCTYPE", ctypes.CFUNCTYPE)
_HRESULT = ctypes.c_long
_LONG_PTR = ctypes.c_ssize_t
_TASKDIALOGCALLBACK = _CALLBACK_FACTORY(
    _HRESULT,
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
    _LONG_PTR,
)


class _TASKDIALOG_BUTTON(ctypes.Structure):
    _fields_ = (
        ("nButtonID", ctypes.c_int),
        ("pszButtonText", wintypes.LPCWSTR),
    )


class _TASKDIALOGCONFIG(ctypes.Structure):
    _fields_ = (
        ("cbSize", wintypes.UINT),
        ("hwndParent", wintypes.HWND),
        ("hInstance", wintypes.HINSTANCE),
        ("dwFlags", wintypes.UINT),
        ("dwCommonButtons", wintypes.UINT),
        ("pszWindowTitle", wintypes.LPCWSTR),
        ("hMainIcon", ctypes.c_void_p),
        ("pszMainInstruction", wintypes.LPCWSTR),
        ("pszContent", wintypes.LPCWSTR),
        ("cButtons", wintypes.UINT),
        ("pButtons", ctypes.POINTER(_TASKDIALOG_BUTTON)),
        ("nDefaultButton", ctypes.c_int),
        ("cRadioButtons", wintypes.UINT),
        ("pRadioButtons", ctypes.POINTER(_TASKDIALOG_BUTTON)),
        ("nDefaultRadioButton", ctypes.c_int),
        ("pszVerificationText", wintypes.LPCWSTR),
        ("pszExpandedInformation", wintypes.LPCWSTR),
        ("pszExpandedControlText", wintypes.LPCWSTR),
        ("pszCollapsedControlText", wintypes.LPCWSTR),
        ("hFooterIcon", ctypes.c_void_p),
        ("pszFooter", wintypes.LPCWSTR),
        ("pfCallback", _TASKDIALOGCALLBACK),
        ("lpCallbackData", _LONG_PTR),
        ("cxWidth", wintypes.UINT),
    )


def _session_summary(sessions: list[dict]) -> str:
    lines = []
    for session in sessions[:8]:
        project = str(session.get("project") or "Untitled project")
        description = str(session.get("description") or "").strip()
        lines.append(f"• {project}{f' — {description}' if description else ''}")
    if len(sessions) > len(lines):
        lines.append(f"• and {len(sessions) - len(lines)} more")
    return "\n".join(lines)


def prompt_for_locked_tasks(application_name: str, sessions: list[dict]) -> LockedTaskAction:
    """Show one foreground Windows prompt for all timers paused by a lock."""

    if os.name != "nt":
        raise RuntimeError("Locked-task prompts require Windows")
    if not sessions:
        return "skip"

    try:
        return _task_dialog(application_name, sessions)
    except (AttributeError, OSError):
        return _message_box(application_name, sessions)


def _task_dialog(application_name: str, sessions: list[dict]) -> LockedTaskAction:
    comctl32 = ctypes.WinDLL("comctl32", use_last_error=True)
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.SetWindowPos.argtypes = (
        wintypes.HWND,
        wintypes.HWND,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        wintypes.UINT,
    )
    user32.SetForegroundWindow.argtypes = (wintypes.HWND,)

    @_TASKDIALOGCALLBACK
    def on_dialog_event(hwnd, notification, _wparam, _lparam, _callback_data):
        if notification == TDN_CREATED:
            user32.SetWindowPos(
                hwnd,
                HWND_TOPMOST,
                0,
                0,
                0,
                0,
                SWP_NOMOVE | SWP_NOSIZE,
            )
            user32.SetForegroundWindow(hwnd)
        return 0

    buttons = (_TASKDIALOG_BUTTON * 3)(
        _TASKDIALOG_BUTTON(RESUME_BUTTON, "Resume timers\nContinue tracking every locked task."),
        _TASKDIALOG_BUTTON(STOP_BUTTON, "Stop timers\nFinish every locked task without adding locked time."),
        _TASKDIALOG_BUTTON(SKIP_BUTTON, "Skip for now\nLeave every task locked and paused."),
    )
    count = len(sessions)
    noun = "timer was" if count == 1 else "timers were"
    config = _TASKDIALOGCONFIG(
        cbSize=ctypes.sizeof(_TASKDIALOGCONFIG),
        dwFlags=TDF_ALLOW_DIALOG_CANCELLATION | TDF_USE_COMMAND_LINKS | TDF_SIZE_TO_CONTENT,
        pszWindowTitle=application_name,
        pszMainInstruction=f"{count} locked {noun} paused",
        pszContent="Choose what to do with the work that was active when Windows locked.",
        cButtons=len(buttons),
        pButtons=buttons,
        nDefaultButton=RESUME_BUTTON,
        pszExpandedInformation=_session_summary(sessions),
        pszExpandedControlText="Show locked tasks",
        pszCollapsedControlText="Hide locked tasks",
        pfCallback=on_dialog_event,
    )
    selected = ctypes.c_int()
    comctl32.TaskDialogIndirect.argtypes = (
        ctypes.POINTER(_TASKDIALOGCONFIG),
        ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(wintypes.BOOL),
    )
    comctl32.TaskDialogIndirect.restype = _HRESULT
    result = comctl32.TaskDialogIndirect(
        ctypes.byref(config),
        ctypes.byref(selected),
        None,
        None,
    )
    if result != 0:
        raise OSError(f"TaskDialogIndirect failed with HRESULT 0x{result & 0xFFFFFFFF:08X}")
    return {
        RESUME_BUTTON: "resume",
        STOP_BUTTON: "stop",
        SKIP_BUTTON: "skip",
    }.get(selected.value, "skip")


def _message_box(application_name: str, sessions: list[dict]) -> LockedTaskAction:
    count = len(sessions)
    noun = "timer" if count == 1 else "timers"
    result = ctypes.windll.user32.MessageBoxW(
        None,
        f"{count} locked {noun} are paused.\n\n"
        "Yes — resume\nNo — stop\nCancel — skip",
        f"{application_name} — Locked timers",
        0x00000003 | 0x00000020 | 0x00010000 | 0x00040000,
    )
    return {6: "resume", 7: "stop"}.get(result, "skip")
