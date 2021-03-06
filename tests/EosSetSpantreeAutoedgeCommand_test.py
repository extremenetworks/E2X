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

import unittest
import sys

sys.path.extend(['../src'])

import EOS_read
import Switch
import Port

from unittest.mock import MagicMock


class EosSetSpantreeAutoedgeCommand_test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.mockSwitch = MagicMock(spec=Switch.Switch)
        cls.mockPort = MagicMock(spec=Port.Port)

        cls.ErrorStart = 'ERROR: '
        cls.NoticeStart = 'NOTICE: '

    def setUp(self):
        self.cmd = EOS_read.EosSetSpantreeAutoedgeCommand(self.mockSwitch)

    def test_default(self):
        line = 'foo'
        expected = self.NoticeStart + \
            'Ignoring unknown command "set spantree autoedge ' + line + '"'

        result = self.cmd.onecmd(line)

        self.assertEqual(expected, result)

    def test_change_autoedge_fail_wrong_cmd(self):
        cmd = 'foo'
        expected = self.ErrorStart + \
            'Wrong command "' + cmd + '" to _change_autoedge()'

        result = self.cmd._change_autoedge(cmd, '')

        self.assertEqual(expected, result)

    def test_change_autoedge_fail_arg_set(self):
        cmd, arg = 'enable', 'foo'
        expected = self.ErrorStart + \
            'Unknown argument "' + arg + '" to command ' + \
            '"set spantree autoedge ' + cmd + '"'

        result = self.cmd._change_autoedge(cmd, arg)

        self.assertEqual(expected, result)

    def test_change_autoedge_fail_no_ports_on_switch(self):
        cmd, arg = 'enable', ''
        self.mockSwitch.get_ports.return_value = []
        self.mockSwitch.get_lags.return_value = []
        expected = self.ErrorStart + \
            'Cannot configure Auto Edge on switch without ports'

        result = self.cmd._change_autoedge(cmd, arg)

        self.assertEqual(expected, result)

    def test_change_autoedge_ok_enable(self):
        self.mockPort.reset_mock()
        cmd, arg = 'enable', ''
        self.mockSwitch.get_ports.return_value = [self.mockPort]
        expected = ''

        result = self.cmd._change_autoedge(cmd, arg)

        self.mockPort.set_stp_auto_edge.assert_called_once_with(True, 'config')
        self.assertEqual(expected, result)

    def test_change_autoedge_ok_disable(self):
        self.mockPort.reset_mock()
        cmd, arg = 'disable', ''
        self.mockSwitch.get_ports.return_value = [self.mockPort]
        expected = ''

        result = self.cmd._change_autoedge(cmd, arg)

        self.mockPort.set_stp_auto_edge.assert_called_once_with(False,
                                                                'config')
        self.assertEqual(expected, result)

    def test_do_enable(self):
        self.mockPort.reset_mock()
        arg = ''
        self.mockSwitch.get_ports.return_value = [self.mockPort]
        expected = ''

        result = self.cmd.do_enable(arg)

        self.mockPort.set_stp_auto_edge.assert_called_once_with(True, 'config')
        self.assertEqual(expected, result)

    def test_do_disable(self):
        self.mockPort.reset_mock()
        arg = ''
        self.mockSwitch.get_ports.return_value = [self.mockPort]
        expected = ''

        result = self.cmd.do_disable(arg)

        self.mockPort.set_stp_auto_edge.assert_called_once_with(False,
                                                                'config')
        self.assertEqual(expected, result)

if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
