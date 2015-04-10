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

from unittest.mock import Mock, call

from Switch import Switch
from Port import Port
import VLAN
from VLAN import VLAN

import EOS_read


class EosSetPortCommand_test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.portCmd = 'ge.1.1'
        cls.mockPort = Mock(spec=Port)

        cls.mockSwitch = Mock(spec=Switch)
        cls.mockSwitch.get_ports_by_name.return_value = \
            [cls.mockPort, cls.mockPort]

        cls.ErrorStart = 'ERROR: '
        cls.WarningStart = 'WARN: '
        cls.NoticeStart = 'NOTICE: '
        cls.PortNotFound = cls.ErrorStart + 'Port ' + cls.portCmd + \
            ' not found (set port {})'
        cls.FailMessage = cls.ErrorStart + 'Could not {} port ' + \
            cls.portCmd

    def setUp(self):
        self.cmd = EOS_read.EosSetPortCommand(self.mockSwitch)

    def tearDown(self):
        self.mockPort.reset_mock()

    def test_default(self):
        line = 'foo'
        expected = self.NoticeStart + \
            'Ignoring unknown command "set port ' + line + '"'

        result = self.cmd.onecmd(line)

        self.assertEqual(expected, result)

    def test_do_enable_disable_port_not_found(self):
        expectedEnable = self.PortNotFound.format('enable')
        expectedDisable = self.PortNotFound.format('disable')

        self.mockSwitch.get_ports_by_name.return_value = []

        resultEnable = self.cmd.do_enable(self.portCmd)
        resultDisable = self.cmd.do_disable(self.portCmd)

        self.assertEqual(expectedEnable, resultEnable)
        self.assertEqual(expectedDisable, resultDisable)

    def test_doEnable_enable_fail(self):
        expected = self.FailMessage.format('enable')
        self.mockSwitch.get_ports_by_name.return_value = [self.mockPort]
        self.mockPort.get_name.return_value = self.portCmd
        self.mockPort.set_admin_state.return_value = False

        result = self.cmd.do_enable(self.portCmd)

        self.mockPort.set_admin_state.assert_called_once_with(True, 'config')
        self.assertEqual(expected, result)

    def test_doEnable_ok(self):
        expected = ''
        self.mockSwitch.get_ports_by_name.return_value = [self.mockPort,
                                                          self.mockPort]
        self.mockPort.set_admin_state.return_value = True

        result = self.cmd.do_enable(self.portCmd)

        self.mockPort.set_admin_state.call_count = 2
        self.assertEqual(expected, result)

    def test_doDisable_disable_fail(self):
        expected = self.FailMessage.format('disable')
        self.mockSwitch.get_ports_by_name.return_value = [self.mockPort]
        self.mockPort.get_name.return_value = self.portCmd
        self.mockPort.set_admin_state.return_value = True

        result = self.cmd.do_disable(self.portCmd)

        self.mockPort.set_admin_state.assert_called_once_with(False, 'config')
        self.assertEqual(expected, result)

    def test_doDisable_ok(self):
        expected = ''
        self.mockSwitch.get_ports_by_name.return_value = [self.mockPort,
                                                          self.mockPort]
        self.mockPort.set_admin_state.return_value = False

        result = self.cmd.do_disable(self.portCmd)

        self.mockPort.set_admin_state.call_count = 2
        self.assertEqual(expected, result)

    def test_doSpeed(self):
        arg = 'ge.1.1 100'

        # argument too long
        result = self.cmd.do_speed(arg + ' too much')

        self.assertTrue(result.startswith(self.ErrorStart))

        # port not found
        self.mockSwitch.get_ports_by_name.return_value = []

        result = self.cmd.do_speed(arg)

        self.assertTrue(result.startswith(self.ErrorStart))

        # setting failed
        self.mockSwitch.get_ports_by_name.return_value = [self.mockPort]
        self.mockPort.set_speed.return_value = False

        result = self.cmd.do_speed(arg)

        self.assertTrue(result.startswith(self.ErrorStart))

        # ok
        self.mockPort.set_speed.return_value = True

        result = self.cmd.do_speed(arg)

        self.assertTrue(len(result) == 0)

    def test_doDuplex(self):
        arg = 'ge.1.1 half'

        # argument too long
        result = self.cmd.do_duplex(arg + ' too much')

        self.assertTrue(result.startswith(self.ErrorStart))

        # port not found
        self.mockSwitch.get_ports_by_name.return_value = []

        result = self.cmd.do_duplex(arg)

        self.assertTrue(result.startswith(self.ErrorStart))

        # setting failed
        self.mockSwitch.get_ports_by_name.return_value = [self.mockPort]
        self.mockPort.set_duplex.return_value = 'full'

        result = self.cmd.do_duplex(arg)

        self.assertTrue(result.startswith(self.ErrorStart))

        # ok
        self.mockPort.set_duplex.return_value = 'half'

        result = self.cmd.do_duplex(arg)

        self.assertEqual('', result)

    def test_doNegotiation(self):
        autoNegotiation = 'enable'
        port = 'ge.1.1 '
        arg = port + autoNegotiation

        # argument too long
        result = self.cmd.do_negotiation(arg + ' too much')

        self.assertTrue(result.startswith(self.ErrorStart))

        # argument unknown
        result = self.cmd.do_negotiation(port + 'foo')

        self.assertTrue(result.startswith(self.ErrorStart))

        # port not found
        self.mockSwitch.get_ports_by_name.return_value = []

        result = self.cmd.do_negotiation(arg)

        self.assertTrue(result.startswith(self.ErrorStart))

        # setting failed enable
        self.mockSwitch.get_ports_by_name.return_value = [self.mockPort]
        self.mockPort.set_auto_neg.return_value = False

        result = self.cmd.do_negotiation(arg)

        self.assertTrue(result.startswith(self.ErrorStart))

        # setting failed disable
        self.mockSwitch.get_ports_by_name.return_value = [self.mockPort]
        self.mockPort.set_auto_neg.return_value = True
        arg = port + 'disable'

        result = self.cmd.do_negotiation(arg)

        self.assertTrue(result.startswith(self.ErrorStart))

        # ok enable
        self.mockPort.set_auto_neg.return_value = True
        arg = port + 'enable'

        result = self.cmd.do_negotiation(arg)

        self.assertEqual('', result)

        # ok disable
        arg = port + 'disable'
        self.mockPort.set_auto_neg.return_value = False

        result = self.cmd.do_negotiation(arg)

        self.assertEqual('', result)

    def test_do_jumbo(self):
        self.cmd._set_port_jumbo.onecmd = Mock()
        arg = 'foo'

        self.cmd.do_jumbo(arg)

        self.cmd._set_port_jumbo.onecmd.assert_called_once_with(arg)

    def test_do_lacp(self):
        self.cmd._set_port_lacp.onecmd = Mock()
        arg = 'foo'

        self.cmd.do_lacp(arg)

        self.cmd._set_port_lacp.onecmd.assert_called_once_with(arg)

    def test_do_alias_arg_separation(self):
        reason = 'config'
        arg = self.portCmd
        self.mockSwitch.get_ports_by_name.return_value = [self.mockPort]

        self.cmd.do_alias(arg)

        self.mockPort.set_description.assert_called_once_with('', reason)
        self.mockPort.set_short_description.assert_called_once_with('', reason)
        self.mockPort.reset_mock()

        description = 'this is a very long description'
        alias = 'this is a very '
        arg = self.portCmd + ' ' + description

        self.cmd.do_alias(arg)

        self.mockPort.set_description.assert_called_once_with(description,
                                                              reason)
        self.mockPort.set_short_description.assert_called_once_with(alias,
                                                                    reason)

    def test_do_alias_port_not_found(self):
        arg = self.portCmd
        expected = self.PortNotFound.format('alias')
        self.mockSwitch.get_ports_by_name.return_value = []

        result = self.cmd.do_alias(arg)

        self.assertEqual(result, expected)

    def test_do_alias_description_set_fails(self):
        arg = self.portCmd
        expected = self.ErrorStart + 'Could not set description on ' + arg
        self.mockSwitch.get_ports_by_name.return_value = [self.mockPort]
        self.mockPort.set_description.return_value = None

        result = self.cmd.do_alias(arg)

        self.assertEqual(result, expected)

    def test_do_vlan_fail_wrong_number_of_arguments(self):
        arg = self.portCmd
        expected = self.ErrorStart + \
            'Wrong number of arguments to "set port vlan": '

        result = self.cmd.do_vlan(arg)

        self.assertTrue(result.startswith(expected))

        arg = self.portCmd + ' 1 modify-egress none'

        result = self.cmd.do_vlan(arg)

        self.assertTrue(result.startswith(expected))

    def test_do_vlan_fail_unknown_argument(self):
        modify = 'mod-egress'
        arg = self.portCmd + ' 1 ' + modify
        expected = self.ErrorStart + 'unknown argument ' + modify

        result = self.cmd.do_vlan(arg)

        self.assertTrue(result.startswith(expected))

    def test_do_vlan_fail_unknown_port(self):
        arg = self.portCmd + ' 1 modify-egress'
        self.mockSwitch.get_ports_by_name.return_value = []
        expected = self.PortNotFound.format('vlan')

        result = self.cmd.do_vlan(arg)

        self.assertEqual(expected, result)

    def test_do_vlan_fail_no_such_vlan(self):
        tag = '1'
        arg = self.portCmd + ' ' + tag + ' modify-egress'
        self.mockSwitch.get_ports_by_name.return_value = [self.mockPort]
        self.mockSwitch.get_vlan.return_value = None
        expected = self.ErrorStart + 'VLAN ' + tag + ' not found ' + \
            '(set port vlan)'

        result = self.cmd.do_vlan(arg)

        self.assertEqual(expected, result)

    def test_do_vlan_ok_no_modify_egress(self):
        tag = '1'
        arg = self.portCmd + ' ' + tag
        self.mockSwitch.get_ports_by_name.return_value = [self.mockPort]
        mockVlan = Mock(spec=VLAN)
        self.mockSwitch.get_vlan.return_value = mockVlan
        self.mockSwitch.get_all_vlans.return_value = [mockVlan]
        mockVlan.get_tag.return_value = int(tag)
        expected = ''

        result = self.cmd.do_vlan(arg)

        self.assertEqual(expected, result)
        mockVlan.del_ingress_port.assert_called_once_with(self.portCmd,
                                                          'untagged')
        mockVlan.add_ingress_port.assert_called_once_with(self.portCmd,
                                                          'untagged')

    def test_do_vlan_ok_modify_egress(self):
        tag = '1'
        arg = self.portCmd + ' ' + tag + ' modify-egress'
        self.mockSwitch.get_ports_by_name.return_value = [self.mockPort]
        mockVlan = Mock(spec=VLAN)
        self.mockSwitch.get_vlan.return_value = mockVlan
        self.mockSwitch.get_all_vlans.return_value = [mockVlan]
        expected = ''
        methodCalls = [call.del_ingress_port(self.portCmd, 'untagged'),
                       call.del_egress_port(self.portCmd, 'all'),
                       call.add_ingress_port(self.portCmd, 'untagged'),
                       call.add_egress_port(self.portCmd, 'untagged')]

        result = self.cmd.do_vlan(arg)

        self.assertEqual(expected, result)
        self.assertEqual(methodCalls, mockVlan.method_calls)

if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
