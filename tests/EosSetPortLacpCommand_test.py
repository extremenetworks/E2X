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
import Port
import Switch

from unittest.mock import MagicMock


class EosSetPortLacpCommand_test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.port1Name = 'ge.1.1'
        cls.mockPort1 = MagicMock(Port.Port)

        cls.mockSwitch = MagicMock(Switch.Switch)

        cls.ErrorStart = 'ERROR: '
        cls.WarningStart = 'WARN: '
        cls.NoticeStart = 'NOTICE: '
        cls.InfoStart = 'INFO: '

    def setUp(self):
        self.cmd = EOS_read.EosSetPortLacpCommand(self.mockSwitch)
        self.mockSwitch.get_ports_by_name.return_value = [self.mockPort1]

    def tearDown(self):
        self.mockPort1.reset_mock()

    def test_default(self):
        line = 'foo'
        expected = self.NoticeStart + \
            'Ignoring unknown command "set port lacp ' + line + '"'

        result = self.cmd.onecmd(line)

        self.assertEqual(expected, result)

    def test_do_port_fail_no_arg(self):
        expected = self.ErrorStart + \
            '"set port lacp port" needs a port string'

        result = self.cmd.do_port('')

        self.assertEqual(expected, result)

    def test_do_port_fail_port_not_found(self):
        portStr = 'ge.1.*'
        self.mockSwitch.get_ports_by_name.return_value = []
        expected = self.ErrorStart + \
            'Port ' + portStr + ' not found (set port lacp port)'

        result = self.cmd.do_port(portStr)

        self.assertEqual(expected, result)

    def test_do_port_fail_too_few_args(self):
        arg = 'ge.1.*'
        expected = self.ErrorStart + \
            'incomplete command "set port lacp port ' + arg + '"'

        result = self.cmd.do_port(arg)

        self.assertEqual(expected, result)

    def test_do_port_fail_unknown_arg(self):
        arg = 'ge.1.* foo'
        expected = self.ErrorStart + \
            'unknown command "set port lacp port ' + arg + '"'

        result = self.cmd.do_port(arg)

        self.assertEqual(expected, result)

    def test_do_port_subcmd_enable_ok(self):
        enabled = True
        reason = 'config'
        self.mockPort1.set_lacp_enabled.return_value = enabled
        self.mockPort1.get_name.return_value = self.port1Name
        arg = 'ge.1.* enable'
        expected = ''

        result = self.cmd.do_port(arg)

        self.assertEqual(expected, result)
        self.mockPort1.set_lacp_enabled.assert_called_once_with(enabled,
                                                                reason)

    def test_do_port_subcmd_disable_ok(self):
        enabled = False
        reason = 'config'
        self.mockPort1.set_lacp_enabled.return_value = enabled
        self.mockPort1.get_name.return_value = self.port1Name
        arg = 'ge.1.* disable'
        expected = ''

        result = self.cmd.do_port(arg)

        self.assertEqual(expected, result)
        self.mockPort1.set_lacp_enabled.assert_called_once_with(enabled,
                                                                reason)

    def test_do_port_subcmd_aadminkey_fail_no_key(self):
        arg = 'ge.1.* aadminkey'
        expected = self.ErrorStart + '"set port lacp port ' + arg + \
            '" needs a key value'

        result = self.cmd.do_port(arg)

        self.assertEqual(expected, result)

    def test_do_port_subcmd_aadminkey_fail_key_is_no_int(self):
        arg = 'ge.1.* aadminkey foo'
        expected = self.ErrorStart + 'LACP actor key must be an integer'

        result = self.cmd.do_port(arg)

        self.assertEqual(expected, result)

    def test_do_port_subcmd_aadminkey_fail_key_not_in_allowed_range(self):
        arg = 'ge.1.* aadminkey 66000'
        expected = self.ErrorStart + 'LACP actor key must be in [0..65535]'

        result = self.cmd.do_port(arg)

        self.assertEqual(expected, result)

    def test_do_port_subcmd_aadminkey_ok(self):
        reason = 'config'
        key = 32768
        self.mockPort1.set_lacp_aadminkey.return_value = key
        arg = 'ge.1.* aadminkey ' + str(key)
        expected = ''

        result = self.cmd.do_port(arg)

        self.assertEqual(expected, result)
        self.mockPort1.set_lacp_aadminkey.assert_called_once_with(key, reason)

    def test_do_port_fail_wrong_return_value_from_port_cmd(self):
        reason = 'config'
        key = 32768
        self.mockPort1.set_lacp_aadminkey.return_value = key - 1
        arg = 'ge.1.* aadminkey ' + str(key)
        expected = self.ErrorStart + \
            'could not apply "set port lacp port ' + arg + '"'

        result = self.cmd.do_port(arg)

        self.assertEqual(expected, result)
        self.mockPort1.set_lacp_aadminkey.assert_called_once_with(key, reason)

    def test_do_port_subcmd_enable_fail_lacp_port(self):
        portName, cmd = 'lag.0.1', 'enable'
        portnameLst = [portName]
        self.mockPort1.get_name.return_value = 'lag.0.1'
        arg = portName + ' ' + cmd
        expected = self.InfoStart + \
            'LACPDUs cannot be disabled or enabled on LAG interfaces, ' + \
            'skipped port(s) ' + str(portnameLst) + \
            ' (command "set port lacp port ' + arg + '")'

        result = self.cmd.do_port(arg)

        self.assertEqual(expected, result)

if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
