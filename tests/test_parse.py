#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `latticeconstructor` package."""

import pytest

import latticeconstructor.parse

def test_greet():
    expected = "Hello John!"
    greeting = latticeconstructor.parse.greet("John")
    assert greeting==expected


# ==============================================================================
# The code below is for debugging a particular test in eclipse/pydev.
# (normally all tests are run with pytest)
# ==============================================================================
if __name__ == "__main__":
    the_test_you_want_to_debug = test_greet

    the_test_you_want_to_debug()
    print("-*# finished #*-")
# ==============================================================================
