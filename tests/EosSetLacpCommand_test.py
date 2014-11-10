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

# Copyright 2014 Extreme Networks, Inc.  All rights reserved.
# Use is subject to license terms.

# This file is part of e2x (translate EOS switch configuration to ExtremeXOS)

import unittest
import sys

sys.path.extend(['../src'])

import EOS_read
import Switch
import Port

from unittest.mock import MagicMock


class EosSetLacpCommand_test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.port1Name = 'ge.1.1'
        cls.mockPort1 = MagicMock(Port.Port)
        cls.mockPort1.get_name.return_value = cls.port1Name

        cls.mockSwitch = MagicMock(Switch.Switch)

        cls.ErrorStart = 'ERROR: '

    def setUp(self):
        self.cmd = EOS_read.EosSetLacpCommand(self.mockSwitch)
        self.mockSwitch.get_ports_by_name.return_value = [self.mockPort1]

    def test_default(self):
        confFragment = 'unknown'
        expected = \
            'NOTICE: Ignoring unknown command "set lacp ' + \
            confFragment + '"'

        result = self.cmd.onecmd(confFragment)

        self.assertEqual(expected, result)

    def test_do_aadminkey_fail_wrong_number_of_parameters(self):
        arg = 'ge.1.*'
        expected = self.ErrorStart + \
            '"set lacp aadminkey" needs two arguments'

        result = self.cmd.do_aadminkey(arg)

        self.assertEqual(expected, result)

    def test_do_aadminkey_fail_key_is_no_int(self):
        arg = 'ge.1.* foo'
        expected = self.ErrorStart + 'LACP actor key must be an integer'

        result = self.cmd.do_aadminkey(arg)

        self.assertEqual(expected, result)

    def test_do_aadminkey_fail_key_not_in_allowed_range(self):
        arg = 'ge.1.* 66000'
        expected = self.ErrorStart + 'LACP actor key must be in [0..65535]'

        result = self.cmd.do_aadminkey(arg)

        self.assertEqual(expected, result)

    def test_do_aadminkey_fail_port_not_found(self):
        portStr = 'ge.1.*'
        key = '65535'
        self.mockSwitch.get_ports_by_name.return_value = []
        expected = self.ErrorStart + \
            'Port ' + portStr + ' not found (set lacp aadminkey)'

        result = self.cmd.do_aadminkey(portStr + ' ' + str(key))

        self.assertEqual(expected, result)

    def test_do_aadminkey_fail_wrong_return_value_from_port_cmd(self):
        reason = 'config'
        key = 32768
        self.mockPort1.set_lacp_aadminkey.return_value = key - 1
        arg = 'ge.1.1 ' + str(key)
        expected = self.ErrorStart + \
            'Could not apply "set lacp aadminkey ' + arg + '"'

        result = self.cmd.do_aadminkey(arg)

        self.assertEqual(expected, result)
        self.mockPort1.set_lacp_aadminkey.assert_called_with(key, reason)

    def test_do_aadminkey_ok(self):
        reason = 'config'
        key = 32768
        self.mockPort1.set_lacp_aadminkey.return_value = key
        arg = 'ge.1.1 ' + str(key)
        expected = ''

        result = self.cmd.do_aadminkey(arg)

        self.assertEqual(expected, result)
        self.mockPort1.set_lacp_aadminkey.assert_called_with(key, reason)

    def test_do_disable_fail_arg_not_empty(self):
        arg = 'dont'
        confFragment = 'disable' + ' ' + arg
        expected = self.ErrorStart + \
            '"set lacp disable" takes no arguments'

        result = self.cmd.onecmd(confFragment)

        self.assertEqual(expected, result)

    def test_do_disable_fail_switch_function_returns_None(self):
        confFragment = 'disable'
        self.mockSwitch.set_lacp_support.return_value = None
        expected = self.ErrorStart + \
            'Could not apply "set lacp disable"'

        result = self.cmd.onecmd(confFragment)

        self.assertEqual(expected, result)

    def test_do_disable_fail_switch_function_returns_True(self):
        confFragment = 'disable'
        self.mockSwitch.set_lacp_support.return_value = True
        expected = self.ErrorStart + \
            'Could not apply "set lacp disable"'

        result = self.cmd.onecmd(confFragment)

        self.assertEqual(expected, result)

    def test_do_disable_ok(self):
        confFragment = 'disable'
        self.mockSwitch.set_lacp_support.return_value = False
        expected = ''

        result = self.cmd.onecmd(confFragment)

        self.assertEqual(expected, result)

    def test_do_enable_fail_arg_not_empty(self):
        arg = 'dont'
        confFragment = 'enable' + ' ' + arg
        expected = self.ErrorStart + \
            '"set lacp enable" takes no arguments'

        result = self.cmd.onecmd(confFragment)

        self.assertEqual(expected, result)

    def test_do_enable_fail_switch_function_returns_None(self):
        confFragment = 'enable'
        self.mockSwitch.set_lacp_support.return_value = None
        expected = self.ErrorStart + \
            'Could not apply "set lacp enable"'

        result = self.cmd.onecmd(confFragment)

        self.assertEqual(expected, result)

    def test_do_emable_fail_switch_function_returns_False(self):
        confFragment = 'enable'
        self.mockSwitch.set_lacp_support.return_value = False
        expected = self.ErrorStart + \
            'Could not apply "set lacp enable"'

        result = self.cmd.onecmd(confFragment)

        self.assertEqual(expected, result)

    def test_do_enable_ok(self):
        confFragment = 'enable'
        self.mockSwitch.set_lacp_support.return_value = True
        expected = ''

        result = self.cmd.onecmd(confFragment)

        self.assertEqual(expected, result)

    def test_do_static_fail_wrong_nr_of_parameter(self):
        arg = ' par1 par2'
        expected = self.ErrorStart + \
            'Unknown argument "' + arg + '" (set lacp static)'

        result = self.cmd.do_static(arg)

        self.assertEqual(expected, result)

    def test_do_static_fail_wrong_char_in_parameter(self):
        arg = ' lag.0.*'
        expected = self.ErrorStart + \
            'Unknown argument "' + arg + '" (set lacp static)'

        result = self.cmd.do_static(arg)

        self.assertEqual(expected, result)

    def test_do_static_fail_lag_not_found_on_switch(self):
        arg = ' lag.0.1'
        self.mockSwitch.get_ports_by_name.return_value = []
        expected = self.ErrorStart + \
            'LAG "' + arg + '" not found (set lacp static)'

        result = self.cmd.do_static(arg)

        self.assertEqual(expected, result)

    def test_do_static_fail_too_many_lags_found_on_switch(self):
        arg = ' lag.0.1'
        self.mockSwitch.get_ports_by_name.return_value = [self.mockPort1,
                                                          self.mockPort1]
        expected = self.ErrorStart + \
            '"set lacp static" accepts a single LAG only'

        result = self.cmd.do_static(arg)

        self.assertEqual(expected, result)

    def test_do_static_fail_lag_function_returns_none(self):
        arg = ' lag.0.1'
        self.mockSwitch.get_ports_by_name.return_value = [self.mockPort1]
        self.mockPort1.set_lacp_enabled.return_value = None
        expected = self.ErrorStart + \
            'Could not configure static LAG "' + arg + '"'

        result = self.cmd.do_static(arg)

        self.assertEqual(expected, result)

    def test_do_static_fail_lag_function_returns_true(self):
        arg = ' lag.0.1'
        self.mockSwitch.get_ports_by_name.return_value = [self.mockPort1]
        self.mockPort1.set_lacp_enabled.return_value = True
        expected = self.ErrorStart + \
            'Could not configure static LAG "' + arg + '"'

        result = self.cmd.do_static(arg)

        self.assertEqual(expected, result)

    def test_do_static_ok(self):
        arg = ' lag.0.1'
        self.mockSwitch.get_ports_by_name.return_value = [self.mockPort1]
        self.mockPort1.set_lacp_enabled.return_value = False
        expected = ''

        result = self.cmd.do_static(arg)

        self.assertEqual(expected, result)

    def test_do_singleportlag(self):
        line = 'dont'
        expected = \
            'NOTICE: Ignoring unknown command "set lacp singleportlag ' + \
            line + '"'

        result = self.cmd.do_singleportlag(line)

        self.assertEqual(expected, result)

if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
