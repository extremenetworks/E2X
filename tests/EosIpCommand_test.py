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

from EOS_read import EosIpCommand
from Switch import Switch
from VLAN import VLAN


class EosIpCommand_test(unittest.TestCase):

    def setUp(self):
        switch = Switch()
        vlan = VLAN('vlan1', 1, None)
        switch.add_vlan(vlan)
        self.cmd = EosIpCommand(None, switch)

    def test_default_unknownCommand(self):

        result = self.cmd.default('unknown command')

        self.assertIn('NOTICE', result)
        self.assertIn('unknown command', result)

    class cmdMock(EosIpCommand):
        def __init__(self):
            super().__init__(None, None)

        def _do_access_group(self, token_lst):
            return 'access-group called'

    def test_default_accessListCommand(self):
        cmd = self.cmdMock()

        result = cmd.default('access-group doesnt matter')

        self.assertEqual('access-group called', result)

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

    def test_do_access_group_InterfaceIsNotAString(self):

        self.cmd.set_state(('router', 'config', 9))

        result = self.cmd._do_access_group('1')

        self.assertIn('ERROR', result)
        self.assertIn('unknown interface', result)

    def test_do_access_group_InterfaceIsNotAVlanInterface(self):

        self.cmd.set_state(('router', 'config', 'interface ge.1.1'))

        result = self.cmd._do_access_group('1')

        self.assertIn('ERROR', result)
        self.assertIn('unknown interface', result)

    def test_do_access_group_InterfaceVlanIdIsNaN(self):

        self.cmd.set_state(('router', 'config', 'interface vlan a'))

        result = self.cmd._do_access_group('1')

        self.assertIn('ERROR', result)
        self.assertIn('integer', result)

    def test_do_access_group_InterfaceVlanNrOutOfRange(self):
        lower_boundary, upper_boundary = 1, 4095

        self.cmd.set_state(('router', 'config',
                            'interface vlan ' + str(lower_boundary - 1)))

        result_lower = self.cmd._do_access_group('1')

        self.cmd.set_state(('router', 'config',
                            'interface vlan ' + str(upper_boundary + 1)))

        result_upper = self.cmd._do_access_group('1')

        self.assertIn('ERROR', result_lower)
        self.assertIn('Illegal VLAN ID', result_lower)
        self.assertIn('ERROR', result_upper)
        self.assertIn('Illegal VLAN ID', result_upper)

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

    def test_do_access_group_unsupportedDirection(self):

        self.cmd.set_state(('router', 'config', 'interface vlan 1'))

        result = self.cmd._do_access_group(('1', 'out'))

        self.assertIn('ERROR', result)
        self.assertIn('direction', result)

if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
