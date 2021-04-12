from re import sub
from PyQt5 import QtWidgets, QtCore

import numpy as np
import skimage.io as io
import os
from pathlib import Path
import sip

from typing import List, Set, Union, Any

import amp.tiff_utils as tiff_utils

# Only supports single page tifs as of 6/22/2020


class CohortTreeWidgetItem(QtWidgets.QTreeWidgetItem):
    def __init__(self, parent: QtWidgets.QWidget = None, path: str = None) -> None:
        super().__init__(parent)
        self.path = path
        self.is_mibitiff = tiff_utils.is_mibitiff(path.split('|')[0])

    def parent(self) -> 'CohortTreeWidgetItem':
        return super().parent()

    def __hash__(self) -> int:
        return hash(id(self))

    def __eq__(self, x: 'CohortTreeWidgetItem') -> bool:
        return x is self

    def __ne__(self, x: 'CohortTreeWidgetItem') -> bool:
        return x is not self

    def get_child_by_name(self, name: str) -> 'CohortTreeWidgetItem':
        child_out = None
        for index in range(self.childCount()):
            child = self.child(index)
            if child.text(0) == name:
                child_out = child
                break
        return child_out

    def get_image_data(self) -> Union[Any, None]:
        if '.tif' in self.path:
            if self.is_mibitiff and len(self.path.split('|')) > 1:
                img_data, _ = tiff_utils.read_mibitiff(
                    self.path.split('|')[0],
                    channels=[self.path.split('|')[1]]
                )
                return img_data[:, :, 0]
            else:
                return io.imread(self.path)
        else:
            return None

    def write_image_data(self, new_data: Any) -> None:
        """ writes image data to saved path

        Args:
            new_data (np.array):
                image data to write out to file
        """

        if '.tif' in self.path:
            if self.is_mibitiff and len(self.path.split('|')) > 1:
                tiff_utils.overwrite_mibitiff_channel(*self.path.split('|'), new_data)
            else:
                io.imsave(self.path, new_data.astype(np.uint8), plugin='tifffile')
        else:
            return


class CohortTreeWidget(QtWidgets.QTreeWidget):
    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)
        self.channels: Set[str] = set()
        self.head: CohortTreeWidgetItem = None

    def load_cohort(self, cohort_head: str) -> None:
        # list lowest depth tifs
        self.head = CohortTreeWidgetItem(self, cohort_head)
        self.head.setText(0, os.path.basename(cohort_head))
        self.channels = tif_bfs([self.head])

    def get_channels(self) -> List[str]:
        return list(self.channels)

    def get_item(self, tree_path: str) -> CohortTreeWidgetItem:
        """ Indexes through provided tree path and returns reference to a widget item

        Args:
            tree_path (str): filepath like string indexing into the tree

        Returns:
            CohortTreeWidgetItem:
                reference to desired point
        """
        # print(Path(tree_path).parts)
        current_node = self.head
        for i, part in enumerate(Path(tree_path).parts):
            if i > 0:
                current_node = current_node.get_child_by_name(part)

            if current_node is None or current_node.text(0) != part:
                return None

        return current_node

    def gen_quickview(self, all_checkable: bool = True,
                      include_channels: bool = False) -> QtWidgets.QTreeWidgetItem:
        """ Generates a default tree view of the cohort.  Useful for passing to plugins for viewing
        and selection purposes.

        Args:
            all_checkable (bool):
                Add checkbox to every item
            include_channels (bool):
                Include channels in tree view

        Returns:
            QtWidgets.QTreeWidgetItem:
                reference to top level item

        """

        # create deep copy
        head_out = self.head.clone()

        if all_checkable:
            add_checks([head_out], self.channels if not include_channels else None)

        return head_out

def add_checks(heads: List[QtWidgets.QTreeWidgetItem], excludes: Union[Set[str], None]) -> None:
    """ Recursively adds checks to all members of the tree widget

    Args:
        heads (List[QtWidgets.QTreeWidgetItem]):
            widgets to initiate recursion from
        excludes (Set[str]):
            widgets will be excluded if their text is in this set
    """

    for head in heads:
        head.setFlags(head.flags() |
                      QtCore.Qt.ItemIsUserCheckable |
                      QtCore.Qt.ItemIsEnabled)
        head.setCheckState(0, QtCore.Qt.Unchecked)

        if excludes is not None:
            for child in [head.child(index) for index in range(head.childCount())]:
                if child.text(0) in excludes:
                    head.removeChild(child)
                    del child

        add_checks([head.child(index) for index in range(head.childCount())], excludes)


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
    channels: Set[str] = set()
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
    if layer_tifs:
        [sip.delete(ltc for ltc in ld.takeChildren()) for ld in layer_dirs]

        # trim layer of universal subdirs if present
        first_lt_parent_name = Path(layer_tifs[0].path).parts[-2]
        has_img_subdir = all(
            [first_lt_parent_name == Path(lt.path).parts[-2] for lt in layer_tifs]
        )
        subdir_is_head = layer_tifs[0].parent().parent() is None
        if has_img_subdir and not subdir_is_head:
            img_subdirs= {lt.parent() for lt in layer_tifs}
            for subdir in img_subdirs:
                channels_obj = subdir.takeChildren()
                fov_head = subdir.parent()
                fov_head.removeChild(subdir)
                fov_head.addChildren(channels_obj)
                del subdir

        # check for mibitiff and set channels to be checkable
        for lt in layer_tifs:
            if tiff_utils.is_mibitiff(lt.path):
                _ , tif_channels = tiff_utils.read_mibitiff(lt.path)
                layer_channels = [
                    CohortTreeWidgetItem(lt, f"{lt.path}|{tif_channel[1].replace('|', '_')}")
                    for tif_channel in tif_channels
                ]
                # redundant iteration (easier to read imo)
                for lc in layer_channels:
                    lc.setFlags(lc.flags() |
                        QtCore.Qt.ItemIsUserCheckable |
                        QtCore.Qt.ItemIsEnabled |
                        QtCore.Qt.ItemNeverHasChildren)
                    lc.setCheckState(0, QtCore.Qt.Unchecked)
                    channel_name = os.path.basename(lc.path.split('|')[1])
                    channels.add(channel_name)
                    lc.setText(0, channel_name)
                    lt.setText(0, os.path.basename(lt.path))
            else:
                lt.setFlags(lt.flags() |
                            QtCore.Qt.ItemIsUserCheckable |
                            QtCore.Qt.ItemIsEnabled |
                            QtCore.Qt.ItemNeverHasChildren)
                lt.setCheckState(0, QtCore.Qt.Unchecked)
                channel_name = os.path.basename(lt.path.split('.')[0])
                channels.add(channel_name)
                lt.setText(0, channel_name)

        return channels
    # if no tifs are found, repeat recursion
    else:
        channels = tif_bfs(layer_dirs, max_depth-1)
        # delete directories with no children and configure the rest
        for ld in layer_dirs:
            if not ld.childCount():
                head = ld.parent()
                if head is not None:
                    sip.delete(head.takeChild(head.indexOfChild(ld)))
            else:
                ld.setText(0, os.path.basename(ld.path))
                ld.setFlags(ld.flags() & (~QtCore.Qt.ItemIsUserCheckable))
                ld.sortChildren(0, 0)
        layer_dirs = [ld for ld in layer_dirs if ld]
        for head in heads:
            head.sortChildren(0, 0)
        return channels
