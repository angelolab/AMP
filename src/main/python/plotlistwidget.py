from PyQt5 import QtWidgets, QtCore

from matplotlib.backends.backend_qt5agg import FigureCanvas
from mplwidget import Plot

import sip

from typing import Dict

# Handles storing plotting data in Qt List


class PlotListWidgetItem(QtWidgets.QListWidgetItem):
    def __init__(self, text: str = None, plot: Plot = None, path: str = None) -> None:
        super().__init__(text)
        self.setFlags(self.flags() | QtCore.Qt.ItemIsEditable)
        self.plot = plot
        self.path = path

    def refresh(self, canvas: FigureCanvas):
        self.plot.plot_update(canvas, self.plot.plot_data)


class PlotListWidget(QtWidgets.QListWidget):
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)
        self.path_to_name: Dict[str, str] = {}

    def add_item(self, name: str, plot: Plot, path: str) -> None:
        super().addItem(PlotListWidgetItem(name, plot, path))
        self.path_to_name[path] = name

    # path is a static breadcumb trail to allow for renaming.
    # for file-images this is literally the filepath.
    # for other plots, this will be a different unique id.
    def get_item_row_by_path(self, path: str) -> int:
        if path in self.path_to_name.keys():
            name = self.path_to_name[path]
        else:
            return -1
        matches = self.findItems(name, QtCore.Qt.MatchExactly)
        return self.row(matches[0]) if matches else -1

    # clear entry in path to name dictionary and delete
    def delete_item(self, row: int) -> None:
        self.path_to_name.pop(self.item(row).path, None)
        sip.delete(self.takeItem(row))

    def refresh_current_plot(self, canvas: FigureCanvas) -> None:
        self.currentItem().refresh(canvas)
