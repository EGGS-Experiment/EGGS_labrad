from artiq.dashboard.moninj import _TTLWidget, _DeviceManager, MonInj, _MonInjDock
import asyncio

from PyQt5 import QtWidgets
from qasync import QEventLoop

import time


if __name__ == "__main__":
    app = QtWidgets.QApplication(["ARTIQ Dashboard"])
    th1 = _MonInjDock('TTL')
    dm=_DeviceManager()
    ttlwidgets = [_TTLWidget(dm, str(i), 'TTL_Out', 'channel ' + str(i)) for i in range(10)]
    th1.layout_widgets(ttlwidgets)
    th1.show()
    time.sleep(5)