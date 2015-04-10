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

# Copyright 2014-2015 Extreme Networks, Inc.  All rights reserved.
# Use is subject to license terms.

# This file is part of e2x (translate EOS switch configuration to ExtremeXOS)

import unittest
import sys

sys.path.extend(['../src'])

import EOS_read
import Port
import Switch

from unittest.mock import MagicMock


class EosSetPortJumboCommand_test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.portName = 'ge.1.1'
        cls.mockPort = MagicMock(spec=Port.Port)
        cls.mockPort.get_name.return_value = cls.portName

        cls.mockSwitch = MagicMock(spec=Switch.Switch)
        cls.mockSwitch.get_ports_by_name.return_value = \
            [cls.mockPort, cls.mockPort]

        cls.ErrorStart = 'ERROR: '
        cls.WarningStart = 'WARN: '
        cls.NoticeStart = 'NOTICE: '
        cls.PortNotFound = \
            cls.ErrorStart + 'Port ' + cls.portName + ' not found'
        cls.FailMessage = \
            cls.ErrorStart + 'Could not {} jumbo frames for port ' + \
            cls.portName

    def setUp(self):
        self.cmd = EOS_read.EosSetPortJumboCommand(self.mockSwitch)

    def tearDown(self):
        self.mockPort.reset_mock()

    def test_default(self):
        line = 'foo'
        expected = self.NoticeStart + \
            'Ignoring unknown command "set port jumbo ' + line + '"'

        result = self.cmd.onecmd(line)

        self.assertEqual(expected, result)

    def test_do_enable_disable_port_not_found(self):
        expectedEnable = self.PortNotFound + ' (set port jumbo enable)'
        expectedDisable = self.PortNotFound + ' (set port jumbo disable)'
        self.mockSwitch.get_ports_by_name.return_value = []

        resultEnable = self.cmd.do_enable(self.portName)
        resultDisable = self.cmd.do_disable(self.portName)

        self.assertEqual(expectedEnable, resultEnable)
        self.assertEqual(expectedDisable, resultDisable)

    def test_do_enable_enable_fail(self):
        expected = self.FailMessage.format('enable')

        self.mockSwitch.get_ports_by_name.return_value = [self.mockPort]
        self.mockPort.set_jumbo.return_value = False

        result = self.cmd.do_enable(self.portName)

        self.mockPort.set_jumbo.assert_called_once_with(True, 'config')
        self.assertEqual(expected, result)

    def test_do_disable_disable_fail(self):
        expected = self.FailMessage.format('disable')

        self.mockSwitch.get_ports_by_name.return_value = [self.mockPort]
        self.mockPort.set_jumbo.return_value = True

        result = self.cmd.do_disable(self.portName)

        self.mockPort.set_jumbo.assert_called_once_with(False, 'config')
        self.assertEqual(expected, result)

if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
