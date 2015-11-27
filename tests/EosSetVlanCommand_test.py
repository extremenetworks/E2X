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
import Switch
import VLAN
import Port

from unittest.mock import MagicMock, patch


class EosSetVlanCommand_test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.portString = 'ge.1.1'
        cls.mockSwitch = MagicMock(spec=Switch.Switch)
        cls.mockPort = MagicMock(spec=Port.Port)
        cls.mockPort.get_name.return_value = cls.portString
        cls.mockVlan = MagicMock(spec=VLAN.VLAN)()

        cls.ErrorStart = 'ERROR: '
        cls.WarningStart = 'WARN: '
        cls.NoticeStart = 'NOTICE: '

    def setUp(self):
        self.cmd = EOS_read.EosSetVlanCommand(self.mockSwitch)

    def tearDown(self):
        self.mockSwitch.reset_mock()

    def test_default(self):
        line = 'foo'
        expected = self.NoticeStart + \
            'Ignoring unknown command "set vlan ' + line + '"'

        result = self.cmd.onecmd(line)

        self.assertEqual(expected, result)

    def test_do_create_fail_missing_tag(self):
        arg = None
        expected = self.ErrorStart + \
            'Missing VLAN tag in "set vlan create" command'

        result = self.cmd.do_create(arg)

        self.assertEqual(expected, result)

    def test_do_create_fail_vlan_tag_not_int(self):
        arg = 'a'
        expected = self.ErrorStart + \
            'VLAN tag must be an integer (set vlan create)'

        result = self.cmd.do_create(arg)

        self.assertEqual(expected, result)

    def test_do_create_fail_vlan_tag_out_of_range(self):
        arg = '4097'
        expected = self.ErrorStart + \
            'VLAN tag must be in [1,4095], but is ' + arg

        result = self.cmd.do_create(arg)

        self.assertEqual(expected, result)

    def test_do_create_ok(self):
        arg = '100'
        expected = ''

        with patch('VLAN.VLAN') as vlan:
            vlan.return_value = self.mockVlan

            result = self.cmd.do_create(arg)

            vlan.assert_called_once_with(switch=self.mockSwitch, tag=int(arg))
            self.mockSwitch.add_vlan.assert_called_once_with(self.mockVlan)

        self.assertEqual(expected, result)

    def test_do_name_fail_tag_not_int_name_not_empty(self):
        arg = 'a foo'
        expected = self.ErrorStart + \
            'VLAN tag must be an integer (set vlan name a foo)'

        result = self.cmd.do_name(arg)

        self.assertEqual(expected, result)

    def test_do_name_fail_tag_not_int_name_empty(self):
        arg = 'a'
        expected = self.ErrorStart + \
            'VLAN tag must be an integer (set vlan name a)'

        result = self.cmd.do_name(arg)

        self.assertEqual(expected, result)

    def test_do_name_fail_vlan_not_found(self):
        arg = '100'
        self.mockSwitch.get_vlan.return_value = []
        expected = self.ErrorStart + \
            'VLAN ' + arg + ' not found (set vlan name 100)'

        result = self.cmd.do_name(arg)

        self.assertEqual(expected, result)

    def test_do_name_ok_name_empty(self):
        arg = '100'
        self.mockSwitch.get_vlan.return_value = self.mockVlan
        expected = ''

        result = self.cmd.do_name(arg)

        self.mockVlan.set_name.assert_called_once_with('')
        self.mockSwitch.get_vlan.assert_called_once_with(tag=int(arg))
        self.assertEqual(expected, result)

    def test_do_name_ok_name_with_double_quotes(self):
        tag, name = '100', 'foo'
        arg = tag + ' ' + '"' + name + ""
        self.mockSwitch.get_vlan.return_value = self.mockVlan
        expected = ''

        result = self.cmd.do_name(arg)

        self.mockVlan.set_name.assert_called_once_with(name)
        self.mockSwitch.get_vlan.assert_called_once_with(tag=int(tag))
        self.assertEqual(expected, result)

    def test_do_name_ok_name_not_empty_trailing_space(self):
        tag, name = '100', 'foo'
        arg = tag + ' ' + name + ' '
        self.mockSwitch.get_vlan.return_value = self.mockVlan
        expected = ''

        result = self.cmd.do_name(arg)

        self.mockVlan.set_name.assert_called_once_with(name + ' ')
        self.mockSwitch.get_vlan.assert_called_once_with(tag=int(tag))
        self.assertEqual(expected, result)

    def test_do_egress_fail_missing_parameters(self):
        arg = ''
        expected = self.ErrorStart + \
            'Missing parameters for "set vlan egress" command'

        result = self.cmd.do_egress(arg)

        self.assertEqual(expected, result)

    def test_do_egress_fail_wrong_number_of_parameters(self):
        arg = '1'
        expected = self.ErrorStart + \
            'Wrong number of arguments to "set vlan egress"'

        result = self.cmd.do_egress(arg)

        self.assertEqual(expected, result)

    def test_do_egress_fail_wrong_vlan_tag(self):
        arg = 'a ' + self.portString
        expected = self.ErrorStart + \
            'VLAN tag must be an integer (set vlan egress)'

        result = self.cmd.do_egress(arg)

        self.assertEqual(expected, result)

    def test_do_egress_fail_port_not_found(self):
        arg = '1 ' + self.portString
        self.mockSwitch.get_ports_by_name.return_value = []
        expected = self.ErrorStart + \
            'Port ' + self.portString + ' not found (set vlan egress)'

        result = self.cmd.do_egress(arg)

        self.assertEqual(expected, result)

    def test_do_egress_fail_vlan_not_found(self):
        tag = '1'
        arg = tag + ' ' + self.portString
        self.mockSwitch.get_ports_by_name.return_value = [self.mockPort]
        self.mockSwitch.get_vlan.return_value = None
        expected = self.ErrorStart + \
            'VLAN ' + tag + ' not found (set vlan egress)'

        result = self.cmd.do_egress(arg)

        self.assertEqual(expected, result)

    def test_do_egress_ok_tagged_not_set(self):
        tag = '1'
        arg = tag + ' ' + self.portString
        self.mockSwitch.get_ports_by_name.return_value = [self.mockPort]
        self.mockSwitch.get_vlan.return_value = self.mockVlan

        expected = ''

        result = self.cmd.do_egress(arg)

        self.assertEqual(expected, result)
        self.mockVlan.add_egress_port.assert_called_once_with(self.portString,
                                                              'tagged')

    def test_do_egress_ok_tagged_set(self):
        tag, tagged = '1', 'untagged'
        arg = tag + ' ' + self.portString + ' ' + tagged
        self.mockSwitch.get_ports_by_name.return_value = [self.mockPort]
        self.mockSwitch.get_vlan.return_value = self.mockVlan

        expected = ''

        result = self.cmd.do_egress(arg)

        self.assertEqual(expected, result)
        self.mockVlan.add_egress_port.assert_called_once_with(self.portString,
                                                              tagged)
if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
