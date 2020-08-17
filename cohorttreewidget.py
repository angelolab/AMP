from PyQt5 import QtWidgets, QtCore

import os
import sip

# Only supports single page tifs as of 6/22/2020


def tif_bfs(heads, max_depth=6):
    # Assembles QtTreeWidget structure for cohort w/ bredth-first search
    # Assumes all tifs of interest are in the same folder depth
    # Only loads single page tifs
    # Multi-tiff support will come later
    if max_depth <= 1:
        return []
    layer_dirs = []
    layer_tifs = []
    # build search space for next recursion
    for head in heads:
        # create directory tree items (if no tifs found)
        layer_dirs.extend(
            [CohortTreeWidgetItem(head, entry.path)
             for entry in os.scandir(head.path)
             if entry.is_dir()
             and not entry.name.startswith('.')
             and len(layer_tifs) < 1]
        )
        # create tiff tree items
        layer_tifs.extend(
            [CohortTreeWidgetItem(head, entry.path)
             for entry in os.scandir(head.path)
             if entry.is_file()
             and '.tif' in entry.name]
        )
    # if tifs are found, delete unused directory nodes
    # and configure tif objects
    if layer_tifs:
        [sip.delete(ltc for ltc in ld.takeChildren()) for ld in layer_dirs]
        for lt in layer_tifs:
            lt.setFlags(lt.flags() |
                        QtCore.Qt.ItemIsUserCheckable |
                        QtCore.Qt.ItemIsEnabled |
                        QtCore.Qt.ItemNeverHasChildren)
            lt.setCheckState(0, QtCore.Qt.Unchecked)
            lt.setText(0, os.path.basename(lt.path))
        return
    # if no tifs are found, repeat recursion
    else:
        tif_bfs(layer_dirs, max_depth-1)
        # delete directories with no children and configure the rest
        for ld in layer_dirs:
            if not ld.childCount():
                head = ld.parent()
                sip.delete(head.takeChild(head.indexOfChild(ld)))
            else:
                ld.setText(0, os.path.basename(ld.path))
                ld.setFlags(ld.flags() & (~QtCore.Qt.ItemIsUserCheckable))
        layer_dirs = [ld for ld in layer_dirs if ld]
        return


class CohortTreeWidgetItem(QtWidgets.QTreeWidgetItem):
    def __init__(self, parent=None, path=None):
        super().__init__(parent)
        self.path = path


class CohortTreeWidget(QtWidgets.QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

    def load_cohort(self, cohort_head):
        # list lowest depth tifs
        head = CohortTreeWidgetItem(self, cohort_head)
        head.setText(0, os.path.basename(cohort_head))
        tif_bfs([head])
