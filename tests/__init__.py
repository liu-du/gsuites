import os
import sys

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
SRC_PATH = os.path.realpath(os.path.join(DIR_PATH, '../src'))
sys.path.insert(0, SRC_PATH)
