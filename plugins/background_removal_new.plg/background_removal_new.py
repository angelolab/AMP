# start custom imports - DO NOT MANUALLY EDIT BELOW
# end custom imports - DO NOT MANUALLY EDIT ABOVE
from PyQt5 import QtWidgets, QtCore, uic

from amp.main_viewer import MainViewer

import numpy as np
from scipy.ndimage import gaussian_filter
from PIL import Image

import os
import pathlib
import concurrent.futures
from datetime import datetime

from typing import Dict, List, Any, Union, Tuple
import numbers


class BackgroundRemovalNew(QtWidgets.QMainWindow):

    def __init__(self, main_viewer: MainViewer, ui_path: str):
        # start typedef - DO NOT MANUALLY EDIT BELOW
        self.statusbar: QtWidgets.QStatusBar
        self.menubar: QtWidgets.QMenuBar
        self.pushButton_2: QtWidgets.QPushButton
        self.pushButton_4: QtWidgets.QPushButton
        self.pushButton_3: QtWidgets.QPushButton
        self.splitter_8: QtWidgets.QSplitter
        self.splitter_9: QtWidgets.QSplitter
        self.spinBox_5: QtWidgets.QSpinBox
        self.horizontalSlider_7: QtWidgets.QSlider
        self.splitter_7: QtWidgets.QSplitter
        self.label_5: QtWidgets.QLabel
        self.layoutWidget_4: QtWidgets.QWidget
        self.spinBox_4: QtWidgets.QSpinBox
        self.horizontalSlider_6: QtWidgets.QSlider
        self.splitter_6: QtWidgets.QSplitter
        self.label_4: QtWidgets.QLabel
        self.layoutWidget_3: QtWidgets.QWidget
        self.splitter_5: QtWidgets.QSplitter
        self.groupBox_2: QtWidgets.QGroupBox
        self.spinBox_3: QtWidgets.QSpinBox
        self.horizontalSlider_5: QtWidgets.QSlider
        self.splitter_3: QtWidgets.QSplitter
        self.label_3: QtWidgets.QLabel
        self.layoutWidget_2: QtWidgets.QWidget
        self.spinBox_2: QtWidgets.QSpinBox
        self.horizontalSlider_4: QtWidgets.QSlider
        self.splitter_2: QtWidgets.QSplitter
        self.label_2: QtWidgets.QLabel
        self.layoutWidget: QtWidgets.QWidget
        self.spinBox: QtWidgets.QSpinBox
        self.horizontalSlider_3: QtWidgets.QSlider
        self.splitter: QtWidgets.QSplitter
        self.label: QtWidgets.QLabel
        self.layoutWidget_0: QtWidgets.QWidget
        self.splitter_4: QtWidgets.QSplitter
        self.groupBox: QtWidgets.QGroupBox
        self.tab_2: QtWidgets.QWidget
        self.tab: QtWidgets.QWidget
        self.tabWidget: QtWidgets.QTabWidget
        self.pushButton: QtWidgets.QPushButton
        self.comboBox: QtWidgets.QComboBox
        self.splitter_10: QtWidgets.QSplitter
        self.centralwidget: QtWidgets.QWidget
        # end typedef - DO NOT MANUALLY EDIT ABOVE

        super().__init__()

        # set reference to main window
        self.main_viewer = main_viewer

        # load ui elements into MainViewer class
        uic.loadUi(
            ui_path,
            self
        )

        self.setWindowTitle("Background Removal New")

    # closeEvent is reserved by pyqt so it can't follow style guide :/
    def closeEvent(self, event: QtCore.QEvent) -> None:
        """ Callback for exiting/closing plugin window

        Deletes points and relevant figure data before closing

        Args:
            event (QtCore.QEvent): qt close event (passed via signal)
        """

        event.accept()


# function for amp plugin building
def build_as_plugin(main_viewer: MainViewer, plugin_path: str) -> BackgroundRemovalNew:
    """ Returns an instance of BackgroundRemovalNew

    This function is common to all plugins; it allows the plugin loader
    to correctly load the plugin.

    Args:
        main_viewer (MainViewer): reference to the main window
    """

    return BackgroundRemovalNew(main_viewer, plugin_path)
