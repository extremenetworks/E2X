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
import Port
import VLAN

from unittest.mock import Mock


class EosClearVlanCommand_test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.portName = 'ge.1.1'
        cls.mockSwitch = Mock(spec=Switch.Switch)
        cls.mockPort = Mock(spec=Port.Port)
        cls.mockPort.get_name.return_value = cls.portName
        cls.mockVlan = Mock(spec=VLAN.VLAN)

        cls.ErrorStart = 'ERROR: '
        cls.NoticeStart = 'NOTICE: '
        cls.WarningStart = 'WARN: '

    def setUp(self):
        self.cmd = EOS_read.EosClearVlanCommand(self.mockSwitch)

    def test_default(self):
        line = 'foo'
        expected = self.NoticeStart + \
            'Ignoring unknown command "clear vlan ' + line + '"'

        result = self.cmd.onecmd(line)

        self.assertEqual(expected, result)

    def test_do_egress_fail_missing_parameters(self):
        arg = ''
        expected = self.ErrorStart + \
            'Missing parameters for "clear vlan egress" command'

        result = self.cmd.do_egress(arg)

        self.assertEqual(expected, result)

    def test_do_egress_fail_wrong_number_of_parameters(self):
        arg = '1'
        expected = self.ErrorStart + \
            'Wrong number of arguments to "clear vlan egress"'

        result = self.cmd.do_egress(arg)

        self.assertEqual(expected, result)

    def test_do_egress_fail_wrong_vlan_tag(self):
        arg = 'a ' + self.portName
        expected = self.ErrorStart + \
            'VLAN tag must be an integer (clear vlan egress)'

        result = self.cmd.do_egress(arg)

        self.assertEqual(expected, result)

    def test_do_egress_fail_port_not_found(self):
        arg = '1 ' + self.portName
        self.mockSwitch.get_ports_by_name.return_value = []
        expected = self.ErrorStart + \
            'Port ' + self.portName + ' not found (clear vlan egress)'

        result = self.cmd.do_egress(arg)

        self.assertEqual(expected, result)

    def test_do_egress_fail_vlan_not_found(self):
        tag = '1'
        arg = tag + ' ' + self.portName
        self.mockSwitch.get_ports_by_name.return_value = [self.mockPort]
        self.mockSwitch.get_vlan.return_value = None
        expected = self.ErrorStart + \
            'VLAN ' + tag + ' not found (clear vlan egress)'

        result = self.cmd.do_egress(arg)

        self.assertEqual(expected, result)

    def test_do_egress_ok(self):
        tag = '1'
        arg = tag + ' ' + self.portName
        self.mockSwitch.get_ports_by_name.return_value = [self.mockPort]
        self.mockSwitch.get_vlan.return_value = self.mockVlan

        expected = ''

        result = self.cmd.do_egress(arg)

        self.assertEqual(expected, result)
        self.mockVlan.del_egress_port.assert_called_once_with(self.portName,
                                                              'all')

if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
