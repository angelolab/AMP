# start custom imports - DO NOT MANUALLY EDIT BELOW
# end custom imports - DO NOT MANUALLY EDIT ABOVE
from PyQt5 import QtWidgets, QtCore, uic

from amp.mplwidget import ImagePlot, Plot
from amp.point import Point
from amp.main_viewer import MainViewer
from amp.resource_path import resource_path

import numpy as np
from scipy.ndimage import gaussian_filter
from PIL import Image

import os
import pathlib
import concurrent.futures
from datetime import datetime

from typing import Dict, List, Any, Union, Tuple
import numbers


class BackgroundRemoval(QtWidgets.QMainWindow):

    def __init__(self, main_viewer: MainViewer, ui_path: str):
        # start typedef - DO NOT MANUALLY EDIT BELOW
        self.statusbar: QtWidgets.QStatusBar
        self.menubar: QtWidgets.QMenuBar
        self.runEvalCapVal: QtWidgets.QLabel
        self.label_9: QtWidgets.QLabel
        self.runRemoveVal: QtWidgets.QLabel
        self.label_14: QtWidgets.QLabel
        self.runBackCapVal: QtWidgets.QLabel
        self.label_12: QtWidgets.QLabel
        self.runThreshVal: QtWidgets.QLabel
        self.label_10: QtWidgets.QLabel
        self.runGausRadiusVal: QtWidgets.QLabel
        self.label_8: QtWidgets.QLabel
        self.runBackgroundButton: QtWidgets.QPushButton
        self.runLoadButton: QtWidgets.QPushButton
        self.runGroup: QtWidgets.QGroupBox
        self.eparamsTable: QtWidgets.QTableWidget
        self.eparamsEvalAllButton: QtWidgets.QPushButton
        self.eparamsEvalButton: QtWidgets.QPushButton
        self.eparamsEvalCapBox: QtWidgets.QDoubleSpinBox
        self.label_7: QtWidgets.QLabel
        self.eparamsRemoveBox: QtWidgets.QDoubleSpinBox
        self.label_6: QtWidgets.QLabel
        self.eparamsPointSelect: QtWidgets.QComboBox
        self.label_5: QtWidgets.QLabel
        self.label_4: QtWidgets.QLabel
        self.eparamsChannelSelect: QtWidgets.QComboBox
        self.eparamsReloadButton: QtWidgets.QPushButton
        self.eparamsDeleteButton: QtWidgets.QPushButton
        self.eparamsGroup: QtWidgets.QGroupBox
        self.rparamsReloadButton: QtWidgets.QPushButton
        self.rparamsDeleteButton: QtWidgets.QPushButton
        self.rparamsTable: QtWidgets.QTableWidget
        self.rparamsReuseButton: QtWidgets.QRadioButton
        self.rparamsTestButton: QtWidgets.QPushButton
        self.rparamsGausRadiusBox: QtWidgets.QDoubleSpinBox
        self.label_2: QtWidgets.QLabel
        self.label_3: QtWidgets.QLabel
        self.rparamsBackCapBox: QtWidgets.QDoubleSpinBox
        self.label: QtWidgets.QLabel
        self.rparamsThreshBox: QtWidgets.QDoubleSpinBox
        self.rparamsGroup: QtWidgets.QGroupBox
        self.loadingReuseButton: QtWidgets.QRadioButton
        self.loadingPointsList: QtWidgets.QListWidget
        self.loadingChannelSelect: QtWidgets.QComboBox
        self.loadingRemoveButton: QtWidgets.QPushButton
        self.loadingAddButton: QtWidgets.QPushButton
        self.loadingGroup: QtWidgets.QGroupBox
        self.centralwidget: QtWidgets.QWidget
        # end typedef - DO NOT MANUALLY EDIT ABOVE

        super().__init__()

        # set reference to main window
        self.main_viewer = main_viewer

        # points dict (indexed by path)
        self.points: Dict[str, Point] = {}

        # reusable figure id's
        self.preview_id: int = None
        self.br_reuse_id: int = None

        # load ui elements into MainViewer class
        uic.loadUi(
            ui_path,
            self
        )

        # General UI threadpool (probably shouldn't use this for big algos)
        self.executer = concurrent.futures.ThreadPoolExecutor(max_workers=1)

        # connect UI callbacks
        self.loadingAddButton.clicked.connect(self.on_add_point)
        self.loadingPointsList.currentItemChanged.connect(self.on_point_change)
        self.loadingChannelSelect.currentTextChanged.connect(self.on_channel_change)
        self.loadingRemoveButton.clicked.connect(self.on_remove_point)

        # background mask generation UI callbacks
        self.rparamsTestButton.clicked.connect(self.test_br_params)
        self.rparamsDeleteButton.clicked.connect(self.remove_br_params)
        self.rparamsReloadButton.clicked.connect(self.reload_br_params)

        # arrow key + click support for mask generation params table
        self.rparamsTable.cellClicked.connect(self.br_cell_click)
        self.rparamsTable.currentCellChanged.connect(self.br_cell_change)

        # removal evaluation UI callbacks
        self.eparamsPointSelect.currentTextChanged.connect(self.on_eparams_point_change)
        self.eparamsEvalButton.clicked.connect(self.on_eval_click)
        self.eparamsEvalAllButton.clicked.connect(self.on_eval_all_click)
        self.eparamsDeleteButton.clicked.connect(self.remove_ev_params)
        self.eparamsReloadButton.clicked.connect(self.reload_ev_params)

        # arrow key + click support for removal evaluation params table
        # self.eparamsTable.cellClicked.connect()
        # self.eparamsTable.currentCellChanged.connect()

        self.runLoadButton.clicked.connect(self.on_load_params)
        self.runBackgroundButton.clicked.connect(self.on_run_background)

        self.loaded_params = {}

        self.setWindowTitle("Background Removal")

    # closeEvent is reserved by pyqt so it can't follow style guide :/
    def closeEvent(self, event: QtCore.QEvent) -> None:
        """ Callback for exiting/closing plugin window

        Deletes points and relevant figure data before closing

        Args:
            event (QtCore.QEvent): qt close event (passed via signal)
        """

        while len(self.points) > 0:
            self.on_remove_point()

        event.accept()

    # TODO: Change Any's to np.ndarray when numpy 1.20 is released
    def _get_point_channel_data(self, point_name: str, channel_name: str) -> Any:
        """ Helper function for accessing channel data in point

        Args:
            point_name (str): key for point in points dictionary
            channel_name (str): name of channel within point

        Returns:
            channel_data (numpy.ndarray): image data for given point's given channel
        """

        return self.points[point_name].get_channel_data(chans=[channel_name])[channel_name]

    def on_add_point(self) -> None:
        """ Callback for Add Point button

        Checks for point existence and adds it to loadingPointsList
        """

        # point_path = QtWidgets.QFileDialog.getExistingDirectory(self,
        #                                                         'Open',
        #                                                         '~')

        # alter file_dialog to make it possible to select multiple directories
        paths = []

        file_dialog = QtWidgets.QFileDialog()
        file_dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
        file_dialog.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, True)
        file_view = file_dialog.findChild(QtWidgets.QListView, 'listView')

        if file_view:
            file_view.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        f_tree_view = file_dialog.findChild(QtWidgets.QTreeView)
        if f_tree_view:
            f_tree_view.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)

        if file_dialog.exec():
            paths = file_dialog.selectedFiles()

        # iterate over selected points
        for point in paths:
            point_name = pathlib.Path(point).name
            print(f'{point_name}: {point}')

            # find tif subdir (allow only one extra tif depth)
            tif_subdir = None
            for subdir in os.listdir(point):
                subdir_path = os.path.join(point, subdir)
                if (
                    os.path.isdir(subdir_path)
                    and any(['.tif' in f for f in os.listdir(subdir_path)])
                ):
                    tif_subdir = subdir_path
                    break

            if tif_subdir is None:
                print(f'{point_name} didn\'t contain any TIF subdirectories')
                continue

            tifs = os.listdir(tif_subdir)
            tifs = [tif
                    for tif in tifs
                    if tif.split('.')[-1] in ['tif', 'tiff']]

            if (
                tifs
                and not self.loadingPointsList.findItems(
                    point,
                    QtCore.Qt.MatchExactly
                )
            ):
                self.points[point_name] = Point(point_name, tif_subdir, tifs)
                self.loadingPointsList.addItem(point_name)
                self.eparamsPointSelect.addItem(point_name)

    def _gen_preview_fig_name(self, point_name: str, channel_name: str) -> str:
        """Generates pretty figure names for preview images

        Args:
            point_name (str):
                Path like string to TIFs directory of FOV
            channel_name (str):
                Name of channel (with or without .tif(f))

        Returns:
            str:
                Pretty figure name for background image
        """

        reduced_channel_name = channel_name.split('.')[0]
        return f"{point_name} channel {reduced_channel_name}"

    def _gen_mask_fig_name(self, point_name: str, channel_name: str,
                           br_params: List[numbers.Number]) -> str:
        """Generates pretty figure names for background mask images

        Args:
            point_name (str):
                Path like string to TIFs directory of FOV
            channel_name (str):
                Name of channel (with or without .tif(f))
            br_pararms (list):
                Parameters used for mask generation

        Returns:
            str:
                Pretty figure name for background mask image
        """

        reduced_channel_name = channel_name.split('.')[0]
        return f"{point_name} channel {reduced_channel_name} mask {br_params}"

    def _gen_eval_fig_names(self, point_name: str, eval_channel: str,
                            params: List[numbers.Number]) -> Tuple[str, str]:
        """Generates pretty figure names for before/after evaluation images

        Args:
            point_name (str):
                Path like string to TIFs directory of FOV
            eval_channel (str):
                Name of channel (with or without .tif(f))
            params (list):
                Parameters used for mask generation

        Returns:
            Tuple[str, str]:
                Before and after names for figures
        """

        reduced_channel_name = eval_channel.split('.')[0]
        return f"{point_name} - {reduced_channel_name} Before", \
               f"{point_name} - {reduced_channel_name} After {params}"

    def _add_update_figure(self, figure_id: Union[int, None], current_point: str, im_plot: Plot,
                           plot_name: str,
                           reuse_button: QtWidgets.QRadioButton = None) -> int:
        """Adds or updates a figure id with supplied plot object

        Args:
            figure_id (int):
                Previous figure id.  If None, a new figure id will be retrieved from figure manager
            current_point (str):
                Key for current point in points dictionary
            im_plot (mplwidget.Plot):
                Image plot object for the new/updated figure
            plot_name (str):
                Name displayed in the plot list for the figure.
            reuse_button (QtWidgets.QRadioButton | None):
                Button which determines 'reuse' or updating behavior between different points.
                If None, figures will be exclusively added w/o updating. Default is None.

        Returns:
            int:
                New/updated figure id for generated figure.
        """
        is_checked = False
        if reuse_button is not None:
            is_checked = reuse_button.isChecked()

        if figure_id is not None and is_checked:
            if figure_id not in self.points[current_point].figure_ids:
                for point in self.points.values():
                    point.safe_remove_figure_id(figure_id)
                self.points[current_point].add_figure_id(figure_id)
            self.main_viewer.figures.update_figure(figure_id, im_plot, plot_name)
        else:
            figure_id = self.main_viewer.figures.add_figure(im_plot, plot_name)
            self.points[current_point].add_figure_id(figure_id)
        return figure_id

    def on_point_change(self, current: QtWidgets.QListWidgetItem,
                        previous: QtWidgets.QListWidgetItem) -> None:
        """ Callback for changing point selection in point list

        Reset's channel selection box options, updates plots, and refills
        parameter tables using saved points data

        Args:
            current: newly selected point
            previous: previously selected point
        """

        if current is None:
            # unset set combo box
            self.loadingChannelSelect.clear()
            return

        # set channels combo box
        comboChannel = self.loadingChannelSelect.currentText()
        self.loadingChannelSelect.clear()
        if comboChannel in self.points[current.text()].get_channel_names():
            self.loadingChannelSelect.addItem(comboChannel)
            self.loadingChannelSelect.addItems(
                [channel
                 for channel in self.points[current.text()].get_channel_names()
                 if channel != comboChannel]
            )
        else:
            self.loadingChannelSelect.addItems(
                self.points[current.text()].get_channel_names()
            )

        # gen/update plots
        new_channel = self.loadingChannelSelect.currentText()

        channel_data = self._get_point_channel_data(current.text(), new_channel)

        plot_name = self._gen_preview_fig_name(current.text(), new_channel)

        self.preview_id = self._add_update_figure(self.preview_id, current.text(),
                                                  ImagePlot(channel_data), plot_name,
                                                  self.loadingReuseButton)

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

    def on_channel_change(self, current_text: str) -> None:
        """ Callback for background channel reselection

        Refreshes plots w/ new background channel

        Args:
            current_text: current name of channel selected
        """

        if current_text and self.loadingPointsList.currentItem() is not None:

            # get channel_data
            current_point = self.loadingPointsList.currentItem().text()
            channel_data = self._get_point_channel_data(current_point, current_text)
            preview_name = self._gen_preview_fig_name(current_point, current_text)

            # update preview
            self.preview_id = self._add_update_figure(self.preview_id, current_point,
                                                      ImagePlot(channel_data), preview_name,
                                                      self.loadingReuseButton)

            # update background mask figure
            if self.points[current_point].get_param('BR_params'):
                br_params = self.points[current_point].get_param('BR_params')[0]
                mask_name = self._gen_mask_fig_name(current_point, current_text, br_params)
                channel_mask = self._generate_mask(channel_data, *br_params)

                self.br_reuse_id = self._add_update_figure(self.br_reuse_id, current_point,
                                                           ImagePlot(channel_mask), mask_name,
                                                           self.rparamsReuseButton)

            # refresh plots
            self.main_viewer.refresh_plots()

    def on_remove_point(self) -> None:
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

            # clear rparamsTable entries:
            while self.rparamsTable.rowCount() > 0:
                self.rparamsTable.removeRow(self.rparamsTable.rowCount()-1)

            # clear eparamsTable entries
            while self.eparamsTable.rowCount() > 0:
                self.eparamsTable.removeRow(self.eparamsTable.rowCount() - 1)

            # directly remove the point from the dictionary
            del self.points[current_point]

            # remove point from point list
            self.loadingPointsList.takeItem(
                self.loadingPointsList.currentRow()
            )

            self.eparamsPointSelect.removeItem(
                self.eparamsPointSelect.findText(current_point)
            )

        else:
            print('No points are currently loaded...')

    def _generate_mask(self, background_image: Any, radius: float, threshold: float,
                       backcap: int) -> Any:
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

    def test_br_params(self) -> None:
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
        mask_name = \
            self._gen_mask_fig_name(current_point, current_channel, [radius, threshold, backcap])

        im_plot = ImagePlot(background_mask)
        self.br_reuse_id = self._add_update_figure(self.br_reuse_id, current_point, im_plot,
                                                   mask_name, self.rparamsReuseButton)

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

    def br_cell_click(self, row: int, column: int) -> None:
        """Callback for item selection in background removal parameters.

        Ensures entire row is selected (mostly for visual appeal) and generates mask for selected
        parameters.

        TODO: Cache previous results ?

        Args:
            row (int):
                row of cell clicked
            columns (int):
                column of cell clicked
        """

        # full row highlighting
        self.rparamsTable.setRangeSelected(
            QtWidgets.QTableWidgetSelectionRange(row, 0, row, 2),
            True
        )

        # get attributes
        current_point = self.loadingPointsList.currentItem().text()
        current_channel = self.loadingChannelSelect.currentText()
        background_image = self._get_point_channel_data(current_point, current_channel)

        params = self.points[current_point].get_param('BR_params')[row]

        # generate mask
        background_mask = self._generate_mask(
            background_image,
            *params
        )

        # generate plot object for mask and create figure
        mask_name = \
            self._gen_mask_fig_name(current_point, current_channel, params)

        im_plot = ImagePlot(background_mask)

        self.br_reuse_id = self._add_update_figure(self.br_reuse_id, current_point, im_plot,
                                                   mask_name, self.rparamsReuseButton)

        self.main_viewer.refresh_plots()

    def br_cell_change(self, new_row: int, new_col: int, old_row: int, old_col: int) -> None:
        """Callback for arrow key selection support in background reduction params table

        Basic wrapper for `br_cell_click`

        Args:
            new_row (int): Row of new current cell selected.
            new_col (int): Column of new current cell selected.
            old_row (int): Row of old current cell selected. Unused.
            old_col (int): Column of new current cell selected. Unused.
        """

        # adjust for mismatched cell_change call on param deletion
        current_point = self.loadingPointsList.currentItem().text()
        num_br_params = len(self.points[current_point].get_param('BR_params') or [])

        if new_row >= 0:
            self.br_cell_click(
                new_row - int(self.rparamsTable.rowCount() != num_br_params),
                new_col
            )

    def remove_br_params(self) -> None:
        """Callback for background reduction parameter row deletion
        """

        if self.rparamsTable.currentRow() >= 0:

            # get attributes
            current_point = self.loadingPointsList.currentItem().text()

            # delete data from points
            br_params = self.points[current_point].get_param('BR_params')
            del br_params[self.rparamsTable.currentRow()]

            # remove row from column
            self.rparamsTable.removeRow(self.rparamsTable.currentRow())

    def reload_br_params(self) -> None:
        """Callback for filling param boxes with row of background reduction parameters
        """

        if self.rparamsTable.currentRow() >= 0:
            current_row = self.rparamsTable.currentRow()

            self.rparamsGausRadiusBox.setValue(
                float(self.rparamsTable.item(current_row, 0).text())
            )
            self.rparamsThreshBox.setValue(
                float(self.rparamsTable.item(current_row, 1).text())
            )
            self.rparamsBackCapBox.setValue(
                float(self.rparamsTable.item(current_row, 2).text())
            )

    def on_eparams_point_change(self, current_text: str) -> None:
        """Callback function for evaluation point reselection

        Args:
            current_text (str):
                key for to points dictionary
        """

        if not current_text:
            return

        # refresh eparams channels
        combo_channel = None
        if self.eparamsChannelSelect.count() > 0:
            combo_channel = self.eparamsChannelSelect.currentText()
            self.eparamsChannelSelect.clear()
        self.eparamsChannelSelect.addItems(self.points[current_text].get_channel_names())
        if combo_channel is not None and combo_channel:
            self.eparamsChannelSelect.setCurrentText(combo_channel)

        # refresh eparams table
        while self.eparamsTable.rowCount() > 0:
            self.eparamsTable.removeRow(self.eparamsTable.rowCount()-1)
        for ev_params in (self.points[current_text].get_param('EV_params') or []):
            new_row = self.eparamsTable.rowCount()
            self.eparamsTable.insertRow(new_row)
            self.eparamsTable.setItem(new_row,
                                      0,
                                      QtWidgets.QTableWidgetItem(f'{ev_params[0]}'))
            self.eparamsTable.setItem(new_row,
                                      1,
                                      QtWidgets.QTableWidgetItem(f'{ev_params[1]}'))

    def _evaluate_channel(self, bg_channel: Any, eval_channel: Any, radius: float,
                          threshold: float, backcap: int, remove_value: int) -> Any:
        """Generate mask and subtract from evaluation channel where the mask is positive

        Args:
            bg_channel (numpy.ndarray):
                Background channel data
            eval_channel (numpy.ndarray):
                Evaluation channel data
            radius (float):
                Radius of gaussian blur used in mask generation
            threshold (float):
                Threshold used in mask generation
            backcap (int):
                Background cap used in mask generation
            remove_value (int):
                Amount subtracted from evaluation channel

        Returns:
            numpy.ndarray:
                Evaluation channel with pixels dimmed/removed in masked region
        """

        bg_mask = self._generate_mask(bg_channel, radius, threshold, backcap)

        return self._evaluate_channel_with_mask(bg_mask, eval_channel, remove_value)

    def _evaluate_channel_with_mask(self, bg_mask: Any, eval_channel: Any,
                                    remove_value: int) -> Any:
        """Subtract mask from evaluation channel where mask is positive

        Args:
            bg_mask (numpy.ndarray):
                Binarized background channel mask
            eval_channel (numpy.ndarray):
                Evaluation channel data
            remove_value (int):
                Amount subtracted from evaluation channel

        Returns:
            numpy.ndarray:
                Evaluation channel with pixels dimmed/removed in masked region
        """

        processed_channel = np.copy(eval_channel).astype('int')
        processed_channel[bg_mask.astype('bool')] -= int(remove_value)
        processed_channel[processed_channel < 0] = 0

        return processed_channel

    def on_eval_click(self) -> None:
        """Callback function for evaluation button
        """

        if not self.eparamsPointSelect.currentText():
            return

        eval_point = self.eparamsPointSelect.currentText()
        eval_channel = self.eparamsChannelSelect.currentText()
        bg_channel = self.loadingChannelSelect.currentText()

        # get relevant parameters
        radius = self.rparamsGausRadiusBox.value()
        threshold = self.rparamsThreshBox.value()
        backcap = self.rparamsBackCapBox.value()
        remove_value = self.eparamsRemoveBox.value()

        before_name, after_name = \
            self._gen_eval_fig_names(eval_point, eval_channel,
                                     [radius, threshold, backcap, remove_value])

        eval_cap = self.eparamsEvalCapBox.value()

        channel_data = self.points[eval_point].get_channel_data([eval_channel, bg_channel])

        unprocessed_channel = np.copy(channel_data[eval_channel].astype('int'))
        unprocessed_channel[unprocessed_channel > eval_cap] = eval_cap

        # get preview image for before and plot
        self._add_update_figure(None, eval_point, ImagePlot(unprocessed_channel), before_name)

        processed_channel = self._evaluate_channel(
            channel_data[bg_channel],
            channel_data[eval_channel],
            radius,
            threshold,
            backcap,
            remove_value
        )

        # show after image as different plot
        processed_channel[processed_channel > eval_cap] = eval_cap
        self._add_update_figure(None, eval_point, ImagePlot(processed_channel), after_name)

        # get next row and add data to points for storage
        new_row = self.eparamsTable.rowCount()
        params = self.points[eval_point].get_param('EV_params')
        params = list() if not params else params
        params.append([remove_value, eval_cap])
        self.points[eval_point].set_param('EV_params', params)

        # add data to rparamsTable
        self.eparamsTable.insertRow(new_row)
        self.eparamsTable.setItem(new_row,
                                  0,
                                  QtWidgets.QTableWidgetItem(f'{remove_value}'))
        self.eparamsTable.setItem(new_row,
                                  1,
                                  QtWidgets.QTableWidgetItem(f'{eval_cap}'))

    def on_eval_all_click(self) -> None:
        """Callback function for evaluate all button.  Runs evaluation over all loaded points
        """

        # get fixed chanels
        eval_channel = self.eparamsChannelSelect.currentText()
        bg_channel = self.loadingChannelSelect.currentText()

        # get relevant parameters
        radius = self.rparamsGausRadiusBox.value()
        threshold = self.rparamsThreshBox.value()
        backcap = self.rparamsBackCapBox.value()
        remove_value = self.eparamsRemoveBox.value()

        eval_cap = self.eparamsEvalCapBox.value()

        for index in range(self.eparamsPointSelect.count()):
            eval_point = self.eparamsPointSelect.itemText(index)

            before_name, after_name = \
                self._gen_eval_fig_names(eval_point, eval_channel,
                                         [radius, threshold, backcap, remove_value])

            channel_data = self.points[eval_point].get_channel_data([eval_channel, bg_channel])

            unprocessed_channel = np.copy(channel_data[eval_channel].astype('int'))
            unprocessed_channel[unprocessed_channel > eval_cap] = eval_cap

            # get preview image for before and plot
            self._add_update_figure(None, eval_point, ImagePlot(unprocessed_channel), before_name)

            processed_channel = self._evaluate_channel(
                channel_data[bg_channel],
                channel_data[eval_channel],
                radius,
                threshold,
                backcap,
                remove_value
            )

            # show after image as different plot
            processed_channel[processed_channel > eval_cap] = eval_cap
            self._add_update_figure(None, eval_point, ImagePlot(processed_channel), after_name)

            new_row = self.eparamsTable.rowCount()
            params = self.points[eval_point].get_param('EV_params')
            params = list() if not params else params
            params.append([remove_value, eval_cap])
            self.points[eval_point].set_param('EV_params', params)

            # add data to rparamsTable
            self.eparamsTable.insertRow(new_row)
            self.eparamsTable.setItem(new_row,
                                      0,
                                      QtWidgets.QTableWidgetItem(f'{remove_value}'))
            self.eparamsTable.setItem(new_row,
                                      1,
                                      QtWidgets.QTableWidgetItem(f'{eval_cap}'))

    def remove_ev_params(self) -> None:
        """Callback for delete eval parameter button
        """

        if self.eparamsTable.currentRow() >= 0:
            current_row = self.eparamsTable.currentRow()
            current_point = self.eparamsPointSelect.currentText()

            # delete data from points
            ev_params = self.points[current_point].get_param('EV_params')
            del ev_params[current_row]

            # remove row from column
            self.eparamsTable.removeRow(current_row)

    def reload_ev_params(self) -> None:
        """Callback for reloading eval params into the boxes
        """

        if self.eparamsTable.currentRow() >= 0:
            current_row = self.eparamsTable.currentRow()

            self.eparamsRemoveBox.setValue(
                float(self.eparamsTable.item(current_row, 0).text())
            )
            self.eparamsEvalCapBox.setValue(
                float(self.eparamsTable.item(current_row, 1).text())
            )

    def on_load_params(self) -> None:
        """Load parameters used for full background subtraction run
        """

        self.loaded_params = {
            'radius': self.rparamsGausRadiusBox.value(),
            'threshold': self.rparamsThreshBox.value(),
            'backcap': self.rparamsBackCapBox.value(),
            'remove': self.eparamsRemoveBox.value(),
            'evalcap': self.eparamsEvalCapBox.value(),
        }

        self.runGausRadiusVal.setText(self.rparamsGausRadiusBox.text())
        self.runThreshVal.setText(self.rparamsThreshBox.text())
        self.runBackCapVal.setText(self.rparamsBackCapBox.text())
        self.runRemoveVal.setText(self.eparamsRemoveBox.text())
        self.runEvalCapVal.setText(self.eparamsEvalCapBox.text())

        self.runBackgroundButton.setEnabled(True)

    def on_run_background(self) -> None:
        """Run full background subtraction on all loaded points/channels
        """

        logfile_txt = ""

        bg_channel_name = self.loadingChannelSelect.currentText()
        logfile_txt += f'background channel: {bg_channel_name}\n'

        for param_name, param_value in zip(self.loaded_params.keys(), self.loaded_params.values()):
            logfile_txt += f'{param_name}: {param_value}\n'

        logfile_txt += '\n'

        timestamp = datetime.now().strftime("%b_%d_%y__%H_%M_%S")

        # just to bound extracted_folder
        extracted_folder = os.path.join(
            list(self.points.values())[0].get_top_dir(),
            f'no_background_{timestamp}'
        )

        # loop over all loaded points
        for point in self.points.values():
            top_dir = point.get_top_dir()
            extracted_folder = os.path.join(top_dir, f'no_background_{timestamp}')
            tif_folder = os.path.join(extracted_folder, point.name, 'TIFs')
            pathlib.Path(tif_folder).mkdir(parents=True, exist_ok=True)

            logfile_txt += f'{point.get_point_dir()}\n'

            bg_channel_data = self._get_point_channel_data(point.name, bg_channel_name)

            mask = self._generate_mask(bg_channel_data, self.loaded_params['radius'],
                                       self.loaded_params['threshold'],
                                       self.loaded_params['backcap'])

            for ev_channel_name in point.get_channel_names():
                ev_channel_data = self._get_point_channel_data(point.name, ev_channel_name)

                processed_channel_data = self._evaluate_channel_with_mask(
                    mask,
                    ev_channel_data,
                    self.loaded_params['remove']
                )

                Image.fromarray(processed_channel_data.astype(np.uint8)).save(
                    os.path.join(tif_folder, f'{ev_channel_name}.tif')
                )

        # write log file out
        with open(os.path.join(extracted_folder, f'{timestamp}.log'), 'w') as f:
            f.write(logfile_txt)


# function for amp plugin building
def build_as_plugin(main_viewer: MainViewer, plugin_path: str) -> BackgroundRemoval:
    """ Returns an instance of BackgroundRemoval

    This function is common to all plugins; it allows the plugin loader
    to correctly load the plugin.

    Args:
        main_viewer (MainViewer): reference to the main window
    """

    return BackgroundRemoval(main_viewer, plugin_path)
