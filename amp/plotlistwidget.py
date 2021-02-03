from PyQt5 import QtWidgets, QtCore

from matplotlib.backends.backend_qt5agg import FigureCanvas
from amp.mplwidget import Plot

import sip

from typing import Dict, Callable, Tuple, Union

# Handles storing plotting data in Qt List


class PlotListWidgetItem(QtWidgets.QListWidgetItem):
    def __init__(self, text: str = None, plot: Plot = None, path: str = None,
                 delete_callback: Callable[..., None] = None, canvas: FigureCanvas = None) -> None:
        super().__init__(text)
        self.setFlags(self.flags() | QtCore.Qt.ItemIsEditable)
        self.plot = plot
        self.path = path
        self.delete_callback = delete_callback
        self.canvas = canvas

    def refresh(self, contrast_settings: Union[Tuple, None] = None):
        if contrast_settings is not None:
            self.plot.plot_data['min_cap'] = contrast_settings[0]
            self.plot.plot_data['max_cap'] = contrast_settings[1]
        self.plot.plot_update(self.canvas, self.plot.plot_data)


class PlotListWidget(QtWidgets.QListWidget):
    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)
        self.path_to_name: Dict[str, str] = {}
        self.canvas = None
        self.check_breakout_callback = None

    def set_canvas(self, default_canvas: FigureCanvas) -> None:
        self.canvas = default_canvas

    def set_breakout_callback(self, callback: Callable[[str], None]) -> None:
        self.check_breakout_callback = callback

    def set_contrast_callback(self, callback: Callable[..., Union[Tuple, None]]) -> None:
        self.contrast_callback = callback

    def add_item(self, name: str, plot: Plot, path: str,
                 delete_callback: Callable[..., None] = None) -> None:

        if self.canvas is None:
            print('PlotListWidget canvas has not been set...\nCannot add item...')
            return

        super().addItem(PlotListWidgetItem(name, plot, path, delete_callback, self.canvas))
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
        if row is None or row < 0:
            return
        if self.item(row).delete_callback is not None:
            self.item(row).delete_callback()

        # remove breakout window
        self.item(row).canvas = None
        self.check_breakout_callback(self.item(row).path)

        self.path_to_name.pop(self.item(row).path, None)
        sip.delete(self.takeItem(row))

    def refresh_current_plot(self, bypass_contrast_lock=False) -> None:
        contrast_settings = self.contrast_callback(bypass_contrast_lock)

        self.currentItem().refresh(contrast_settings)

        for i in range(self.count()):
            if self.item(i).canvas != self.canvas:
                self.item(i).refresh(contrast_settings)
