# start custom imports - DO NOT MANUALLY EDIT BELOW
# end custom imports - DO NOT MANUALLY EDIT ABOVE
from PyQt5 import QtWidgets, QtCore, uic

from amp.main_viewer import MainViewer
from amp.mplwidget import ImagePlot, HistPlot, Plot

import numpy as np
from scipy.stats import gamma
from scipy.optimize import fsolve
from scipy.special import digamma
from scipy.special import gamma as gamma_func
from sklearn.neighbors import NearestNeighbors

import os
import shutil
import json

# TODO: figure out how to import util files
#       one option is to do inject stuff on load
#       not sure what the other options would be :/

from typing import Tuple, List, Dict, Any, Union

def _alpha_eqn(ahat: float, C: float) -> float:
    return np.log(ahat) - digamma(ahat) - C

def _calc_q(x, Ts, ws, alphas, betas):
    param_terms = alphas * np.log(betas) - np.log(gamma_func(alphas)) + np.log(ws)
    combined_terms = (
        (alphas[:, np.newaxis] - 1) * np.log([x,]*alphas.shape[0])
        - betas[:, np.newaxis] * np.array([x, ]* alphas.shape[0])
    )
    return np.sum(Ts * (param_terms[:, np.newaxis] + combined_terms))

def _gamma_mixture(x, n_dists, max_iter, init_index, tol):

    # for a gamma distribution, alpha = mean**2 / var, beta = mean / var
    ws, alphas, betas = (np.zeros(n_dists), np.zeros(n_dists), np.zeros(n_dists))
    dist_pdfs = np.zeros((n_dists, x.shape[0]))
    for i in range(n_dists):
        ws[i] = np.mean(init_index == i)
        alphas[i] = (np.mean(x[init_index == i]) ** 2) / np.var(x[init_index == i])
        betas[i] = np.mean(x[init_index == i]) / np.var(x[init_index == i])
        dist_pdfs[i] = gamma.pdf(x, alphas[i], scale = 1 / betas[i])

    total_dist = np.dot(dist_pdfs.T, ws)

    z_cond_dists = (ws[:, np.newaxis] * dist_pdfs) / total_dist

    for _iter in range(max_iter):

        sum_Ts = np.sum(z_cond_dists, axis=1)
        sum_Txs = np.dot(z_cond_dists, x)
        sum_Tlogxs = np.dot(z_cond_dists, np.log(x))

        alpha_eq_consts = np.log(sum_Txs / sum_Ts) - (sum_Tlogxs / sum_Ts)

        # compute argmax's
        a_hats = np.array([
            fsolve(_alpha_eqn, alphas[i], args=(alpha_eq_consts[i]))[0]
            for i in range(n_dists)
        ])
        b_hats = a_hats * sum_Ts / sum_Txs
        w_hats = sum_Ts / x.shape[0]

        # get next iter distributions
        dist_pdfs_next = np.array([
            gamma.pdf(x, a_hats[i], scale = 1 / b_hats[i])
            for i in range(n_dists)
        ])
        total_dist_next = np.dot(dist_pdfs_next.T, w_hats)
        z_cond_dists_next = (w_hats[:, np.newaxis] * dist_pdfs_next) / total_dist_next

        # compute delta_q
        delta_q = (
            _calc_q(x, z_cond_dists_next, w_hats, a_hats, b_hats)
            - _calc_q(x, z_cond_dists, ws, alphas, betas)
        )

        # update params and distributions
        ws, alphas, betas = (w_hats, a_hats, b_hats)
        dist_pdfs = dist_pdfs_next
        total_dist = total_dist_next
        z_cond_dists = z_cond_dists_next

        if np.abs(delta_q) <= tol:
            break

    return ws, alphas, betas

_INIT_KNN_THRESH = 6

def optimize_threshold(knn_dists):
    # approximate initial distribution assignments
    assignment_guess = np.zeros_like(knn_dists)
    assignment_guess[knn_dists > _INIT_KNN_THRESH] = 1

    w, alpha, beta = _gamma_mixture(knn_dists, 2, 500, assignment_guess, 1e-3)

    means = np.sort(alpha / beta)
    x = np.linspace(means[0], means[1], num=int(10*(means[1] - means[0])))

    dist1 = w[0] * gamma.pdf(x, alpha[0], scale = 1 / beta[0])
    dist2 = w[1] * gamma.pdf(x, alpha[1], scale = 1 / beta[1])

    if len(np.abs(dist1 - dist2)) == 0:
        return _INIT_KNN_THRESH

    return x[np.argmin(np.abs(dist1 - dist2))]

class KnnDenoising(QtWidgets.QMainWindow):

    def __init__(self, main_viewer: MainViewer, ui_path: str):
        # start typedef - DO NOT MANUALLY EDIT BELOW
        self.statusbar: QtWidgets.QStatusBar
        self.menubar: QtWidgets.QMenuBar
        self.runDenoiseButton: QtWidgets.QPushButton
        self.saveSettingsButton: QtWidgets.QPushButton
        self.loadSettingsButton: QtWidgets.QPushButton
        self.splitter_8: QtWidgets.QSplitter
        self.splitter_9: QtWidgets.QSplitter
        self.capSpinBox: QtWidgets.QSpinBox
        self.capSlider: QtWidgets.QSlider
        self.splitter_3: QtWidgets.QSplitter
        self.label_3: QtWidgets.QLabel
        self.threshDoubleSpinBox: QtWidgets.QDoubleSpinBox
        self.threshSlider: QtWidgets.QSlider
        self.splitter: QtWidgets.QSplitter
        self.label: QtWidgets.QLabel
        self.groupBox: QtWidgets.QGroupBox
        self.channelPlotSelect: QtWidgets.QComboBox
        self.label_7: QtWidgets.QLabel
        self.pointPlotSelect: QtWidgets.QComboBox
        self.label_6: QtWidgets.QLabel
        self.optAllButton: QtWidgets.QRadioButton
        self.optThreshButton: QtWidgets.QPushButton
        self.channelList: QtWidgets.QListWidget
        self.channelTab: QtWidgets.QWidget
        self.pointTree: QtWidgets.QTreeWidget
        self.pointTab: QtWidgets.QWidget
        self.tabWidget: QtWidgets.QTabWidget
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

        # Fill channel list (TODO: see above)
        # BONUS TODO: add refocus plot callbacks to all these!!!
        self.channels: List[str] = main_viewer.CohortTreeWidget.get_channels()
        if self.channels is not None:
            self.channelList.addItems(self.channels)
            for channel_row in range(self.channelList.count()):
                channel_item = self.channelList.item(channel_row)
                channel_item.setFlags(channel_item.flags() |
                    QtCore.Qt.ItemIsUserCheckable |
                    QtCore.Qt.ItemIsEnabled)
                channel_item.setCheckState(QtCore.Qt.Unchecked)

        self.pointTree.itemChanged.connect(self.on_point_toggle)
        self.runDenoiseButton.clicked.connect(self.denoise)
        self.saveSettingsButton.clicked.connect(self.save_settings)
        self.loadSettingsButton.clicked.connect(self.load_settings)

        # connect sliders and spin boxes
        spin_slider_pairs: List[Tuple[QtWidgets.QSpinBox, QtWidgets.QSlider]] = \
            [
                (self.threshDoubleSpinBox, self.threshSlider),
                (self.capSpinBox, self.capSlider),
            ]
        # assumes minimum is always 0
        self.replot_on_spinchange = True
        for spin_box, slider in spin_slider_pairs:
            def spinbox_change(spi=spin_box, sli=slider):
                sli.setValue(
                    round(
                        float(sli.maximum()) * (spi.value() - spi.minimum())
                        / (spi.maximum() - spi.minimum())
                    )
                )
                if self.replot_on_spinchange:
                    self.refocus_plots()

            def slider_change(x, spi=spin_box, sli=slider) -> None:
                spi.setValue((
                        (spi.maximum() - spi.minimum())
                        * float(x) / float(sli.maximum())
                    ) + spi.minimum()
                )

            spin_box.editingFinished.connect(spinbox_change)
            slider.valueChanged.connect(slider_change)
            slider.sliderReleased.connect(self.refocus_plots)

        # add plot point select callback
        self.pointPlotSelect.currentIndexChanged.connect(lambda x: self.refocus_plots())

        # set callback for threshold optimizing
        self.optThreshButton.clicked.connect(self.run_knns)

        # initialize settings and extract default alg params
        # settings are per FOV
        self.settings: Dict[str, Dict[str, Dict]] = {}

        # prevents figure gen during settings load
        self.prevent_plotting: bool = False

        self.figure_ids = {
            'target_preview': None,
            'knn_hist': None,
            'target_denoised': None,
        }

        self.spin_boxes: Dict[str, QtWidgets.QSpinBox] = {
            'thresh': self.threshDoubleSpinBox,
            'cap': self.capSpinBox,
        }

        self.current_point = None
        self.current_channel = None

        # Cache source and target data (prevents needless file reads)
        self.channel_data = None
        self.non_zeros = None

        # Store knn mean dist vals
        # Technically these depend on the nonzeros for each image, but that's deterministic
        # and quickly recomputable
        self.knns = {}

        self.setWindowTitle("KNN Denoising")

        # define and set callbacks
        def target_list_changed_callback(item: QtWidgets.QListWidgetItem) -> None:
            if self.prevent_plotting:
                return

            if self.current_point not in self.settings.keys():
                if item.checkState():
                    item.setCheckState(False)

                return

            if item.checkState():
                # init settings and refocus plot
                self.settings[self.current_point][item.text()] = self.get_params()
                if item.text() != self.current_channel:
                    # set item to current
                    item.listWidget().setCurrentItem(item)
                    self.refocus_plots()
                    self.current_channel = item.text()
            else:
                # clean up removal settings
                self.settings[self.current_point].pop(item.text())
                self.current_channel = item.text()

        # refocus plots if called
        def target_list_clicked_callback(item: QtWidgets.QListWidgetItem,
                                         settings=self.settings) -> None:
            if self.prevent_plotting:
                return

            if item.checkState():
                # load settings if they exist
                if self.current_point in settings.keys():
                    if item.text() in settings[self.current_point].keys():
                        self.replot_on_spinchange = False
                        self.set_params(settings[self.current_point][item.text()])
                        self.replot_on_spinchange = True
                if item.text() != self.current_channel:
                    self.refocus_plots()
                    self.current_channel = item.text()

        self.channelList.itemChanged.connect(target_list_changed_callback)
        self.channelList.itemClicked.connect(target_list_clicked_callback)

        # closeEvent is reserved by pyqt so it can't follow style guide :/
    def closeEvent(self, event: QtCore.QEvent) -> None:
        """ Callback for exiting/closing plugin window

        Deletes points and relevant figure data before closing

        Args:
            event (QtCore.QEvent): qt close event (passed via signal)
        """

        event.accept()

    def update_figures(self, new_figures: Dict[str, Tuple[str, Plot]]) -> None:
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

    def get_params(self) -> Dict:
        """ Get parameter settings
        """
        return {
            'thresh': self.threshDoubleSpinBox.value(),
            'cap': self.capSpinBox.value(),
        }

    def set_params(self, params: Dict) -> None:
        """ Set parameters
        """

        # setting + unsetting focus here to force a call to 'editingFinished'
        for param_name, param_value in params.items():
            if param_name not in self.spin_boxes.keys():
                continue
            # prevents redundant signal chaining
            if self.spin_boxes[param_name].value() == param_value:
                continue
            self.spin_boxes[param_name].setFocus()
            self.spin_boxes[param_name].setValue(param_value)
            self.spin_boxes[param_name].clearFocus()


    def refocus_plots(self) -> None:
        """ Detect point and target channel active and replot
        """

        if self.prevent_plotting:
            return

        figure_updates = {}

        # get point
        point_path = self.pointPlotSelect.currentText()
        if point_path == '' or point_path is None:
            return

        target_channel = None
        if self.channelList.currentItem() is None:
            self.current_point = point_path
            if point_path not in self.settings.keys():
                self.settings[point_path] = {}
            return

        if self.channelList.currentItem().checkState():
            target_channel = self.channelList.currentItem().text()

        if target_channel == '' or target_channel is None:
            self.current_point = point_path
            if point_path not in self.settings.keys():
                self.settings[point_path] = {}
            return

        if (point_path != self.current_point
            or target_channel != self.current_channel
            or self.channel_data is None
        ):
            self.channel_data = self.main_viewer.CohortTreeWidget.get_item(
                f'{point_path}/{target_channel}'
            ).get_image_data()

        # update settings if necessary
        recalcs = {
            'thresh': True,
            'kval': False,
            'cap': True,
        }
        if point_path == self.current_point and target_channel == self.current_channel:
            params = self.get_params()
            # loop over keys to avoid overwriting optimized threshold
            # NOTE: checking for what's actually changed here would avoid unecessary recalcs
            for key in params:
                recalcs[key] = (self.settings[point_path][target_channel][key] != params[key])
                self.settings[point_path][target_channel][key] = params[key]
        else:
            self.replot_on_spinchange = False
            self.set_params(self.settings[point_path][target_channel])
            self.replot_on_spinchange = True

        if recalcs['cap']:
            data_preview = self.channel_data.copy()
            data_preview[data_preview > self.get_params()['cap']] = self.get_params()['cap']

            figure_updates['target_preview'] = (
                f"{point_path.split('/')[-1]} channel: {target_channel}",
                ImagePlot(data_preview, fixed_contrast=True)
            )

        # generate mean dist knn
        if point_path in self.knns.keys() and target_channel in self.knns[point_path].keys():
            if recalcs['kval']:
                _, self.knns[point_path][target_channel] = \
                    self._generate_knn(self.channel_data)
                print('recomputing knn :(')

            if recalcs['kval'] or recalcs['thresh']:
                figure_updates['knn_hist'] = (
                    f"{point_path.split('/')[-1]} channel {target_channel} knn hist",
                    HistPlot(
                        self.knns[point_path][target_channel],
                        n_bins=30,
                        thresh=self.settings[point_path][target_channel]['thresh']
                    )
                )

            # filter image using mean dist knn
            if any(recalcs.values()):
                processed_target = self._evaluate_target(
                    np.array(self.channel_data.nonzero()).T,
                    self.knns[point_path][target_channel],
                    self.channel_data
                )

                figure_updates['target_denoised'] = (
                    f"{point_path.split('/')[-1]} - {target_channel} w/ {self.get_params()}",
                    ImagePlot(processed_target, fixed_contrast=True)
                )

        self.update_figures(figure_updates)

        self.current_point = point_path

    def _generate_knn(self, channel_data: Any, k_val: int = 0) -> Any:
        """Generates mean knn distance image for denoising

        Args:
            channel_data (ndarray): channel data used to compute mean knn dist

        Returns:
            tuple: nonzero indicies, generated mean knn distances
        """
        if k_val == 0:
            k_val = self.get_params()['kval']

        non_zeros = np.array(channel_data.nonzero()).T
        nbrs = NearestNeighbors(
            n_neighbors=int(k_val + 1),
            algorithm='kd_tree').fit(non_zeros)

        distances, _ = nbrs.kneighbors(non_zeros)

        knn_mean = np.mean(distances[:, 1:], axis=1)

        return non_zeros, knn_mean

    def _evaluate_target(self, non_zeros: Any, knn: Any, channel_data: Any, cap: bool = True) -> Any:
        """
        """
        params = self.get_params()

        denoised = channel_data.copy()
        bad_inds = non_zeros[knn > params['thresh']].T
        if bad_inds.size > 0:
            denoised[bad_inds[0], bad_inds[1]] = 0
        if cap:
            denoised[denoised > params['cap']] = params['cap']

        return denoised

    # TODO: implement status window
    def run_knns(self) -> None:
        """
        """

        for point in self.settings.keys():
            print(f'running point: {point}')
            if point not in self.knns.keys():
                self.knns[point] = {}
            for i, channel in enumerate(self.settings[point].keys()):
                print(f'    running channel: {channel}  ({i}/{len(self.settings[point].keys())})')
                params = self.settings[point][channel]
                self.channel_data = self.main_viewer.CohortTreeWidget.get_item(
                    f'{point}/{channel}'
                ).get_image_data()

                if channel not in self.knns[point].keys():
                    _, self.knns[point][channel] = \
                        self._generate_knn(self.channel_data, params['kval'])

                if self.optAllButton.isChecked():
                    print(f'        optimizing threshold...')
                    if 'opt_thresh' not in self.settings[point][channel].keys():
                        opt_thresh = optimize_threshold(self.knns[point][channel])
                        self.settings[point][channel]['opt_thresh'] = opt_thresh
                    else:
                        opt_thresh = self.settings[point][channel]['opt_thresh']
                    self.settings[point][channel]['thresh'] = opt_thresh

    def save_settings(self) -> None:
        """ write background removal settings out to json
        """

        settings_dir = self.main_viewer.CohortTreeWidget.topLevelItem(0).path

        with open(os.path.join(settings_dir, 'denoising_settings.json'), 'w') as fp:
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

        # check points as needed
        for point, targets in new_settings.items():
            column = len(point.split('/')) - 1
            tree_item = self.pointTree.findItems(point, QtCore.Qt.MatchExactly, column=column)[0]
            tree_item.setCheckState(0, QtCore.Qt.Checked)

        # reuse last targest iteration to check targets
        for target, params in targets.items():
            if target in self.channels:
                target_index = [
                    self.channelList.item(i).text()
                    for i in range(self.channelList.count())].index(target)
                
                self.channelList.item(target_index).setCheckState(True)

        self.prevent_plotting = False

    def denoise(self) -> None:
        """ run full denoising on all selected points/channels and save output
        """
        self.prevent_plotting = True

        # copy directory
        src_dir = self.main_viewer.CohortTreeWidget.topLevelItem(0).path
        parent_dir = os.path.dirname(src_dir[:-1])
        tmp_dir = os.path.join(parent_dir, 'denoised_temp')
        final_dir = os.path.join(parent_dir, 'denoised')

        shutil.copytree(src_dir, tmp_dir)

        # loop over settings
        for point, targets in self.settings.items():
            for target, params in targets.items():
                target_item = self.main_viewer.CohortTreeWidget.get_item(f'{point}/{target}')
                if target_item is None:
                    continue
                target_data = target_item.get_image_data()
                self.set_params(params)

                ## Do denoising here
                if point in self.knns.keys() and target in self.knns[point].keys():
                    target_data_cleaned = self._evaluate_target(
                        np.array(target_data.nonzero()).T,
                        self.knns[point][target],
                        target_data
                    )
                else:
                    nz, knn = self._generate_knn(target_data)
                    target_data_cleaned = self._evaluate_target(
                        nz,
                        knn,
                        target_data
                    )
                target_item.write_image_data(target_data_cleaned)

        # rename directories
        os.rename(src_dir, final_dir)
        os.rename(tmp_dir, src_dir)

        self.prevent_plotting = False


# function for amp plugin building
def build_as_plugin(main_viewer: MainViewer, plugin_path: str) -> KnnDenoising:
    """ Returns an instance of KnnDenoising

    This function is common to all plugins; it allows the plugin loader
    to correctly load the plugin.

    Args:
        main_viewer (MainViewer): reference to the main window
    """

    return KnnDenoising(main_viewer, plugin_path)
