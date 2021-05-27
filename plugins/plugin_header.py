from PyQt5 import QtWidgets, QtCore, uic

from amp.main_viewer import MainViewer
from amp.mplwidget import ImagePlot, HistPlot, Plot

import numpy as np
from scipy.ndimage import gaussian_filter
from scipy.stats import gamma
from scipy.optimize import fsolve
from scipy.special import digamma
from scipy.special import gamma as gamma_func
from sklearn.neighbors import NearestNeighbors

# extra hidden import (should tell pyinstaller to update their sklearn hook)
import sklearn.utils._weight_vector

import os
import shutil
import json

from typing import Tuple, List, Dict, Any, Union