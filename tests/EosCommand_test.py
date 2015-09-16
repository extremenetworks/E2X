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
from unittest.mock import MagicMock
import sys

sys.path.extend(['../src'])

from EOS_read import EosCommand

from Switch import Switch
from Port import Port
from ACL import ACL, Standard_ACE


class EosCommand_test(unittest.TestCase):

    def setUp(self):
        self.cmd = EosCommand(None)

    def test_default_shouldForward2doAccessList(self):
        self.cmd._do_access_list = MagicMock()
        config_line = "access-list"

        self.cmd.default(config_line)

        self.cmd._do_access_list.assert_called_once_with([])

    def test_default_shouldOutputBrokenConfigLine(self):
        config_line = "access-list 1 permit unknown"

        result = self.cmd.default(config_line)

        self.assertRegex(result, '^ERROR:.*' + config_line + '"$')

    def test_default_shouldOutputEmptyStringIfSuccess(self):
        self.cmd._do_access_list = MagicMock()
        self.cmd._do_access_list.return_value = ''

        config_line = "access-list 1 permit any"

        result = self.cmd.default(config_line)

        self.assertEqual('', result)

    def test_do_router_ok(self):

        self.assertEqual('', self.cmd.do_router(''))

    def test_do_router_unexpectedArgumentIsUnknownCommand(self):

        self.assertIn('NOTICE: Ignoring unknown command',
                      self.cmd.do_router('not empty'))

    def test_do_router_statementOccursInRouterConfModeShouldInform(self):
        self.cmd.do_router('')

        self.assertIn('INFO', self.cmd.do_router(''))

    def test_do_exit_ok(self):
        self.cmd.do_router('')

        self.assertEqual('', self.cmd.do_exit(''))

    def test_do_exit_unexpectedArgumentShouldFail(self):
        self.cmd.do_router('')

        self.assertIn('ERROR', self.cmd.do_exit('not empty'))

    def test_do_exit_statementOccursInBaseModeShouldInform(self):

        self.assertIn('INFO', self.cmd.do_exit(''))

    def test_do_enable_ok(self):
        self.cmd.do_router('')

        self.assertEqual('', self.cmd.do_enable(''))

    def test_do_enable_unexpectedArgumentShouldFailWithNotice(self):
        self.cmd.do_router('')

        self.assertIn(
            'NOTICE: Ignoring unknown command',
            self.cmd.do_enable('not empty'))

    def test_do_enable_statementOccursOutsideRouterModeShouldInform(self):

        result = self.cmd.do_enable('')

        self.assertIn('INFO', result)
        self.assertIn('enable', result)

    def test_do_configure_ok(self):
        self.cmd.do_router('')
        self.cmd.do_enable('')

        self.assertEqual('', self.cmd.do_configure(''))

    def test_do_configure_terminal_ok(self):
        self.cmd.do_router('')
        self.cmd.do_enable('')

        self.assertEqual('', self.cmd.do_configure('terminal'))

    def test_do_configure_not_empty_unknown_fail(self):
        self.cmd.do_router('')
        self.cmd.do_enable('')

        self.assertEqual(
            'NOTICE: Ignoring unknown command "configure not empty"',
            self.cmd.do_configure('not empty'))

    def test_do_configure_statementOccursOutsideEnableModeShouldInform(self):
        self.cmd.do_router('')

        result = self.cmd.do_configure('')

        self.assertIn('INFO', result)
        self.assertIn('configure', result)

    def _setup_cmd_interpreter_base_state(self):
        portData = {"type": "rj45",
                    "speedrange": [10, 100, 1000], "PoE": "yes"}
        switch = Switch()
        switch._ports.append(Port('1', 'ge.1.1', portData))
        cmd = EosCommand(switch)
        return cmd

    def _setup_cmd_interpreter_router_state(self):
        cmd = self._setup_cmd_interpreter_base_state()
        cmd.do_router('')
        return cmd

    def _setup_cmd_interpreter_enable_state(self):
        cmd = self._setup_cmd_interpreter_router_state()
        cmd.do_enable('')
        return cmd

    def _setup_cmd_interpreter_configure_state(self):
        cmd = self._setup_cmd_interpreter_enable_state()
        cmd.do_configure('')
        return cmd

    def test_do_access_lists_ok(self):
        cmd = self._setup_cmd_interpreter_configure_state()
        exp_ace = Standard_ACE(action='permit')
        exp_ace.set_source('192.168.0.1')
        exp_ace.set_source_mask('0.0.0.0')
        token_list = '1 permit host 192.168.0.1'.split()

        self.assertEqual('', cmd._do_access_list(token_list))

        ace = (cmd._switch.get_acl_by_number(1).get_entries())[0]
        self.assertEqual(exp_ace, ace)

    def test_do_access_lists_occursOutsideConfigureModeShouldInform(self):
        cmd = self._setup_cmd_interpreter_enable_state()
        token_list = '1 permit host 192.0.2.1'.split()

        self.assertRegex(cmd._do_access_list(token_list), '^INFO:.*outside.*')

    def test_do_access_lists_argumentsCompletelyMissing(self):
        cmd = self._setup_cmd_interpreter_configure_state()

        self.assertRegex(cmd._do_access_list(None),
                         '^ERROR:.*without arguments')

    def test_do_access_lists_shouldForwardToDoAccessListInterface(self):
        self.cmd._do_access_list_interface = MagicMock()
        token_list = 'interface'.split()

        self.cmd._do_access_list(token_list)

        self.cmd._do_access_list_interface.\
            assert_called_once_with([])

    def test_do_access_lists_shouldNotAcceptMacAccessLists(self):
        token_list = "mac".split()

        self.assertRegex(self.cmd._do_access_list(token_list),
                         "^NOTICE: Ignoring unknown.*$")

    def test_do_access_lists_shouldNotAcceptIpv6AccessLists(self):
        token_list = "ipv6".split()

        self.assertRegex(self.cmd._do_access_list(token_list),
                         "^NOTICE: Ignoring unknown.*$")

    def test_do_access_lists_shouldNotAcceptIpv6ModeAccessLists(self):
        token_list = "ipv6mode".split()

        self.assertRegex(self.cmd._do_access_list(token_list),
                         "^NOTICE: Ignoring unknown.*$")

    def test_do_access_lists_stdAclsShouldGiveExpectedResult(self):
        cmd = self._setup_cmd_interpreter_configure_state()
        token_list = '1 permit host 192.168.0.1'.split()
        result = cmd._do_access_list(token_list)

        self.assertEqual('', result)
        self.assertIsNotNone(cmd._switch.get_acl_by_number(1))

    def test_do_access_lists_shouldWarnOnSurPlusParams(self):
        cmd = self._setup_cmd_interpreter_configure_state()
        params = 'access-list 1 permit host 192.168.0.1 assign-queue 1'

        result = cmd.default(params)

        self.assertEqual('WARN: Ignoring "assign-queue 1" in "' +
                         params + '"', result)

    def test_do_access_list_shouldAddNonExistingAclToSwitch(self):
        cmd = self._setup_cmd_interpreter_configure_state()
        nr_of_acls = len(cmd._switch.get_acls())
        token_list = '1 permit host 192.168.0.1'.split()

        result = cmd._do_access_list(token_list)

        self.assertEqual('', result)
        self.assertEqual(nr_of_acls + 1, len(cmd._switch.get_acls()))

    def test_do_access_list_shouldAddNewAceToExistingAclOnSwitch(self):
        cmd = self._setup_cmd_interpreter_configure_state()
        acl = ACL(number=1)
        cmd._switch.add_complete_acl(acl)
        nr_of_aces = len(acl.get_entries())
        nr_of_acls = len(cmd._switch.get_acls())
        token_list = '1 permit host 192.168.0.1'.split()

        result = cmd._do_access_list(token_list)

        self.assertEqual('', result)
        self.assertEqual(nr_of_acls, len(cmd._switch.get_acls()),
                         ' number of acls ')
        self.assertEqual(nr_of_aces + 1,
                         len(acl.get_entries()),
                         ' number of aces')

    def test_do_acl_interface_noArguments(self):

        result = self.cmd._do_access_list_interface('')

        self.assertIn('ERROR', result)
        self.assertIn('arguments', result)

    def test_do_acl_interface_statementOccursOutsideConfigureMode(self):
        cmd = self._setup_cmd_interpreter_router_state()
        token_list = '1 ge.1.1 in'.split()

        result = cmd._do_access_list_interface(token_list)

        self.assertIn('INFO', result)
        self.assertIn('configuration mode', result)

    def test_do_acl_interface_tooMany_arguments(self):
        cmd = self._setup_cmd_interpreter_configure_state()
        token_list = '1 ge.1.1 in sequence 5 a'.split()

        result = cmd._do_access_list_interface(token_list)

        self.assertIn('ERROR', result)
        self.assertIn('Illegal', result)

    def test_do_acl_interface_wrongDirectionKeyword(self):
        cmd = self._setup_cmd_interpreter_configure_state()
        token_list = '1 ge.1.1 out'.split()

        result = cmd._do_access_list_interface(token_list)

        self.assertIn('ERROR', result)
        self.assertIn('inbound', result)

    def test_do_acl_interface_wrongSequenceKeyword(self):
        cmd = self._setup_cmd_interpreter_configure_state()
        token_list = '1 ge.1.1 seq 1'.split()

        result = cmd._do_access_list_interface(token_list)

        self.assertIn('ERROR', result)
        self.assertIn('sequence', result)

    def test_do_acl_interface_wrongSequenceNumber(self):
        cmd = self._setup_cmd_interpreter_configure_state()
        token_list = '1 ge.1.1 in sequence a'.split()

        result = cmd._do_access_list_interface(token_list)

        self.assertIn('ERROR', result)
        self.assertIn('integer', result)

    def test_do_acl_interface_shouldIgnoringSequenceNumber(self):
        cmd = self._setup_cmd_interpreter_configure_state()
        token_list = '1 ge.1.1 in sequence 1'.split()

        result = cmd._do_access_list_interface(token_list)

        self.assertIn('WARN', result)
        self.assertIn('sequence', result)

    def test_do_acl_interface_portNotFound(self):
        cmd = self._setup_cmd_interpreter_configure_state()
        token_list = '1 ge.1.2 in sequence 1'.split()

        result = cmd._do_access_list_interface(token_list)

        self.assertIn('ERROR', result)
        self.assertIn('Port', result)

    def test_do_interface_noArguments(self):

        result = self.cmd.do_interface('')

        self.assertIn('ERROR', result)
        self.assertIn('argument', result)

    def test_do_interface_argumentIsNotString(self):

        result = self.cmd.do_interface(1)

        self.assertIn('ERROR', result)
        self.assertIn('string as argument', result)

    def test_do_interface_wrongInterfaceName(self):

        result = self.cmd.do_interface('ge.1.1')

        self.assertIn('NOTICE: Ignoring unknown command "interface ge.1.1"',
                      result)

    def test_do_interface_missingVlanNumber(self):

        result = self.cmd.do_interface('vlan')

        self.assertIn('ERROR', result)
        self.assertIn('Unknown', result)

    def test_do_interface_directlyAttachedVlanNumberNaN(self):

        result = self.cmd.do_interface('vlanA')

        self.assertIn('ERROR', result)
        self.assertIn('Unknown', result)

    def test_do_interface_directlyAttachedVlanNumberOutOfRange(self):
        lower_boundary, upper_boundary = 1, 4095

        result = self.cmd.do_interface('vlan' + str(lower_boundary - 1))

        self.assertIn('ERROR', result)
        self.assertIn('Unknown', result)

        result = self.cmd.do_interface('vlan' + str(upper_boundary + 1))

        self.assertIn('ERROR', result)
        self.assertIn('Unknown', result)

    def test_do_interface_VlanNumberNaN(self):

        result = self.cmd.do_interface('vlan A')

        self.assertIn('ERROR', result)
        self.assertIn('integer', result)

    def test_do_interface_statementOccursOutsideConfigureMode(self):
        cmd = self._setup_cmd_interpreter_router_state()
        arg = 'vlan 1'

        result = cmd.do_interface(arg)

        self.assertIn('INFO', result)
        self.assertIn('config', result)

    def test_do_interface_createVlanIfNecessary(self):
        cmd = self._setup_cmd_interpreter_configure_state()
        arg = 'vlan4000'
        nr_vlans = len(cmd._switch.get_all_vlans())

        result = cmd.do_interface(arg)

        self.assertEqual('', result)
        self.assertEqual(nr_vlans + 1, len(cmd._switch.get_all_vlans()))

    def test_EosCommand__ignore_word(self):
        config_line = ""
        result = self.cmd._ignore_word('ignored', config_line)
        self.assertEqual('', result)

    def test_EosCommand_end_something(self):
        config_line = "something"
        result = self.cmd._ignore_word('ignore', config_line)
        self.assertEqual('NOTICE: Ignoring unknown command "ignore something"',
                         result)

    def test_EosCommand_begin(self):
        config_line = ""
        result = self.cmd.do_begin(config_line)
        self.assertEqual('', result)

    def test_EosCommand_begin_something(self):
        config_line = "something"
        result = self.cmd.do_begin(config_line)
        self.assertEqual('NOTICE: Ignoring unknown command "begin something"',
                         result)

    def test_EosCommand_end(self):
        config_line = ""
        result = self.cmd.do_end(config_line)
        self.assertEqual('', result)

    def test_EosCommand_ignore_end_something(self):
        config_line = "something"
        result = self.cmd.do_end(config_line)
        self.assertEqual('NOTICE: Ignoring unknown command "end something"',
                         result)

if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
