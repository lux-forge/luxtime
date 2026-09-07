"""pywin32 service host for the LuxTime watchdog."""

from __future__ import annotations

import contextlib
import io
from pathlib import Path
import subprocess
import sys
import threading
import traceback

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

import pywintypes
import servicemanager
import win32con
import win32event
import win32security
import win32service
import win32serviceutil
import winerror

from service.watchdog import LuxTimeWatchdog

SERVICE_START = 0x0010
AUTHENTICATED_USERS_SID = "S-1-5-11"


class LuxTimeService(win32serviceutil.ServiceFramework):
    _svc_name_ = "LuxTimeService"
    _svc_display_name_ = "LuxTime Service"
    _svc_description_ = "Ensures the local LuxTime Docker application remains healthy."

    def __init__(self, args: list[str]) -> None:
        super().__init__(args)
        self.stop_handle = win32event.CreateEvent(None, 0, 0, None)
        self.stop_event = threading.Event()

    def SvcStop(self) -> None:
        servicemanager.LogInfoMsg("LuxTime Service stop requested")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.stop_event.set()
        win32event.SetEvent(self.stop_handle)

    def SvcDoRun(self) -> None:
        servicemanager.LogInfoMsg("LuxTime Service starting")
        try:
            LuxTimeWatchdog().run(self.stop_event)
        except Exception as error:
            servicemanager.LogErrorMsg(
                f"LuxTime Service failed: {type(error).__name__}: {error}"
            )
            raise
        finally:
            servicemanager.LogInfoMsg("LuxTime Service stopped")


def _grant_authenticated_users_start_right() -> None:
    """Add an ACE letting any signed-in user start the service without a UAC prompt.

    Strictly additive: appends one ACE for Authenticated Users if an
    equivalent one isn't already present, and never touches any other ACE.
    This is what lets the desktop shortcut launcher (running as a standard
    user) start the service on click.
    """
    sid = win32security.ConvertStringSidToSid(AUTHENTICATED_USERS_SID)
    scm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_CONNECT)
    try:
        handle = win32service.OpenService(
            scm,
            LuxTimeService._svc_name_,
            win32con.READ_CONTROL | win32con.WRITE_DAC,
        )
        try:
            descriptor = win32service.QueryServiceObjectSecurity(
                handle, win32security.DACL_SECURITY_INFORMATION
            )
            dacl = descriptor.GetSecurityDescriptorDacl()
            already_granted = any(
                dacl.GetAce(index)[0][0] == win32security.ACCESS_ALLOWED_ACE_TYPE
                and dacl.GetAce(index)[2] == sid
                and dacl.GetAce(index)[1] & SERVICE_START
                for index in range(dacl.GetAceCount())
            )
            if not already_granted:
                dacl.AddAccessAllowedAce(win32security.ACL_REVISION, SERVICE_START, sid)
                descriptor.SetSecurityDescriptorDacl(1, dacl, 0)
                win32service.SetServiceObjectSecurity(
                    handle, win32security.DACL_SECURITY_INFORMATION, descriptor
                )
        finally:
            win32service.CloseServiceHandle(handle)
    finally:
        win32service.CloseServiceHandle(scm)


def _log_install_result(verb: str, captured_output: str, error: BaseException | None) -> None:
    """Write a readable record of an `ensure-installed`/`ensure-removed` failure.

    The MSI custom action host (WixQuietExec) captures this process's output
    through a codepage conversion that garbles it in the msiexec log, and a
    failed install execute sequence removes this action's own just-installed
    files afterward - so this deliberately writes next to (not inside)
    REPOSITORY_ROOT, outside the install tree MSI owns and cleans up.
    """
    log_path = REPOSITORY_ROOT.parent / "LuxTime-install-error.log"
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"--- {verb} failed ---\n")
        if captured_output:
            handle.write(captured_output)
            if not captured_output.endswith("\n"):
                handle.write("\n")
        if error is not None:
            traceback.print_exception(type(error), error, error.__traceback__, file=handle)


def main() -> int:
    """Dispatch to pywin32's verbs, plus two installer-friendly idempotent ones.

    ``ensure-installed``/``ensure-removed`` give the MSI custom actions a
    single static command line that succeeds whether or not the service is
    already in the desired state, and a real process exit code to detect
    genuine failures (``HandleCommandLine`` alone never calls ``sys.exit``).
    """
    argv = list(sys.argv)
    verb = argv[1] if len(argv) > 1 else None

    if verb in ("ensure-installed", "ensure-removed"):
        captured = io.StringIO()
        try:
            with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
                result = _ensure_installed() if verb == "ensure-installed" else _ensure_removed()
        except (Exception, SystemExit) as error:  # noqa: BLE001 - must still fail the MSI custom action
            _log_install_result(verb, captured.getvalue(), error)
            raise
        if result:
            _log_install_result(verb, captured.getvalue(), None)
        return result

    return win32serviceutil.HandleCommandLine(LuxTimeService, argv=argv) or 0


def _ensure_installed() -> int:
    # Options must precede the verb - win32serviceutil.HandleCommandLine uses
    # plain getopt, which stops parsing options at the first positional
    # argument, so "install --startup delayed" silently drops --startup.
    error_code = win32serviceutil.HandleCommandLine(
        LuxTimeService, argv=[sys.argv[0], "--startup", "delayed", "install"]
    )
    if error_code:
        return error_code
    _grant_authenticated_users_start_right()
    subprocess.run(
        [
            "sc.exe",
            "failure",
            LuxTimeService._svc_name_,
            "reset=",
            "86400",
            "actions=",
            "restart/15000/restart/30000/restart/60000",
        ],
        check=True,
    )
    subprocess.run(["sc.exe", "failureflag", LuxTimeService._svc_name_, "1"], check=True)
    try:
        win32serviceutil.StartService(LuxTimeService._svc_name_)
    except pywintypes.error as error:
        if error.winerror != winerror.ERROR_SERVICE_ALREADY_RUNNING:
            raise
    return 0


def _ensure_removed() -> int:
    try:
        win32serviceutil.StopService(LuxTimeService._svc_name_)
    except pywintypes.error as error:
        if error.winerror not in (
            winerror.ERROR_SERVICE_NOT_ACTIVE,
            winerror.ERROR_SERVICE_DOES_NOT_EXIST,
        ):
            raise
    try:
        win32serviceutil.RemoveService(LuxTimeService._svc_name_)
    except pywintypes.error as error:
        if error.winerror != winerror.ERROR_SERVICE_DOES_NOT_EXIST:
            raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
