import os

from importlib import import_module

# tools for loading amp plugins
# TODO: Reimplement to build plugin from a *.py file


def load_plugin(ui_file, main_viewer):
    imp_name = os.path.basename(ui_file).split('.')[0]
    plugin = import_module(imp_name)
    builder = getattr(plugin, 'buildAsPlugin')
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
