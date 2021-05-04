from fractions import Fraction
import numpy as np
from tifffile import TiffFile, TiffWriter
import json
import datetime
from itertools import compress

import sys


def read_mibitiff(file, channels=None, get_metadata=False):
    """ Reads MIBI data from an IonpathMIBI TIFF file.
    Currently, only SIMS data is supported
    Args:
        file (str): The string path or an open file object to a MIBItiff file.
        channels (list): Targets to load. If None, all targets/channels are loaded
        get_metadata (bool): Return global image metadata
    Returns:
        tuple (np.ndarray, list[tuple], dict):
        - image data
        - channel data
        - metadata (optional)
    """
    return_channels = []
    img_data = []
    metadata = {}
    with TiffFile(file) as tif:

        # make sure it's a mibitiff
        _check_version(tif)

        for page in tif.pages:

            # get tags as json
            description = json.loads(
                page.tags['ImageDescription'].value
            )

            # only load supplied channels
            if channels is not None and description['channel.target'] not in channels:
                continue

            # read channel data
            return_channels.append((
                description['channel.mass'],
                description['channel.target']
            ))

            # read image data
            img_data.append(page.asarray())

            # copy metadata
            if metadata == {} and get_metadata:
                metadata = description.copy()

    # make sure all passed channels were found
    if channels is not None:
        try:
            channel_names = [return_channel[1] for return_channel in return_channels]
            # TODO: replace this verify_in_list
            # verify_in_list(passed_channels=channels, in_tiff=channel_names)
        except ValueError as exc:
            raise IndexError('Passed unknown channels...') from exc

    if get_metadata:
        return np.stack(img_data, axis=2), return_channels, metadata
    else:
        return np.stack(img_data, axis=2), return_channels


def is_mibitiff(path: str) -> bool:
    """ Checks that file is MIBItiff, but raises no error

    Args:
        path (str): The string path or an open file object pointing to a tiff file

    Returns:
        bool:
            is the file a mibitiff?
    """
    try:
        with TiffFile(path) as tif:
            _check_version(tif)
        return True
    except:
        return False


def overwrite_mibitiff_channel(file, channel, data):
    """ Overwrites data within a mibitiff channel with the provided data

    Args:
        file (str): The string path or an open file object pointing to a MIBItiff file.
        channel (str): The target channel to overwrite
        data (ndarray): The image data
    """

    img_data, file_channels, metadata = read_mibitiff(file, get_metadata=True)

    # overwrite channel with new data
    img_data[:, :, [file_channel[1] for file_channel in file_channels].index(channel)] = data

    # write tiff out
    write_mibitiff(file, img_data, file_channels, metadata, prefixed=True)


def _check_version(file: TiffFile):
    """ Checks that file is MIBItiff
    Args:
        file (TiffFile): opened tiff file
    Raises:
        ValueError
    """
    filetype = file.pages[0].tags['Software']
    if not (filetype and filetype.value.startswith('IonpathMIBI')):
        raise ValueError('File is not of type IonpathMIBI...')


_PREFIXED_METADATA_ATTRIBUTES = ('run', 'coordinates', 'size', 'slide',
                                 'fov_id', 'fov_name', 'folder', 'dwell',
                                 'scans', 'aperture', 'instrument', 'tissue',
                                 'panel', 'mass_offset', 'mass_gain',
                                 'time_resolution', 'miscalibrated',
                                 'check_reg', 'filename', 'description',
                                 'version')


def write_mibitiff(filepath, img_data, channel_tuples, metadata, prefixed=False):
    """ Writes MIBI data to a multipage TIFF.
    Args:
        filepath (str):
            The path to the target file
        img_data (np.ndarray):
            Image data
        channel_tuples (iterable):
            Iterable of tuples corresponding to image channel massess and target names
        metadata (dict):
            MIBItiff specific metadata
        prefixed (bool):
            Specifies if metadata atributes are already prefixed with 'mibi.'
    """

    # set up mibitiff metadata
    ranges = [(0, m) for m in img_data.max(axis=(0, 1))]

    range_dtype = _range_dtype_map(img_data.dtype)

    coordinates = [
        (286, '2i', 1, _micron_to_cm(metadata[f'{"mibi." if prefixed else ""}coordinates'][0])),
        (287, '2i', 1, _micron_to_cm(metadata[f'{"mibi." if prefixed else ""}coordinates'][1]))
    ]
    resolution = (img_data.shape[0] * 1e4 / float(metadata[f'{"mibi." if prefixed else ""}size']),
                  img_data.shape[1] * 1e4 / float(metadata[f'{"mibi." if prefixed else ""}size']),
                  'CENTIMETER')

    description = {}
    for key, value in metadata.items():
        if key in _PREFIXED_METADATA_ATTRIBUTES:
            description[f'mibi.{key}'] = value

    with TiffWriter(filepath) as infile:
        for index, channel_tuple in enumerate(channel_tuples):
            mass, target = channel_tuple
            _metadata = description.copy()
            _metadata.update({
                'image.type': 'SIMS',
                'channel.mass': int(mass),
                'channel.target': target,
            })
            page_name = (
                285, 's', 0, '{} ({})'.format(target,
                                              mass)
            )
            min_value = (340, range_dtype, 1, ranges[index][0])
            max_value = (341, range_dtype, 1, ranges[index][1])
            page_tags = coordinates + [page_name, min_value, max_value]

            date = \
                None if 'date' not in metadata.keys() else datetime.datetime.strptime(
                    metadata['date'],
                    '%Y-%m-%dT%H:%M:%S'
                )

            infile.save(
                img_data[:, :, index], compress=6, resolution=resolution,
                extratags=page_tags, metadata=_metadata,
                datetime=date,
                software="IonpathMIBIv1.0"
            )


def _micron_to_cm(um):
    """ Converts microns to a fraction tuple in cm
    """
    frac = Fraction(float(um) / 10000).limit_denominator(1000000)
    return frac.numerator, frac.denominator


def _range_dtype_map(dtype):
    if dtype == np.float32 or np.issubdtype(dtype, np.floating):
        return 'd'
    else:
        return 'I'