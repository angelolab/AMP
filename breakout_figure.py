# start custom imports - DO NOT MANUALLY EDIT BELOW
from typing import Callable
from mplwidget import MplWidget
# end custom imports - DO NOT MANUALLY EDIT ABOVE

from PyQt5 import QtWidgets, QtGui, uic


class BreakoutWindow(QtWidgets.QMainWindow):

    def __init__(self, on_close_callback: Callable[..., None]) -> None:
        # start typedef - DO NOT MANUALLY EDIT BELOW
        self.statusbar: QtWidgets.QStatusBar
        self.menubar: QtWidgets.QMenuBar
        self.MplWidget: MplWidget
        self.centralwidget: QtWidgets.QWidget
        # end typedef - DO NOT MANUALLY EDIT ABOVE

        super().__init__()

        # load ui elements into MainViewer class
        uic.loadUi("BreakoutFigure.ui", self)

        self.on_close_callback = on_close_callback

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.on_close_callback()
        event.accept()
