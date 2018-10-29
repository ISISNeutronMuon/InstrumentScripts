"""Unittests for the Sans module"""

import unittest
import doctest
import os


def load_tests(_loader, tests, _ignore):
    """Run doc tests for the sans module"""
    pwd = os.getcwd()
    tests.addTests(
        doctest.DocFileSuite("../../../doc/source/sans/tutorial.rst",
                             setUp=lambda _: os.chdir("technique/sans"),
                             tearDown=lambda _: os.chdir(pwd)))
    return tests


if __name__ == "__main__":
    unittest.main()
