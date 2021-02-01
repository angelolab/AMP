import os

from PyQt5 import QtWidgets

from importlib.machinery import SourceFileLoader

# tools for loading amp plugins


def load_plugin(ui_file: str, main_viewer: QtWidgets.QMainWindow) -> QtWidgets.QMainWindow:
    """Load plugin from file and return an instance

    Args:
        ui_file (str):
            File path to plugin.  This must be a .py file.
        main_viewer (QtWidgets.QMainWindow):
            Main viewer instance.  Plugins need to contain a reference to the main viewer.

    Returns:
        QtWidgets.QMainWindow:
            Plugin defined within ui_file
    """
    imp_name = os.path.basename(ui_file).split('.')[0]
    plugin = SourceFileLoader(imp_name, ui_file).load_module()
    builder = getattr(plugin, 'build_as_plugin')
    return builder(main_viewer)


# class Plugin(QtWidgets.QMainWindow):
#     def __init__(self, ui_file):
#         super().__init__()
#         # load ui elements into MainViewer class
#         uic.loadUi(ui_file, self)
#
#         # General UI threadpool (probably shouldn't use for big algorithms)
#         #self.executer = concurrent.futures.ThreadPoolExecutor(max_workers=1)
#
#         # connect UI callbacks (somehow?)
#
#         self.setWindowTitle("Plugin")
