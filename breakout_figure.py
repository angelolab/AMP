# start custom imports - DO NOT MANUALLY EDIT BELOW
from mplwidget import MplWidget
# end custom imports - DO NOT MANUALLY EDIT ABOVE

from PyQt5 import QtWidgets, uic


class BreakoutWindow(QtWidgets.QMainWindow):

    def __init__(self) -> None:
        # start typedef - DO NOT MANUALLY EDIT BELOW
        self.statusbar: QtWidgets.QStatusBar
        self.menubar: QtWidgets.QMenuBar
        self.MplWidget: MplWidget
        self.centralwidget: QtWidgets.QWidget
        # end typedef - DO NOT MANUALLY EDIT ABOVE

        super().__init__()

        # load ui elements into MainViewer class
        uic.loadUi("BreakoutFigure.ui", self)
