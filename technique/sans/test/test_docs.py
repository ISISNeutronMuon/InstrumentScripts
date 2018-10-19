"""Unittests for the Sans module"""

import unittest
import doctest


def load_tests(_loader, tests, _ignore):
    """Run doc tests for the sans module"""
    tests.addTests(
        doctest.DocFileSuite("../../../doc/source/sans/tutorial.rst"))
    return tests


if __name__ == "__main__":
    unittest.main()
