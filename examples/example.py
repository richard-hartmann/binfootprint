#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division, print_function

import sys
from os.path import abspath, dirname, split

# Add parent directory to beginning of path variable
sys.path = [split(dirname(abspath(__file__)))[0]] + sys.path

import binfootprint as bf

atoms = [
    12345678,  # int32
    3.141,  # float
    "hallo Welt",  # ascii string
    "öäüß",  # utf8 string
    True,
    False,
    None,  # special Value
    2 ** 65,
    -(3 ** 65),  # integer
    b"\xff\fe\03",
]  # bytes

binkey = bf.dump(atoms)  # generate a unique byte sequence
atoms_prime = bf.load(binkey)  # restore the original object
