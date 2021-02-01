import os
import re

from PyQt5 import QtWidgets

from importlib.machinery import SourceFileLoader

# tools for loading amp plugins


def load_plugin(plugin_path: str, main_viewer: QtWidgets.QMainWindow) -> QtWidgets.QMainWindow:
    """Load plugin from file and return an instance

    Args:
        plugin_path (str):
            File path to plugin.  This should be a folder/zip with .ui and .py file
        main_viewer (QtWidgets.QMainWindow):
            Main viewer instance.  Plugins need to contain a reference to the main viewer.

    Returns:
        QtWidgets.QMainWindow:
            Plugin defined within ui_file
    """

    plugin_name = os.path.basename(plugin_path).split('.')[0]
    ui_name = ''.join([f'{tocap[0].upper()}{tocap[1:]}' for tocap in plugin_name.split('_')])
    py_path = os.path.join(plugin_path, f'{plugin_name}.py')
    ui_path = os.path.join(plugin_path, f'{ui_name}.ui')

    plugin = SourceFileLoader(plugin_name, py_path).load_module()
    builder = getattr(plugin, 'build_as_plugin')
    return builder(main_viewer, ui_path)


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
