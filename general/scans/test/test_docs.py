"""Unittests for the Scans module"""

import unittest
import doctest
import os


def load_tests(_loader, tests, _ignore):
    """Run doc tests for the scans module"""

    # Use postscript backend - this is non interactive so won't block tests.
    import matplotlib
    matplotlib.use("PS")

    pwd = os.getcwd()
    tests.addTests(
        doctest.DocFileSuite(os.path.join("..", "..", "..", "doc", "source", "scans", "tutorial.rst"),
                             setUp=lambda _: os.chdir(os.path.join("doc", "source", "scans")),
                             tearDown=lambda _: os.chdir(pwd)))
    tests.addTests(
        doctest.DocFileSuite(os.path.join("..", "..", "..", "doc", "source", "scans", "instrument.rst"),
                             setUp=lambda _: os.chdir(os.path.join("doc", "source", "scans")),
                             tearDown=lambda _: os.chdir(pwd)))
    return tests


if __name__ == "__main__":
    unittest.main()
