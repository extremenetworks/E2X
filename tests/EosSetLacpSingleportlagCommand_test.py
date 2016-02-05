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

# Copyright 2014-2016 Extreme Networks, Inc.  All rights reserved.
# Use is subject to license terms.

# This file is part of e2x (translate EOS switch configuration to ExtremeXOS)

import unittest
import sys

sys.path.extend(['../src'])

import EOS_read
import Switch

from unittest.mock import MagicMock


class EosSetLacpSingleportlagCommand_test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.mockSwitch = MagicMock(spec=Switch.Switch)

        cls.ErrorStart = 'ERROR: '
        cls.ErrEnDisStr = cls.ErrorStart + 'Could not {} single port lag'
        cls.ErrNoArgStr = \
            cls.ErrorStart + '"set lacp singleportlag {}" takes no argument'

    def setUp(self):
        self.cmd = EOS_read.EosSetLacpSingleportlagCommand(self.mockSwitch)

    def test_default(self):
        confFragment = 'unknown'
        expected = \
            'NOTICE: Ignoring unknown command "set lacp singleportlag ' + \
            confFragment + '"'

        result = self.cmd.onecmd(confFragment)

        self.assertEqual(expected, result)

    def test_do_disable_fail_arg_not_empty(self):
        arg = 'dont'
        confFragment = 'disable' + ' ' + arg
        expected = self.ErrNoArgStr.format('disable')

        result = self.cmd.onecmd(confFragment)

        self.assertEqual(expected, result)

    def test_do_disable_fail_switch_function_returns_None(self):
        confFragment = 'disable'
        self.mockSwitch.set_single_port_lag.return_value = None
        expected = self.ErrEnDisStr.format('disable')

        result = self.cmd.onecmd(confFragment)

        self.assertEqual(expected, result)

    def test_do_disable_fail_switch_function_returns_True(self):
        confFragment = 'disable'
        self.mockSwitch.set_single_port_lag.return_value = True
        expected = self.ErrEnDisStr.format('disable')

        result = self.cmd.onecmd(confFragment)

        self.assertEqual(expected, result)

    def test_do_disable_ok(self):
        confFragment = 'disable'
        self.mockSwitch.set_single_port_lag.return_value = False
        expected = ''

        result = self.cmd.onecmd(confFragment)

        self.assertEqual(expected, result)

    def test_do_enable_fail_arg_not_empty(self):
        arg = 'dont'
        confFragment = 'enable' + ' ' + arg
        expected = self.ErrNoArgStr.format('enable')

        result = self.cmd.onecmd(confFragment)

        self.assertEqual(expected, result)

    def test_do_enable_fail_switch_function_returns_None(self):
        confFragment = 'enable'
        self.mockSwitch.set_single_port_lag.return_value = None
        expected = self.ErrEnDisStr.format('enable')

        result = self.cmd.onecmd(confFragment)

        self.assertEqual(expected, result)

    def test_do_emable_fail_switch_function_returns_False(self):
        confFragment = 'enable'
        self.mockSwitch.set_single_port_lag.return_value = False
        expected = self.ErrorStart + \
            'Could not enable single port lag'

        result = self.cmd.onecmd(confFragment)

        self.assertEqual(expected, result)

    def test_do_enable_ok(self):
        confFragment = 'enable'
        self.mockSwitch.set_single_port_lag.return_value = True
        expected = ''

        result = self.cmd.onecmd(confFragment)

        self.assertEqual(expected, result)

if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
