import os

from PIL import Image
import numpy as np

from typing import List, Union, Dict, Any


class Point(object):
    def __init__(self, path: str, channels: List[str]) -> None:
        self.path = path
        self.channels = channels

        self.figure_ids: List[int] = []
        self.params = {}

    def add_figure_id(self, id: int) -> None:
        self.figure_ids.append(id)

    def remove_figure_id(self, id: int) -> None:
        self.figure_ids.remove(id)

    def safe_remove_figure_id(self, id: int) -> None:
        try:
            self.figure_ids.remove(id)
        except ValueError:
            return

    def set_param(self, name: str, data: dict) -> None:
        self.params[name] = data

    def get_param(self, name: str) -> Union[dict, None]:
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
