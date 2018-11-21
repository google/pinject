import os

__all__ = [
    'VERSION',
]

curr_path = os.path.abspath(os.path.dirname(__file__))
VERSION_FILE = os.path.join(curr_path, '../VERSION')

VERSION = open(VERSION_FILE).read().strip()
