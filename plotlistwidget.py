from PyQt5 import QtWidgets, QtCore

import sip

# Handles storing plotting data in Qt List


class PlotListWidgetItem(QtWidgets.QListWidgetItem):
    def __init__(self, text=None, plot=None, path=None):
        super().__init__(text)
        self.setFlags(self.flags() | QtCore.Qt.ItemIsEditable)
        self.plot = plot
        self.path = path

    def refresh(self, canvas):
        self.plot.plot_update(canvas, self.plot.plot_data)


class PlotListWidget(QtWidgets.QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.path_to_name = {}

    def addItem(self, name, plot, path):
        super().addItem(PlotListWidgetItem(name, plot, path))
        self.path_to_name[path] = name

    # path is a static breadcumb trail to allow for renaming.
    # for file-images this is literally the filepath.
    # for other plots, this will be a different unique id.
    def getItemRowByPath(self, path):
        if path in self.path_to_name.keys():
            name = self.path_to_name[path]
        else:
            return -1
        matches = self.findItems(name, QtCore.Qt.MatchExactly)
        return self.row(matches[0]) if matches else -1

    # clear entry in path to name dictionary and delete
    def deleteItem(self, row):
        self.path_to_name.pop(self.item(row).path, None)
        sip.delete(self.takeItem(row))

    def refreshCurrentPlot(self, canvas):
        self.currentItem().refresh(canvas)
