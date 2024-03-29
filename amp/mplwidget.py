from os import path

from PyQt5 import QtGui, QtWidgets

from matplotlib.backends.backend_qt5agg import (
    FigureCanvas, NavigationToolbar2QT as NavigationToolbar
)

import numpy as np

from matplotlib.figure import Figure
import matplotlib.cm as cm

from matplotlib.image import AxesImage

from typing import Callable, Dict, Any, List, Union

class Plot(object):
    # base class for plot objects
    # plot objects store a plot_update function, and associated plot_data
    def __init__(self, plot_update: Callable[[FigureCanvas, Dict[str, Any]], None],
                 plot_data: Dict[str, Any]) -> None:
        self.plot_update = plot_update
        self.plot_data = plot_data


def image_plot_update(canvas: FigureCanvas, data: Dict[str, Any]) -> None:
    # ImagePlot update function
    cur_xlim = []
    cur_ylim = []
    if any([isinstance(c, AxesImage) for c in canvas.axes.get_children()]):
        cur_xlim = canvas.axes.get_xlim()
        cur_ylim = canvas.axes.get_ylim()
        #_clean_canvas()
    canvas.axes.clear()

    # check plot data for contrast info
    # contrast is relative now
    raw_imdata = data['image'].copy()
    if 'min_cap' in data.keys() and not data['fixed_contrast']:
        min_cap = data['min_cap'] / 100
        max_cap = data['max_cap'] * np.max(raw_imdata) / 100
        raw_imdata[raw_imdata < min_cap] = min_cap
        raw_imdata[raw_imdata > max_cap] = max_cap

    canvas.axes.imshow(raw_imdata, cmap=cm.afmhot)
    if cur_xlim:
        canvas.axes.set_xlim(cur_xlim)
        canvas.axes.set_ylim(cur_ylim)
    canvas.draw()

def hist_plot_update(canvas: FigureCanvas, data: Dict[str, Any]) -> None:
    # HistPlot update function
    canvas.axes.clear()
    canvas.axes.set_aspect('auto')
    canvas.axes.hist(data['flattened_data'], bins=data['n_bins'])
    if data['threshold'] is not None:
        canvas.axes.axvline(data['threshold'], color='r', linestyle='dashed', linewidth=2)
    canvas.axes.relim()
    canvas.draw()

class ImagePlot(Plot):
    # plots images via imshow
    def __init__(self, data: Any, fixed_contrast: bool = False) -> None:
        super().__init__(image_plot_update, {'image': data, 'fixed_contrast': fixed_contrast})


class HistPlot(Plot):
    # plots histograms via hist
    def __init__(self, data: Any, n_bins: int = 30, thresh: Union[float, None] = None) -> None:
        super().__init__(hist_plot_update, {'flattened_data': data, 'n_bins': n_bins, 'threshold': thresh})

# a more customizable toolbar (loadable icons)
class CleanToolbar(NavigationToolbar):
    toolitems: List[str] = [t for t in NavigationToolbar.toolitems if
                            t[0] in ('Home', 'Pan', 'Zoom', 'Save')]

    # custom icon injection (could be made to be not so hardcoded)
    '''
    toolitems[0] = (toolitems[0][0],
                    toolitems[0][1],
                    'test_icon',
                    toolitems[0][3])
    '''
    # hardcoding is a little bad here?
    resourcedir = "./resources/icons/"

    def __init__(self, canvas: FigureCanvas = None, parent: QtWidgets.QWidget = None) -> None:
        super().__init__(canvas, parent)
        self.sizePolicy().setHorizontalPolicy(QtWidgets.QSizePolicy.Expanding)

    # overloads _icon function to support custom icons
    def _icon(self, name: str) -> QtGui.QIcon:
        if path.exists(path.join(self.basedir, name)):
            return super()._icon(name)
        else:
            pm = QtGui.QPixmap(path.join(self.resourcedir, name))
            if hasattr(pm, 'setDevicePixelRatio'):
                pm.setDevicePixelRatio(self.canvas._dpi_ratio)
            return QtGui.QIcon(pm)


# class for handling plotting widget
class MplWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)
        self.sizePolicy().setHorizontalPolicy(QtWidgets.QSizePolicy.Expanding)
        self._canvas = FigureCanvas(Figure(figsize=(5, 3)))
        self._canvas.sizePolicy().setHorizontalPolicy(
            QtWidgets.QSizePolicy.Expanding)

        vertical_layout = QtWidgets.QVBoxLayout()
        vertical_layout.addWidget(CleanToolbar(self._canvas, parent))
        vertical_layout.addWidget(self._canvas)

        self._canvas.axes = self._canvas.figure.add_subplot(111)
        self._canvas.axes.set_facecolor((0, 0, 0))
        self._canvas.figure.set_facecolor((0, 0, 0))
        self._canvas.axes.set_frame_on(False)
        self._canvas.axes.xaxis.set_visible(False)
        self._canvas.axes.yaxis.set_visible(False)
        self._canvas.figure.tight_layout(pad=0)
        # parent.layout().addWidget(vertical_layout)
        self.setLayout(vertical_layout)
