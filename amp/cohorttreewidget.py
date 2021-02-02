from PyQt5 import QtWidgets, QtCore

import os
import sip

from typing import List

# Only supports single page tifs as of 6/22/2020


class CohortTreeWidgetItem(QtWidgets.QTreeWidgetItem):
    def __init__(self, parent: QtWidgets.QWidget = None, path: str = None) -> None:
        super().__init__(parent)
        self.path = path


class CohortTreeWidget(QtWidgets.QTreeWidget):
    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)

    def load_cohort(self, cohort_head: str) -> None:
        # list lowest depth tifs
        head = CohortTreeWidgetItem(self, cohort_head)
        head.setText(0, os.path.basename(cohort_head))
        tif_bfs([head])


def tif_bfs(heads: List[CohortTreeWidgetItem], max_depth: int = 6) -> None:
    """Recursive assembler of QtTreeWidget structure via breadth-first search.

    The child directories and/or tifs of each given head are collected and formated as new
    CohortTreeWidgetItem's.  If any tifs are found, no more recursive file searches are performed,
    and the final layers CohortTreeWidgetItem's are made togglable.  However, if no tifs are found,
    an this function is called recursively with `heads` being the found directories, and a
    max_depth one lower than the previous `max_depth`.

    Assumes all tifs of interest are within the same folder depth.  Only loads single page tifs.
    Multi-tiff and MIBITiff support is planned and will come later.

    Args:
        heads (List[CohortTreeWidgetItem]):
            Directories to search within. Formated as CohortTreeWidgetItem's so that
            CohortTreeWidget is automatically built; no need to be built externally.
        max_depth (int):
            Maximum file structure search depth. It's best to keep this low, as bfs grow
            exponentially with depth. Default is 6.
    """
    if max_depth <= 1:
        return []
    layer_dirs: List[CohortTreeWidgetItem] = []
    layer_tifs: List[CohortTreeWidgetItem] = []
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
