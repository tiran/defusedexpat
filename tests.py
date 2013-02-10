from __future__ import print_function
import os
import sys
import unittest

import defusedexpat
import pyexpat
import _elementtree


def test_main():
    suite = unittest.TestSuite()
    #suite.addTests(unittest.makeSuite(cls))
    return suite

if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(test_main())
    sys.exit(not result.wasSuccessful())
