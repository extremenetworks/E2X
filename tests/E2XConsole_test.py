# CDDL HEADER START
#
# The contents of this file are subject to the terms
# of the Common Development and Distribution License
# (the "License").  You may not use this file except
# in compliance with the License.
#
# You can obtain a copy of the license at
# LICENSE.txt or http://opensource.org/licenses/CDDL-1.0.
# See the License for the specific language governing
# permissions and limitations under the License.
#
# When distributing Covered Code, include this CDDL
# HEADER in each file and include the License file at
# LICENSE.txt  If applicable,
# add the following below this CDDL HEADER, with the
# fields enclosed by brackets "[]" replaced with your
# own identifying information: Portions Copyright [yyyy]
# [name of copyright owner]
#
# CDDL HEADER END

# Copyright 2014-2017 Extreme Networks, Inc.  All rights reserved.
# Use is subject to license terms.

# This file is part of e2x (translate EOS switch configuration to ExtremeXOS)

import sys
sys.path.extend(['../src'])

import unittest
from unittest.mock import MagicMock
import importlib

from E2XConsole import E2XConsole, SysInOutConsole, CursesConsole
import cli


class E2XConsole_test(unittest.TestCase):

    realimport = None
    curses_available = True

    def myimport(name):
        if name == 'curses' or name == 'unicurses':
            raise ImportError
        return E2XConsole_test.realimport(name)

    @classmethod
    def setUpClass(cls):
        E2XConsole_test.realimport = importlib.import_module
        try:
            importlib.import_module('curses')
        except:
            try:
                importlib.import_module('unicurses')
            except:
                E2XConsole_test.curses_available = False

    def skipUnlessCursesAvailable():
        try:
            importlib.import_module('curses')
        except:
            try:
                importlib.import_module('unicurses')
            except:
                return unittest.skip('curses module not available')
        return lambda func: func

    def setUp(self):
        self.e2xc = E2XConsole(True)
        self.screen_mock = MagicMock()

    def tearDown(self):
        importlib.import_module = E2XConsole_test.realimport

    def test_init_shouldFallBackToSysInOutConsole(self):
        importlib.import_module = E2XConsole_test.myimport

        e2xc = E2XConsole(True)

        screen = e2xc.get_screen()

        self.assertIsInstance(screen, SysInOutConsole)

    @skipUnlessCursesAvailable()
    def test_init_shouldUseCursesIfAvailable(self):
        self.e2xc.close()

        screen = self.e2xc.get_screen()
        self.assertIsInstance(screen, CursesConsole)

    def test_display_intro_shouldShowProgramNameAndVersion(self):
        self.e2xc.screen = self.screen_mock
        disp_intro_method = self.screen_mock.display_intro
        intro = cli.progname + ' ' + cli.progver

        self.e2xc.display_intro(intro)

        disp_intro_method.assert_called_once_with(intro)

    def test_display_intro_shouldContainProgramNameAndVersion(self):
        self.e2xc.screen = self.screen_mock
        disp_intro_method = self.screen_mock.display_intro
        prog = cli.progname + ' ' + cli.progver

        self.e2xc.display_intro(prog)

        (args, keys) = disp_intro_method.call_args
        self.assertIn(prog, args[0])

    def test_close_shouldPropagateToScreen(self):
        self.e2xc.screen = self.screen_mock
        close_method = self.screen_mock.close

        self.e2xc.close()

        close_method.assert_called_once_with()

if __name__ == '__main__':
    unittest.main(buffer=True)

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
