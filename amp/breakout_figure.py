# start custom imports - DO NOT MANUALLY EDIT BELOW
from amp.mplwidget import MplWidget
# end custom imports - DO NOT MANUALLY EDIT ABOVE

from typing import Callable
from PyQt5 import QtWidgets, QtGui, uic

from amp.resource_path import resource_path


class BreakoutWindow(QtWidgets.QMainWindow):

    def __init__(self, on_close_callback: Callable[..., None],
                 title: str="Breakout Window") -> None:
        # start typedef - DO NOT MANUALLY EDIT BELOW
        self.statusbar: QtWidgets.QStatusBar
        self.menubar: QtWidgets.QMenuBar
        self.MplWidget: MplWidget
        self.centralwidget: QtWidgets.QWidget
        # end typedef - DO NOT MANUALLY EDIT ABOVE

        super().__init__()

        # load ui elements into MainViewer class
        uic.loadUi(
            resource_path('ui/BreakoutFigure.ui'),
            self
        )

        self.on_close_callback = on_close_callback

        self.setWindowTitle(title)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.on_close_callback()
        event.accept()
