"""pywin32 service host for the LuxTime watchdog."""

from __future__ import annotations

from pathlib import Path
import sys
import threading

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

import servicemanager
import win32event
import win32service
import win32serviceutil

from service.watchdog import LuxTimeWatchdog


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


if __name__ == "__main__":
    win32serviceutil.HandleCommandLine(LuxTimeService)
