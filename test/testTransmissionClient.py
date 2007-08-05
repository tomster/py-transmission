#!/usr/bin/env python
# encoding: utf-8

__author__ = "Tom Lazar (tom@tomster.org)"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2007/07/29 $"
__copyright__ = "Copyright (c) 2007 Tom Lazar"
__license__ = "MIT License"

import sys, os
sys.path = ['.',] + sys.path #HACK: enables importing from `TransmissionClient`

import unittest
import doctest
from TransmissionClient import TransmissionClient

SOCKETPATH = None

class TransmissionTests(unittest.TestCase):
    """ 
        These tests expect a running transmission-daemon instance listening on port 9090
    """
    def setUp(self):
        """makes sure we've got a transmission daemon running to run the tests against."""
        self.daemon = TransmissionClient(SOCKETPATH)

    def testStartup(self):
        self.failIf(self.daemon == None) 
    
    def testDoctests(self):
        """docstring for testDoctests"""
        doctest.testfile("README.rst", verbose=False, report=True, globs={'SOCKETPATH': SOCKETPATH, 'self': self})

def usage():
    print """ERROR:
        You must provide a full path to the socket of a locally running transmission-daemon as 
        the LAST command line argument to this test call, i.e.:
        
            python test/testTransmissionClient.py SOCKETPATH
            python test/testTransmissionClient.py TransmissionTests SOCKETPATH
            python test/testTransmissionClient.py TransmissionTests.testDoctests SOCKETPATH
            etc.
        
        """

if __name__ == "__main__":
    if len(sys.argv) < 2:
        usage()
        sys.exit(2)
    SOCKETPATH = sys.argv[-1]
    if os.path.exists(SOCKETPATH):
        sys.argv = sys.argv[:-1]
        unittest.main()

    else:
        usage()

