import sys
import traceback
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt

from amp.main_viewer import MainViewer

# start application
if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)
    window = MainViewer()
    window.show()
    def windowed_excepthook(type, value, tback):
        error_window = QtWidgets.QMessageBox()
        error_window.setText(f'{type.__name__}: {value}')
        error_window.setInformativeText('\n'.join(traceback.format_tb(tback)))
        error_window.exec()

        sys.__excepthook__(type, value, tback)

        window.close()

    sys.excepthook = windowed_excepthook

    sys.exit(app.exec_())

