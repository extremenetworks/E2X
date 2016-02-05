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

from EOS_read import EosIpCommand
from Switch import Switch
from VLAN import VLAN

from unittest.mock import Mock


class EosIpCommand_test(unittest.TestCase):

    def setUp(self):
        self.switch = Switch()
        vlan = VLAN('vlan1', 1, None)
        self.switch.add_vlan(vlan)
        self.cmd = EosIpCommand(None, self.switch)

    def test_default_unknownCommand(self):
        argStr = 'unknown'

        result = self.cmd.onecmd(argStr)

        self.assertIn('NOTICE', result)
        self.assertIn('unknown command', result)

    def test_default_accessGroup(self):
        argStr = 'access-group'
        self.cmd._do_access_group = Mock(return_value=None)

        self.cmd.onecmd(argStr)

        self.assertEqual(1, self.cmd._do_access_group.call_count)

    def test_do_access_group_noArgument(self):

        result = self.cmd._do_access_group('')

        self.assertIn('ERROR', result)
        self.assertIn('argument', result)

    def test_do_access_group_statementOccursOutsideRouterInterfaceMode(self):

        # TO-DO Is state correctly handled?

        result = self.cmd._do_access_group('1')

        self.assertIn('ERROR', result)
        self.assertIn('router interface', result)

    def test_set_state(self):
        old_state = self.cmd._state

        self.assertNotEqual(old_state, self.cmd.set_state('interface'))

    def test_do_access_group_invalidInterface(self):

        self.cmd.set_state(('router', 'config', 'interface ge.1.1'))

        result = self.cmd._do_access_group('1')

        self.assertIn('ERROR', result)
        self.assertIn('unknown interface', result)

    def test_do_access_group_InterfaceIsLoopback(self):

        self.cmd.set_state(('router', 'config', 'interface loopback 3'))

        result = self.cmd._do_access_group('1')

        self.assertIn('ERROR', result)
        self.assertIn('ACLs', result)
        self.assertIn('loopback interface', result)

    def test_do_access_group_InterfaceVlanIdIsInvalid(self):

        self.cmd.set_state(('router', 'config', 'interface vlan 0'))

        result = self.cmd._do_access_group('1')

        self.assertIn('ERROR', result)
        self.assertIn('Illegal VLAN ID', result)

    def test_do_access_group_sequenceIsIgnored(self):

        self.cmd.set_state(('router', 'config', 'interface vlan 1'))

        result = self.cmd._do_access_group(('1', 'sequence', '1'))

        self.assertIn('WARN', result)
        self.assertIn('Ignoring', result)
        self.assertIn('sequence', result)
        self.assertIn('in', result)

    def test_do_access_group_vlanDoesNotExist(self):

        self.cmd.set_state(('router', 'config', 'interface vlan 2'))

        result = self.cmd._do_access_group('1')

        self.assertIn('ERROR', result)
        self.assertIn('exist', result)

    def test_do_access_group_invalidACLNumber(self):

        self.cmd.set_state(('router', 'config', 'interface vlan 1'))

        result = self.cmd._do_access_group('a')

        self.assertIn('NOTICE', result)
        self.assertIn('unknown command', result)

    def test_do_access_group_unsupportedDirection(self):

        self.cmd.set_state(('router', 'config', 'interface vlan 1'))

        result = self.cmd._do_access_group(('1', 'out'))

        self.assertIn('ERROR', result)
        self.assertIn('direction', result)

    #####
    #####

    def test_default_helperAddress(self):
        argStr = 'helper-address'
        self.cmd._do_helper_address = Mock(return_value=None)

        self.cmd.onecmd(argStr)

        self.assertEqual(1, self.cmd._do_helper_address.call_count)

    def test_do_helper_address_noArgument(self):

        result = self.cmd._do_helper_address('')

        self.assertIn('ERROR', result)
        self.assertIn('argument', result)

    def test_do_helper_address_excessArgument(self):
        arg_list = ['192.0.2.47', 'excess arg']

        result = self.cmd._do_helper_address(arg_list)

        self.assertIn('NOTICE', result)
        self.assertIn('unknown', result)
        self.assertIn('excess', result)

    def test_do_helper_address_statementOccursOutsideRouterInterfaceMode(self):
        arg_list = ['192.0.2.47']

        result = self.cmd._do_helper_address(arg_list)

        self.assertIn('ERROR', result)
        self.assertIn('router interface', result)

    def test_do_helper_address_unknownInterface(self):
        arg_list = ['192.0.2.47']
        self.cmd.set_state(('router', 'interface'))

        result = self.cmd._do_helper_address(arg_list)

        self.assertIn('ERROR', result)
        self.assertIn('unknown interface', result)

    def test_do_helper_address_interfaceIsLoopback(self):
        arg_list = ['192.0.2.47']
        self.cmd.set_state(('router', 'interface loopback 3'))

        result = self.cmd._do_helper_address(arg_list)

        self.assertIn('ERROR', result)
        self.assertIn('loopback interface', result)

    def test_do_helper_address_interfaceIsVLANwithIDNull(self):
        arg_list = ['192.0.2.47']
        self.cmd.set_state(('router', 'interface vlan -1'))

        result = self.cmd._do_helper_address(arg_list)

        self.assertIn('ERROR', result)
        self.assertIn('Illegal', result)
        self.assertIn('-1', result)

    def test_do_helper_address_interfaceIsVLANwithID4096(self):
        arg_list = ['192.0.2.47']
        self.cmd.set_state(('router', 'interface vlan 4096'))

        result = self.cmd._do_helper_address(arg_list)

        self.assertIn('ERROR', result)
        self.assertIn('Illegal', result)
        self.assertIn('4096', result)

    def test_do_helper_address_interfaceIsVLANNotDefinedForSwitch(self):
        arg_list = ['192.0.2.47']
        self.cmd.set_state(('router', 'interface vlan 4095'))

        result = self.cmd._do_helper_address(arg_list)

        self.assertIn('ERROR', result)
        self.assertIn('does not exist', result)
        self.assertIn('4095', result)

    def test_do_helper_address_invalidIPv4Address(self):
        arg_list = ['192.0.2.477']
        self.cmd.set_state(('router', 'interface vlan 1'))

        result = self.cmd._do_helper_address(arg_list)

        self.assertIn('ERROR', result)
        self.assertIn('invalid', result)
        self.assertIn('477', result)

    def test_do_helper_address_sucess(self):
        arg_list = ['192.0.2.47']
        self.cmd.set_state(('router', 'interface vlan 2'))
        vlan2_mock = Mock(spec=VLAN)
        vlan2_mock.get_tag.return_value = 2
        self.switch.add_vlan(vlan2_mock)

        result = self.cmd._do_helper_address(arg_list)

        self.assertEqual('', result)
        vlan2_mock.add_ipv4_helper_address.assert_called_once_with(arg_list[0])

    def test_do_address(self):
        confFragment = 'address'
        self.cmd.do_address = Mock(return_value=None)

        self.cmd.onecmd(confFragment)

        self.assertEqual(1, self.cmd.do_address.call_count)

    def test_do_address_noArgument(self):

        result = self.cmd.do_address('')

        self.assertIn('ERROR', result)
        self.assertIn('argument', result)

    def test_do_address_statementOccursOutsideRouterInterfaceMode(self):
        arg_str = '192.0.2.47'

        result = self.cmd.do_address(arg_str)

        self.assertIn('ERROR', result)
        self.assertIn('router interface', result)

    def test_do_address_argumentTooSmall(self):
        arg_str = '192.0.2.47'
        self.cmd.set_state(('router', 'interface vlan 2'))

        result = self.cmd.do_address(arg_str)

        self.assertIn('NOTICE', result)
        self.assertIn('unknown command', result)

    def test_do_address_WrongArgument(self):
        arg_str = '192.0.2.77 255.255.256.0'
        self.cmd.set_state(('router', 'interface vlan 2'))

        result = self.cmd.do_address(arg_str)

        self.assertIn('NOTICE', result)
        self.assertIn('unknown command', result)
        self.assertIn('invalid IPv4 address', result)

    def test_do_address_interfaceIsNotVLANOrLoopback(self):
        arg_str = '192.0.2.77 255.255.255.0'
        self.cmd.set_state(('router', 'interface ge.1.1 2'))

        result = self.cmd.do_address(arg_str)

        self.assertIn('ERROR', result)
        self.assertIn('unknown interface', result)

    def test_do_address_interfaceInvalidVlanId(self):
        arg_str = '192.0.2.77 255.255.255.0'
        self.cmd.set_state(('router', 'interface vlan 0'))

        result = self.cmd.do_address(arg_str)

        self.assertIn('ERROR', result)
        self.assertIn('Illegal VLAN ID', result)

    def test_do_address_interfaceInvalidLoopbackNumber(self):
        arg_str = '192.0.2.77 255.255.255.0'
        self.cmd.set_state(('router', 'interface loopback 8'))

        result = self.cmd.do_address(arg_str)

        self.assertIn('ERROR', result)
        self.assertIn('Illegal Loopback ID', result)

    def test_do_address_interfaceNotDefinedForSwitch(self):
        arg_str = '192.0.2.77 255.255.255.0'
        self.cmd.set_state(('router', 'interface loopback 2'))

        result = self.cmd.do_address(arg_str)

        self.assertIn('ERROR', result)
        self.assertIn('Interface', result)
        self.assertIn('not defined', result)

    def test_do_address_vlanOk(self):
        arg_str = '192.0.2.77 255.255.255.0'
        self.cmd.set_state(('router', 'interface vlan 1'))

        result = self.cmd.do_address(arg_str)

        self.assertEqual('', result)

    def test_do_address_loopbackOk(self):
        arg_str = '192.0.2.77 255.255.255.0'
        self.cmd.set_state(('router', 'interface loopback 0'))
        self.switch.add_loopback(0)

        result = self.cmd.do_address(arg_str)

        self.assertEqual('', result)

    #####
    #####

    def test_do_routing(self):
        confFragment = 'routing'
        self.cmd.do_routing = Mock(return_value=None)

        self.cmd.onecmd(confFragment)

        self.assertEqual(1, self.cmd.do_routing.call_count)

    def test_do_routing_unknownArg(self):

        result = self.cmd.do_routing('arg')

        self.assertIn('NOTICE', result)
        self.assertIn('Ignoring unknown', result)

    def test_do_routing_ok(self):

        result = self.cmd.do_routing('')

        self.assertEqual('', result)

    #####
    #####

    def test_do_route(self):
        confFragment = 'route'
        self.cmd.do_route = Mock(return_value=None)

        self.cmd.onecmd(confFragment)

        self.assertEqual(1, self.cmd.do_route.call_count)

    def test_do_route_noArg(self):

        result = self.cmd.do_route('')

        self.assertIn('ERROR', result)
        self.assertIn('needs argument', result)

    def test_do_route_statementOccursOutsideRouterConfigureMode(self):
        argStr = '192.0.3.0 255.255.255.0 192.0.2.77'

        result = self.cmd.do_route(argStr)

        self.assertIn('INFO', result)
        self.assertIn('outside', result)

    def test_do_route_wrongNrOfArg(self):
        argStr = '192.0.3.477 255.255.255.0'

        result = self.cmd.do_route(argStr)

        self.assertIn('NOTICE', result)
        self.assertIn('unknown', result)

    def test_do_route_wrongTypeOfArg(self):
        argStr = '192.0.a.77 255.255.255.0 192.0.2.77'

        result = self.cmd.do_route(argStr)

        self.assertIn('NOTICE', result)
        self.assertIn('unknown', result)

    def test_do_route_wrongIpAddress(self):
        argStr = '192.0.3.77 255.255.256.0 192.0.2.77'

        result = self.cmd.do_route(argStr)

        self.assertIn('NOTICE', result)
        self.assertIn('invalid', result)

    def test_do_route_ok(self):
        argStr = '192.0.3.77 255.255.255.0 192.0.2.77'
        self.cmd.set_state(('router', 'configure'))

        result = self.cmd.do_route(argStr)

        self.assertEqual('', result)

if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
