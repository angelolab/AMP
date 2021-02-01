import sys
import os

def resource_path(relative_path):
    """ Get absolute path to resource (eg .ui files).  Should work for dev and pyinstaller
    """

    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)