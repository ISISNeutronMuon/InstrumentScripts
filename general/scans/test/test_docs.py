import unittest
import doctest


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocFileSuite("../../../doc/source/scans/tutorial.rst"))
    tests.addTests(doctest.DocFileSuite("../../../doc/source/scans/instrument.rst"))
    return tests


if __name__ == "__main__":
    unittest.main()
