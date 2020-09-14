import os

from PIL import Image
import numpy as np

from typing import List, Union, Dict, Any
from numbers import Number


class Point:
    """Class containing relevent information and methods for a managing points within AMP plugins

    Raw point data is not handled by this class; rather this class manages file locations and
    dynamically loads channel data when requested.

    Atributes:
        path (str):
            path to folder of tifs for point
        channels (List[str]):
            file names for channels
        figure_ids (List[int]):
            figure id's for point related figures within figure_manager
        params (Dict[str, Any]):
            dictionary containing arbitrary algorithm inputs
    """

    def __init__(self, path: str, channels: List[str]) -> None:
        self.path = path
        self.channels = channels

        self.figure_ids: List[int] = []
        self.params: Dict[str, Any] = {}

    def add_figure_id(self, id: int) -> None:
        self.figure_ids.append(id)

    def remove_figure_id(self, id: int) -> None:
        self.figure_ids.remove(id)

    def safe_remove_figure_id(self, id: int) -> None:
        try:
            self.figure_ids.remove(id)
        except ValueError:
            return

    def set_param(self, name: str, data: List[List[Number]]) -> None:
        self.params[name] = data

    def get_param(self, name: str) -> Union[List[List[Number]], None]:
        if name in self.params:
            return self.params[name]
        else:
            return None

    def remove_param(self, name: str) -> None:
        del self.params[name]

    def get_channel_data(self,
                         chans: Union[List[str], None] = None) -> Union[Dict[str, Any], None]:
        if chans is None:
            chans = self.channels
        elif not all(chan in self.channels for chan in chans):
            print(f'Some channels in, {chans}, could not be located')
            return

        data_out: Dict[str, Any] = {}
        for chan in chans:
            full_path = os.path.join(self.path, chan)
            data_out[chan] = np.asarray(Image.open(full_path))

        return data_out
