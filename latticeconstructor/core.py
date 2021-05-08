# -*- coding: utf-8 -*-

"""
Module latticeconstructor.core 
=================================================================

A module containing the main lattice builder classes.

"""

import queue
# your imports here ...
import re
from copy import deepcopy

import pandas as pd


def greet(to=''):
	"""Say "Hello <to>!".
	
	:param str to: whom you want to say hello to.
	"""
	f"Hello {to}!"
