from PyQt5 import QtWidgets, QtCore, uic

from mplwidget import ImagePlot
from point import Point
from main_viewer import MainViewer

import numpy as np
from scipy.ndimage import gaussian_filter

import os
import concurrent.futures
from typing import Dict


class BackgroundRemoval(QtWidgets.QMainWindow):

    def __init__(self, main_viewer: MainViewer):
        super().__init__()

        # set reference to main window
        self.main_viewer = main_viewer

        # points dict (indexed by path)
        self.points: Dict[str, Point] = {}

        # reusable figure id's
        self.preview_id = None
        self.br_reuse_id = None

        # load ui elements into MainViewer class
        uic.loadUi("BackgroundRemoval.ui", self)

        # General UI threadpool (probably shouldn't use this for big algos)
        self.executer = concurrent.futures.ThreadPoolExecutor(max_workers=1)

        # connect UI callbacks
        self.loadingAddButton.clicked.connect(self.on_add_point)
        self.loadingPointsList.currentItemChanged.connect(self.on_point_change)
        self.loadingChannelSelect.currentTextChanged.connect(self.on_channel_change)
        self.loadingRemoveButton.clicked.connect(self.on_remove_point)
        self.rparamsTestButton.clicked.connect(self.test_br_params)

        self.setWindowTitle("Background Removal")

    # closeEvent is reserved by pyqt so it can't follow style guide :/
    def closeEvent(self, event):
        """ Callback for exiting/closing plugin window

        Deletes points and relevant figure data before closing

        Args:
            event: qt close event (passed via signal)

        """
        while len(self.points) > 0:
            self.on_remove_point()

        event.accept()

    def _get_point_channel_data(self, point_name, channel_name):
        """ Helper function for accessing channel data in point

        Args:
            point_name (str): key for point in points dictionary
            channel_name (str): name of channel within point

        Returns:
            channel_data (ndarray): image data for given point's given channel

        """
        return self.points[point_name].get_channel_data(chans=[channel_name])[channel_name]

    def on_add_point(self):
        """ Callback for Add Point button

        Checks for point existence and adds it to loadingPointsList
        """
        point_path = QtWidgets.QFileDialog.getExistingDirectory(self,
                                                                'Open',
                                                                '~')
        # scan directory for tifs and build channel select
        if point_path:
            tifs = os.listdir(point_path)
            tifs = [tif
                    for tif in tifs
                    if tif.split('.')[-1] in ['tif', 'tiff']]

            # add point to point container if it qualifies
            # this syntax is confusing... :/
            if (
                tifs
                and not self.loadingPointsList.findItems(
                    point_path,
                    QtCore.Qt.MatchExactly
                )
            ):
                self.points[point_path] = Point(point_path, tifs)
                self.loadingPointsList.addItem(point_path)

    def on_point_change(self, current, previous):
        """ Callback for changing point selection in point list

        Reset's channel selection box options, updates plots, and refills
        parameter tables using saved points data

        Args:
            current: newly selected point
            previous: previously selected point

        """

        if current is None:
            return

        # set combo box
        comboChannel = self.loadingChannelSelect.currentText()
        self.loadingChannelSelect.clear()
        if comboChannel in self.points[current.text()].channels:
            self.loadingChannelSelect.addItem(comboChannel)
            self.loadingChannelSelect.addItems(
                [channel
                 for channel in self.points[current.text()].channels
                 if channel != comboChannel]
            )
        else:
            self.loadingChannelSelect.addItems(
                self.points[current.text()].channels
            )

        # gen/update plots
        newChannel = self.loadingChannelSelect.currentText()
        channel_data = self._get_point_channel_data(current.text(), newChannel)
        if self.preview_id is not None and self.loadingReuseButton.isChecked():
            self.points[previous.text()].remove_figure_id(self.preview_id)
            self.points[current.text()].add_figure_id(self.preview_id)

            self.main_viewer.figures.update_figure(self.preview_id,
                                                   ImagePlot(channel_data))
        # only make a plot here if no preview_id is set
        # otherwise, two plots are generated (one here and one in channel change call)
        elif self.preview_id is None:
            self.preview_id = self.main_viewer.figures.add_figure(ImagePlot(channel_data))
            self.points[current.text()].add_figure_id(self.preview_id)

        # swap br_reuse_id ownership if relevant
        if(
            self.br_reuse_id is not None
            and self.points[current.text()].get_param('BR_params') is not None
            and self.rparamsReuseButton.isChecked()
        ):
            self.points[previous.text()].remove_figure_id(self.br_reuse_id)
            self.points[current.text()].add_figure_id(self.br_reuse_id)
            # figure update happens in channel change call

        # refill rparamsTable
        while self.rparamsTable.rowCount() > 0:
            self.rparamsTable.removeRow(self.rparamsTable.rowCount()-1)
        for br_params in (self.points[current.text()].get_param('BR_params') or []):
            new_row = self.rparamsTable.rowCount()
            self.rparamsTable.insertRow(new_row)
            self.rparamsTable.setItem(new_row,
                                      0,
                                      QtWidgets.QTableWidgetItem(f'{br_params[0]}'))
            self.rparamsTable.setItem(new_row,
                                      1,
                                      QtWidgets.QTableWidgetItem(f'{br_params[1]}'))
            self.rparamsTable.setItem(new_row,
                                      2,
                                      QtWidgets.QTableWidgetItem(f'{br_params[2]}'))

        self.main_viewer.refresh_plots()

    def on_channel_change(self, current_text):
        """ Callback for background channel reselection

        Refreshes plots w/ new background channel

        Args:
            current_text: current name of channel selected

        """

        if current_text:

            # get channel_data
            current_point = self.loadingPointsList.currentItem().text()
            channel_data = self._get_point_channel_data(current_point, current_text)

            # update preview
            if self.preview_id is not None and self.loadingReuseButton.isChecked():
                self.main_viewer.figures.update_figure(self.preview_id,
                                                       ImagePlot(channel_data))
            elif self.preview_id is not None:
                self.preview_id = self.main_viewer.figures.add_figure(ImagePlot(channel_data))
                self.points[current_point].add_figure_id(self.preview_id)

            # update background mask figure
            if (
                self.br_reuse_id is not None
                and self.points[current_point].get_param('BR_params') is not None
            ):
                br_params = self.points[current_point].get_param('BR_params')[0]
                channel_mask = self._generate_mask(
                    channel_data,
                    *br_params
                )
                if self.rparamsReuseButton.isChecked():
                    self.main_viewer.figures.update_figure(self.br_reuse_id,
                                                           ImagePlot(channel_mask))
                else:
                    self.br_reuse_id = self.main_viewer.figures.add_figure(
                        ImagePlot(channel_mask)
                    )

            # refresh plots
            self.main_viewer.refresh_plots()

    def on_remove_point(self):
        """ Callback for Remove Point button

        Removes point from list and clears its associated figures

        """

        if self.loadingPointsList.currentItem():
            # get current point key value
            current_point = self.loadingPointsList.currentItem().text()

            # remove all of current point's figure ids
            if self.main_viewer.figures.remove_figures(
                self.points[current_point].figure_ids
            ):
                print('Figures successfully removed')
            else:
                # this indicates a problem w/ either figure manager
                # or untracked figure-point ownerships/associations
                print('Some figures could not be located for removal')

            # clear figure id's if they're associated with the removed point
            if self.preview_id in self.points[current_point].figure_ids:
                self.preview_id = None
            if self.br_reuse_id in self.points[current_point].figure_ids:
                self.br_reuse_id = None

            # directly remove the point from the dictionary
            del self.points[current_point]

            # remove point from point list
            self.loadingPointsList.takeItem(
                self.loadingPointsList.currentRow()
            )

        else:
            print('No points are currently loaded...')

    def _generate_mask(self, background_image, radius, threshold, backcap):
        """ Mask generation algorithm

        Generates binaraized mask used for background removal

        Args:
            background_image (ndarray): background channel to create mask with (const)
            radius (float): radius of gaussian blur
            theshold (float): binarization threshold post-bluring
            backcap (int): maximum pixel value pre-bluring

        Returns:
            background_mask (ndarray): generated binarized mask

        """

        # generate new array
        background_mask = np.zeros_like(background_image)

        # apply cap
        background_mask[background_image > backcap] = backcap

        # apply blur
        background_mask = gaussian_filter(background_mask, radius)

        # mat2gray
        background_mask = np.interp(background_mask,
                                    (background_mask.min(),
                                     background_mask.max()),
                                    (0, 1))

        # thresh
        background_mask = np.where(background_mask > threshold, 1, 0)

        return background_mask

    def test_br_params(self):
        """ Callback for background removal 'test' button

        Generates background mask with current parameters, plots it,
        adds parameters to parameter table, and stores relevent data
        within the selected 'Point' object.

        """

        if self.loadingPointsList.currentItem() is None:
            return

        # get point information
        current_point = self.loadingPointsList.currentItem().text()
        current_channel = self.loadingChannelSelect.currentText()
        background_image = self._get_point_channel_data(current_point, current_channel)

        # get alg params
        radius = self.rparamsGausRadiusBox.value()
        threshold = self.rparamsThreshBox.value()
        backcap = self.rparamsBackCapBox.value()

        # generate mask
        background_mask = self._generate_mask(
            background_image,
            radius,
            threshold,
            backcap
        )

        # generate plot object for mask and create figure
        im_plot = ImagePlot(background_mask)
        if self.br_reuse_id is not None and self.rparamsReuseButton.isChecked():
            if self.br_reuse_id not in self.points[current_point].figure_ids:
                for point in self.points.values():
                    point.safe_remove_figure_id(self.br_reuse_id)
                self.points[current_point].add_figure_id(self.br_reuse_id)
            self.main_viewer.figures.update_figure(self.br_reuse_id, im_plot)
        else:
            self.br_reuse_id = self.main_viewer.figures.add_figure(im_plot)
            self.points[current_point].add_figure_id(self.br_reuse_id)

        # get next row and add data to points for storage
        new_row = self.rparamsTable.rowCount()
        params = self.points[current_point].get_param('BR_params')
        params = list() if not params else params
        params.append([radius, threshold, backcap])
        self.points[current_point].set_param('BR_params', params)

        # add data to rparamsTable
        self.rparamsTable.insertRow(new_row)
        self.rparamsTable.setItem(new_row,
                                  0,
                                  QtWidgets.QTableWidgetItem(f'{radius}'))
        self.rparamsTable.setItem(new_row,
                                  1,
                                  QtWidgets.QTableWidgetItem(f'{threshold}'))
        self.rparamsTable.setItem(new_row,
                                  2,
                                  QtWidgets.QTableWidgetItem(f'{backcap}'))

        self.main_viewer.refresh_plots()


# function for amp plugin building
def build_as_plugin(main_viewer):
    """ Returns an instance of BackgroundRemoval

    This function is common to all plugins; it allows the plugin loader
    to correctly load the plugin.

    Args:
        main_viewer: reference to the main window

    """
    return BackgroundRemoval(main_viewer)
