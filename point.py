import os

from PIL import Image
import numpy as np
import pathlib

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

    def __init__(self, name: str, tif_path: str, channels: List[str]) -> None:
        self.name = name
        self.tif_path = tif_path
        self.channels = channels

        self.figure_ids: List[int] = []
        self.params: Dict[str, Any] = {}

    def add_figure_id(self, id: int) -> None:
        self.figure_ids.append(id)
        # print(f'{self.path}\nAfter add {self.figure_ids}\n')

    def remove_figure_id(self, id: int) -> None:
        self.figure_ids.remove(id)
        # print(f'{self.path}\nAfter remove {self.figure_ids}\n')

    def safe_remove_figure_id(self, id: int) -> None:
        try:
            self.figure_ids.remove(id)
            # print(f'{self.path}\nAfter SAFE remove {self.figure_ids}\n')
        except ValueError:
            return

    def get_channel_names(self) -> List[str]:
        return [chan.split('.')[0] for chan in self.channels]

    def get_parent_dir(self) -> str:
        return pathlib.Path(self.tif_path).parents[1]

    def get_top_dir(self) -> str:
        return pathlib.Path(self.tif_path).parents[2]

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

        # extension agnostic
        chans_filtered = []
        for chan in chans:
            for channel in self.channels:
                if chan == channel.split('.')[0] or chan == channel:
                    chans_filtered.append(channel)
                    break

        if not all(chan in self.channels for chan in chans_filtered):
            print(f'Some channels in, {chans}, could not be located')
            return

        data_out: Dict[str, Any] = {}
        for chan_name, chan_path in zip(chans, chans_filtered):
            full_path = os.path.join(self.tif_path, chan_path)
            data_out[chan_name] = np.asarray(Image.open(full_path))

        return data_out
