import os

from PIL import Image
import numpy as np


class Point(object):
    def __init__(self, path, channels):
        self.path = path
        self.channels = channels

        self.figure_ids = []
        self.params = {}

    def add_figure_id(self, id):
        self.figure_ids.append(id)

    def remove_figure_id(self, id):
        self.figure_ids.remove(id)

    def safe_remove_figure_id(self, id):
        try:
            self.figure_ids.remove(id)
        except ValueError:
            return

    def set_param(self, name, data):
        self.params[name] = data

    def get_param(self, name):
        if name in self.params:
            return self.params[name]
        else:
            return None

    def remove_param(self, name):
        del self.params[name]

    def get_channel_data(self, chans=None):
        if chans is None:
            chans = self.channels
        elif not all(chan in self.channels for chan in chans):
            print(f'Some channels in, {chans}, could not be located')
            return

        data_out = {}
        for chan in chans:
            full_path = os.path.join(self.path, chan)
            data_out[chan] = np.asarray(Image.open(full_path))

        return data_out
