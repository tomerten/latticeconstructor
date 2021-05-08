#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `latticeconstructor` package."""

import latticeconstructor.core
import numpy as np
import pandas as pd
import pytest
from latticeconstructor.core import LatticeBuilderLine


def test_fodo():
    expected_dc = {
        "family": {
            0: "MARKER",
            1: "QUADRUPOLE",
            2: "DRIFT",
            3: "QUADRUPOLE",
            4: "DRIFT",
            5: "QUADRUPOLE",
        },
        "L": {0: 0.0, 1: 0.342, 2: 3.5805, 3: 0.668, 4: 3.5805, 5: 0.342},
        "filename": {0: '"%s-%03ld.w1"', 1: np.nan, 2: np.nan, 3: np.nan, 4: np.nan, 5: np.nan},
        "mode": {0: "coordinates", 1: np.nan, 2: np.nan, 3: np.nan, 4: np.nan, 5: np.nan},
        "name": {0: "W1", 1: "QF", 2: "D", 3: "QD", 4: "D", 5: "QF"},
        "K1": {0: np.nan, 1: 0.49, 2: np.nan, 3: -0.4999, 4: np.nan, 5: 0.49},
        "N_KICKS": {0: np.nan, 1: 16.0, 2: np.nan, 3: 16.0, 4: np.nan, 5: 16.0},
        "pos": {0: 0.0, 1: 0.171, 2: 2.13225, 3: 4.2565, 4: 6.380749999999999, 5: 8.342},
    }

    expected = pd.DataFrame.from_dict(expected_dc)

    lblfodo = LatticeBuilderLine()
    lblfodo.add_def(
        {
            "QF": {"family": "KQUAD", "L": 0.342, "K1": 0.4900, "N_KICKS": 16},
            "QD": {"family": "KQUAD", "L": 0.668, "K1": -0.4999, "N_KICKS": 16},
            "D": {"family": "DRIF", "L": 3.5805},
            "W1": {"family": "WATCH", "L": 0, "filename": '"%s-%03ld.w1"', "mode": "coordinates"},
        }
    )
    lblfodo.add_element(["W1", "QF", "D", "QD", "D", "QF"])
    assert lblfodo.table.equals(expected)


# ==============================================================================
# The code below is for debugging a particular test in eclipse/pydev.
# (normally all tests are run with pytest)
# ==============================================================================
if __name__ == "__main__":
    the_test_you_want_to_debug = test_fodo

    the_test_you_want_to_debug()
    print("-*# finished #*-")
# ==============================================================================
