# start custom imports - DO NOT MANUALLY EDIT BELOW
# end custom imports - DO NOT MANUALLY EDIT ABOVE
from PyQt5 import QtWidgets, QtCore, uic

from amp.main_viewer import MainViewer
from amp.mplwidget import ImagePlot

import numpy as np
from scipy.ndimage import gaussian_filter

import os
import shutil
import json

from typing import Tuple, List, Dict, Any, Union


class BackgroundRemoval(QtWidgets.QMainWindow):

    def __init__(self, main_viewer: MainViewer, ui_path: str):
        # start typedef - DO NOT MANUALLY EDIT BELOW
        self.statusbar: QtWidgets.QStatusBar
        self.menubar: QtWidgets.QMenuBar
        self.runRemovalButton: QtWidgets.QPushButton
        self.saveSettingsButton: QtWidgets.QPushButton
        self.loadSettingsButton: QtWidgets.QPushButton
        self.splitter_8: QtWidgets.QSplitter
        self.splitter_9: QtWidgets.QSplitter
        self.setAllTargetsButton: QtWidgets.QRadioButton
        self.evalcapSpinBox: QtWidgets.QSpinBox
        self.evalcapSlider: QtWidgets.QSlider
        self.splitter_7: QtWidgets.QSplitter
        self.label_5: QtWidgets.QLabel
        self.layoutWidget_4: QtWidgets.QWidget
        self.removeSpinBox: QtWidgets.QSpinBox
        self.removeSlider: QtWidgets.QSlider
        self.splitter_6: QtWidgets.QSplitter
        self.label_4: QtWidgets.QLabel
        self.layoutWidget_3: QtWidgets.QWidget
        self.splitter_5: QtWidgets.QSplitter
        self.groupBox_2: QtWidgets.QGroupBox
        self.capSpinBox: QtWidgets.QSpinBox
        self.capSlider: QtWidgets.QSlider
        self.splitter_3: QtWidgets.QSplitter
        self.label_3: QtWidgets.QLabel
        self.layoutWidget_2: QtWidgets.QWidget
        self.threshDoubleSpinBox: QtWidgets.QDoubleSpinBox
        self.threshSlider: QtWidgets.QSlider
        self.splitter_2: QtWidgets.QSplitter
        self.label_2: QtWidgets.QLabel
        self.layoutWidget: QtWidgets.QWidget
        self.blurDoubleSpinBox: QtWidgets.QDoubleSpinBox
        self.blurSlider: QtWidgets.QSlider
        self.splitter: QtWidgets.QSplitter
        self.label: QtWidgets.QLabel
        self.layoutWidget_0: QtWidgets.QWidget
        self.splitter_4: QtWidgets.QSplitter
        self.groupBox: QtWidgets.QGroupBox
        self.pointTree: QtWidgets.QTreeWidget
        self.pointTab: QtWidgets.QWidget
        self.tabWidget: QtWidgets.QTabWidget
        self.pointPlotSelect: QtWidgets.QComboBox
        self.label_6: QtWidgets.QLabel
        self.addSourceButton: QtWidgets.QPushButton
        self.sourceSelect: QtWidgets.QComboBox
        self.splitter_10: QtWidgets.QSplitter
        self.label_7: QtWidgets.QLabel
        self.centralwidget: QtWidgets.QWidget
        # end typedef - DO NOT MANUALLY EDIT ABOVE

        super().__init__()

        # set reference to main window
        self.main_viewer = main_viewer

        # load ui elements
        uic.loadUi(
            ui_path,
            self
        )

        # TODO: move this (and channels) into a refresh function (callable by main viewer that way)
        # load point tree from main_viewer into pointTree
        self.pointTree.addTopLevelItem(
            main_viewer.CohortTreeWidget.gen_quickview()
        )

        # TODO: see above
        self.channels: List[str] = main_viewer.CohortTreeWidget.get_channels()
        if self.channels is not None:
            self.sourceSelect.addItems(
                sorted(self.channels)
            )

        # connect callbacks
        self.pointTree.itemChanged.connect(self.on_point_toggle)
        
        # connect sliders and spin boxes
        spin_slider_pairs: List[Tuple[QtWidgets.QSpinBox, QtWidgets.QSlider]] = \
            [
                (self.blurDoubleSpinBox, self.blurSlider),
                (self.threshDoubleSpinBox, self.threshSlider),
                (self.capSpinBox, self.capSlider),
                (self.removeSpinBox, self.removeSlider),
                (self.evalcapSpinBox, self.evalcapSlider),
            ]
        # assumes minimum is always 0
        for spin_box, slider in spin_slider_pairs:
            def spinbox_change(spi=spin_box, sli=slider):
                sli.setValue(
                    round(float(sli.maximum()) * spi.value() / spi.maximum())
                )
                self.refocus_plots()

            def slider_change(x, spi=spin_box, sli=slider) -> None:
                spi.setValue(spi.maximum() * float(x) / float(sli.maximum()))

            spin_box.editingFinished.connect(spinbox_change)
            slider.valueChanged.connect(slider_change)
            slider.sliderReleased.connect(self.refocus_plots)

        # set up source tab callbacks
        self.addSourceButton.clicked.connect(self.on_add_source)

        # add plot point select callback
        self.pointPlotSelect.currentIndexChanged.connect(lambda x: self.refocus_plots())
        self.tabWidget.currentChanged.connect(lambda x: self.refocus_plots())

        # toggle channel settings update mode
        self.set_all_targets = False
        self.setAllTargetsButton.clicked.connect(self.toggle_settings_mode)

        # add settings callbacks
        self.saveSettingsButton.clicked.connect(self.save_settings)
        self.loadSettingsButton.clicked.connect(self.load_settings)

        # add remove background callback
        self.runRemovalButton.clicked.connect(self.remove_background)

        # initialize settings and extract default alg params
        self.settings: Dict[str, Dict[str, Dict]] = {}

        # prevents figure gen during settings load
        self.prevent_plotting: bool = False

        self.figure_ids = {
            'source_preview': None,
            'background_mask': None,
            'target_preview': None,
            'target_no_background': None,
        }

        self.spin_boxes: Dict[str, QtWidgets.QSpinBox] = {
            'blur': self.blurDoubleSpinBox,
            'thresh': self.threshDoubleSpinBox,
            'cap': self.capSpinBox,
            'remove': self.removeSpinBox,
            'evalcap': self.evalcapSpinBox,
        }

        # Use these to determine figure refocus
        self.current_point = None
        self.current_source = None
        self.current_target = None

        # Cache source and target data (prevents needless file reads)
        self.source_data = None
        self.target_data = None

        self.setWindowTitle("Background Removal New")

    # closeEvent is reserved by pyqt so it can't follow style guide :/
    def closeEvent(self, event: QtCore.QEvent) -> None:
        """ Callback for exiting/closing plugin window

        Deletes points and relevant figure data before closing

        Args:
            event (QtCore.QEvent): qt close event (passed via signal)
        """

        event.accept()

    def get_params(self) -> Dict:
        """ Get parameter settings
        """
        return {
            'blur': self.blurDoubleSpinBox.value(),
            'thresh': self.threshDoubleSpinBox.value(),
            'cap': self.capSpinBox.value(),
            'remove': self.removeSpinBox.value(),
            'evalcap': self.evalcapSpinBox.value(),
        }

    def set_params(self, params: Dict) -> None:
        """ Set parameters
        """

        # setting + unsetting focus here to force a call to 'editingFinished'
        for param_name, param_value in params.items():
            # prevents redundant signal chaining
            if self.spin_boxes[param_name].value() == param_value:
                continue
            self.spin_boxes[param_name].setFocus()
            self.spin_boxes[param_name].setValue(param_value)
            self.spin_boxes[param_name].clearFocus()

    def update_figures(self, new_figures: Dict[str, Tuple[str, ImagePlot]]) -> None:
        """Adds or updates relevant figures with supplied plot object

        Args:
            new_figures (Dict[str, (str, mplwidget.ImagePlot)]):
                Map from internal figure names to new plot objects (and name)
        """
        for internal_figure_name, (figure_name, figure_data) in new_figures.items():
            if self.figure_ids.get(internal_figure_name) is not None:
                self.main_viewer.figures.update_figure(
                    self.figure_ids.get(internal_figure_name), figure_data,
                    figure_name
                )
            else:
                self.figure_ids[internal_figure_name] = \
                    self.main_viewer.figures.add_figure(
                        figure_data, figure_name, self.clear_figure_id
                    )
    
        self.main_viewer.refresh_plots()
    
    def clear_figure_id(self, figure_id: int) -> None:
        """ Finds and clears figure id

        Args:
            figure_id (int):
                Figure id to search for
        """
        self.main_viewer.figures.remove_figure(figure_id)
        for stored_name, stored_id in self.figure_ids.items():
            if stored_id == figure_id:
                self.figure_ids[stored_name] = None
                return

    def on_point_toggle(self, item: QtWidgets.QTreeWidgetItem, column: int) -> None:
        """ Callback for toggling point selection

        Adds/removes points to background removal queue

        Args:
            item (QtWidgets.QTreeWidgetItme):
                toggled widget item
            column (int):
                mandatory unused argument in signal
        """
        if item.childCount() == 0:
            # a bit inefficient here (e.g dynamic programming could help)
            treepath = ''
            node = item
            while node is not None:
                treepath = '/' + node.text(0) + treepath
                node = node.parent()
            # remove prepended '/'
            treepath = treepath[1:]

            index = self.pointPlotSelect.findText(treepath)
            if index < 0 and item.checkState(0):
                self.pointPlotSelect.addItem(treepath)
            elif index >= 0 and not item.checkState(0):
                self.pointPlotSelect.removeItem(index)

        else:
            for child in [item.child(index) for index in range(item.childCount())]:
                child.setCheckState(0, item.checkState(0))

    def on_add_source(self) -> None:
        """ Callback for adding new source channel
        """

        # get currently selected channel
        channel = self.sourceSelect.currentText()
        # check if tab already exists!
        if channel not in [self.tabWidget.tabText(t) for t in range(self.tabWidget.count())]:
            # create target channel list
            self.settings[channel] = {}
            self.tabWidget.addTab(self.generate_new_target_list(channel), channel)

    def generate_new_target_list(self, channel: str) -> QtWidgets.QListWidget:
        """ Generates new checkable list of target channels
        
        Args:
            channel (str):
                channel used for callback setting
        """
        target_list = QtWidgets.QListWidget()
        target_list.addItems(self.channels)
        for item in [target_list.item(i) for i in range(len(self.channels))]:
            item.setFlags(item.flags() |
                      QtCore.Qt.ItemIsUserCheckable |
                      QtCore.Qt.ItemIsEnabled)
            item.setCheckState(QtCore.Qt.Unchecked)
        target_list.sortItems(0)

        # define and set callbacks
        def target_list_changed_callback(item: QtWidgets.QListWidgetItem) -> None:
            if self.prevent_plotting:
                return

            if item.checkState():
                # init settings and refocus plots
                self.settings[channel][item.text()] = self.get_params()
                if item.text() != self.current_target or channel != self.current_source:
                    # set item to current
                    item.listWidget().setCurrentItem(item)
                    self.refocus_plots()
                    self.current_target = item.text()
                    self.current_source = channel

            else:
                # clean up removal settings
                self.settings[channel].pop(item.text())
                self.current_target = item.text()
                self.current_source = channel

        # refocus plots if called
        def target_list_clicked_callback(item: QtWidgets.QListWidgetItem, settings=self.settings) -> None:
            if self.prevent_plotting:
                return

            if item.checkState():
                # load settings if they exist
                if channel in settings.keys():
                    if item.text() in settings[channel].keys():
                        self.set_params(settings[channel][item.text()])
                if item.text() != self.current_target or channel != self.current_source:
                    self.refocus_plots()
                    self.current_target = item.text()
                    self.current_source = channel

        target_list.itemChanged.connect(target_list_changed_callback)
        target_list.itemClicked.connect(target_list_clicked_callback)

        return target_list

    def refocus_plots(self) -> None:
        """ Detect point, source channel, and target channel active and replot
        """

        if self.prevent_plotting:
            return

        figure_updates = {}

        # get point
        point_path = self.pointPlotSelect.currentText()
        if point_path == '' or point_path is None:
            return

        source_channel = self.tabWidget.tabText(self.tabWidget.currentIndex())

        if source_channel == 'Points':
            self.current_point = point_path
            return

        # refresh raw source channel plot
        if (point_path != self.current_point 
            or source_channel != self.current_source
            or self.source_data is None):

            self.source_data = self.main_viewer.CohortTreeWidget.get_item(
                f'{point_path}/{source_channel}'
            ).get_image_data()

            figure_updates['source_preview'] = (
                f"{point_path.split('/')[-1]} channel: {source_channel}",
                ImagePlot(self.source_data)
            )

        active_tab: QtWidgets.QListWidget = self.tabWidget.currentWidget()
        target_channel = None
        if active_tab.currentItem() is not None and active_tab.currentItem().checkState():
            target_channel = active_tab.currentItem().text()

        if target_channel == '' or target_channel is None:
            self.update_figures(figure_updates)
            self.current_point = point_path
            return

        # conditionally update source/target parameters
        if source_channel == self.current_source and target_channel == self.current_target:
            if self.set_all_targets:
                params = self.get_params()
                for target in self.settings[source_channel].keys():
                    self.settings[source_channel][target] = params
            else:
                self.settings[source_channel][target_channel] = self.get_params()
        else:
            self.set_params(self.settings[source_channel][target_channel])

        # generate mask
        mask = self._generate_mask(self.source_data)
        figure_updates['background_mask'] = (
            f"{point_path.split('/')[-1]} channel {source_channel} mask {self.get_params()}",
            ImagePlot(mask, fixed_contrast=True)
        )

        # get/refresh target channel plot
        if (target_channel != self.current_target
            or point_path != self.current_point
            or self.target_data is None):

            self.target_data = self.main_viewer.CohortTreeWidget.get_item(
                f'{point_path}/{target_channel}'
            ).get_image_data()
        unprocessed_target, processed_target = self._evaluate_target_views(mask, self.target_data)        

        figure_updates['target_preview'] = (
            f"{point_path.split('/')[-1]} - {target_channel} Before",
            ImagePlot(unprocessed_target, fixed_contrast=True)
        )
        figure_updates['target_no_background'] = (
            f"{point_path.split('/')[-1]} - {target_channel} After {self.get_params()}",
            ImagePlot(processed_target, fixed_contrast=True)
        )

        self.update_figures(figure_updates)

        self.current_point = point_path

    def _generate_mask(self, background_image: Any) -> Any:
        """Generates binaraized mask used for background removal

        Args:
            background_image (ndarray): background channel to create mask with (const)

        Returns:
            background_mask (ndarray): generated binarized mask
        """
        params = self.get_params()

        background_mask = np.zeros_like(background_image)
        background_mask[background_image > params['cap']] = params['cap']
        background_mask = gaussian_filter(background_mask, params['blur'])
        background_mask = np.interp(background_mask,
                                    (background_mask.min(),
                                     background_mask.max()),
                                    (0, 1))
        background_mask = np.where(background_mask > params['thresh'], 1, 0)
        return background_mask

    def _evaluate_target(self, mask: Any, target_data: Any, remove_value: Union[int, None] = None) -> Any:
        """ Subtracts remove value from target image at positive mask values

        Args:
            mask (np.array):
                boolean background mask
            target_data (np.array):
                target channel data
            remove_value (int):
                intensity value to deduct from target

        Returns:
            np.array:
                processed data
        """
        if remove_value is None:
            remove_value = self.get_params()['remove']

        processed_channel = np.copy(target_data).astype('int')
        processed_channel[mask.astype('bool')] -= remove_value
        processed_channel[processed_channel < 0] = 0

        return processed_channel

    def _evaluate_target_views(self, mask: Any, target_data: Any) -> Tuple[Any]:
        """Generates plot views for before/after targets

        Args:
            mask (np.array):
                boolean background mask
            target_data (np.array):
                target channel data

        Returns:
            (np.array, np.array):
                - unprocessed channel view (before)
                - processed channel view (after)
        """
        params = self.get_params()

        unprocessed_channel = np.copy(target_data).astype('int')
        unprocessed_channel[unprocessed_channel > params['evalcap']] = params['evalcap']

        processed_channel = self._evaluate_target(mask, target_data, params['remove'])        
        processed_channel[processed_channel > params['evalcap']] = params['evalcap']

        return unprocessed_channel, processed_channel

    def toggle_settings_mode(self, mode: bool) -> None:
        """ toggles the 'set all targets' option

        Args:
            mode (bool):
                value for 'set all targets' option

        """
        self.set_all_targets = mode        

    def save_settings(self) -> None:
        """ write background removal settings out to json
        """

        settings_dir = self.main_viewer.CohortTreeWidget.topLevelItem(0).path

        with open(os.path.join(settings_dir, 'background_settings.json'), 'w') as fp:
            json.dump(self.settings, fp, indent=4)

    def load_settings(self) -> None:
        """ load settings from json file
        """
        self.prevent_plotting = True

        settings_path = str(QtWidgets.QFileDialog.getOpenFileName(
            self,
            'Load Settings',
            self.main_viewer.CohortTreeWidget.topLevelItem(0).path,
            'JSON files(*.json)'
        )[0])

        with open(os.path.join(settings_path), 'r') as fp:
            new_settings: Dict[str, Dict[str, Dict[str, Any]]] = json.load(fp)

        # TODO: clean settings
        self.settings = new_settings

        # create tabs, check targets as needed
        sources = [self.tabWidget.tabText(i) for i in range(self.tabWidget.count())]
        for source, targets in new_settings.items():
            if source in self.channels:
                tab_index = None
                if source not in sources:
                    # add source
                    tab_index = self.tabWidget.addTab(self.generate_new_target_list(source), source)
                else:
                    tab_index = sources.index(source)
                source_tab: QtWidgets.QListWidget = self.tabWidget.widget(tab_index)
                for target, params in targets.items():
                    if target in self.channels:

                        target_index = [
                            source_tab.item(i).text()
                            for i in range(source_tab.count())].index(target)

                        source_tab.item(target_index).setCheckState(True)

        self.prevent_plotting = False

    def remove_background(self) -> None:
        """ run full background removal on all selected points and save output
        """

        self.prevent_plotting = True

        # copy directory
        src_dir = self.main_viewer.CohortTreeWidget.topLevelItem(0).path
        parent_dir = os.path.dirname(src_dir[:-1])
        tmp_dir = os.path.join(parent_dir, 'bg_removed_temp')
        final_dir = os.path.join(parent_dir, 'background_removed')

        shutil.copytree(src_dir, tmp_dir)

        # loop over all selected points
        points = [self.pointPlotSelect.itemText(i) for i in range(self.pointPlotSelect.count())]
        for point in points:
            # loop over settings
            for source, targets in self.settings.items():
                source_item = self.main_viewer.CohortTreeWidget.get_item(f'{point}/{source}')
                if source_item is None:
                    continue
                source_data = source_item.get_image_data()
                for target, params in targets.items():
                    target_item = self.main_viewer.CohortTreeWidget.get_item(f'{point}/{target}')
                    if target_item is None:
                        continue
                    target_data = target_item.get_image_data()
                    self.set_params(params)
                    mask = self._generate_mask(source_data)
                    target_data_cleaned = self._evaluate_target(mask, target_data)

                    target_item.write_image_data(target_data_cleaned)

        # rename directories
        os.rename(src_dir, final_dir)
        os.rename(tmp_dir, src_dir)

        self.prevent_plotting = False

# function for amp plugin building
def build_as_plugin(main_viewer: MainViewer, plugin_path: str) -> BackgroundRemoval:
    """ Returns an instance of BackgroundRemoval

    This function is common to all plugins; it allows the plugin loader
    to correctly load the plugin.

    Args:
        main_viewer (MainViewer): reference to the main window
    """

    return BackgroundRemoval(main_viewer, plugin_path)
