"""Unittests for the Scans module"""

import unittest
import doctest


def load_tests(_loader, tests, _ignore):
    """Run doc tests for the scans module"""
    # tests.addTests(
    #     doctest.DocFileSuite("../../../doc/source/scans/tutorial.rst"))
    tests.addTests(
        doctest.DocFileSuite("../../../doc/source/scans/instrument.rst"))
    return tests


if __name__ == "__main__":
    unittest.main()
