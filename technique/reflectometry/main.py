# This is a sample Python script.

import sys
from collections import OrderedDict
from contextlib2 import contextmanager
# from termcolor import colored

from future.moves import itertools
from math import tan, radians, sin

from six.moves import input

import logging

try:
    # pylint: disable=import-error
    from genie_python import genie as g
except ImportError:
    from mocks import g

# import general.utilities.io
from sample import Sample
from instrument_constants import InstrumentConstant

const = InstrumentConstant()

print(const)
