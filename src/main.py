import sys
from PyQt5 import QtWidgets

from amp.main_viewer import MainViewer

# start application
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainViewer()
    window.show()
    sys.exit(app.exec_())
