# start custom imports - DO NOT MANUALLY EDIT BELOW
# end custom imports - DO NOT MANUALLY EDIT ABOVE
from PyQt5 import QtWidgets, QtGui, uic


class ContrastWindow(QtWidgets.QMainWindow):

    def __init__(self) -> None:
        # start typedef - DO NOT MANUALLY EDIT BELOW
        self.freezeContrastBox: QtWidgets.QCheckBox
        self.minCapSlider: QtWidgets.QSlider
        self.label_2: QtWidgets.QLabel
        self.maxCapSlider: QtWidgets.QSlider
        self.label: QtWidgets.QLabel
        # end typedef - DO NOT MANUALLY EDIT ABOVE

        super().__init__()

        uic.loadUi("ContrastWindow.ui", self)

        self.minCapSlider.setTracking(False)
        self.maxCapSlider.setTracking(False)

        pass

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.hide()
        a0.ignore()
