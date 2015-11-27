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

from EOS_read import EosSetSystemCommand
from Switch import Switch
from Account import UserAccount

from unittest.mock import Mock


class EosSetSystemCommand_test(unittest.TestCase):

    def setUp(self):
        self.switch = Mock(spec=Switch)
        self.cmd = EosSetSystemCommand(self.switch)

    def test_default_unknownCommand(self):
        argStr = 'unknown'

        result = self.cmd.onecmd(argStr)

        self.assertIn('NOTICE', result)
        self.assertIn('unknown command', result)

    def test_do_name_noArgument(self):

        result = self.cmd.do_name('')

        self.switch.set_snmp_sys_name.assert_called_once_with(None, 'config')
        self.assertEqual('', result)

    def test_do_name_argumentMissesQuotes(self):
        argStr = "test lab"

        result = self.cmd.do_name(argStr)

        self.switch.set_snmp_sys_name.assert_called_once_with(argStr, 'config')
        self.assertIn('WARN', result)
        self.assertIn('quotes', result)

    def test_do_name_argumentOk(self):
        unquotedArgStr = 'test lab'
        argStr = '"' + unquotedArgStr + '"'
        result = self.cmd.do_name(argStr)

        self.switch.set_snmp_sys_name.assert_called_once_with(unquotedArgStr,
                                                              'config')
        self.assertEqual('', result)

    ###
    ###

    def test_do_contact_noArgument(self):

        result = self.cmd.do_contact('')

        self.switch.set_snmp_sys_contact.assert_called_once_with(None,
                                                                 'config')
        self.assertEqual('', result)

    def test_do_contact_argumentMissesQuotes(self):
        argStr = "admin admin"

        result = self.cmd.do_contact(argStr)

        self.switch.set_snmp_sys_contact.assert_called_once_with(argStr,
                                                                 'config')
        self.assertIn('WARN', result)
        self.assertIn('quotes', result)

    def test_do_contact_argumentOk(self):
        unquotedArgStr = 'admin admin'
        argStr = '"' + unquotedArgStr + '"'

        result = self.cmd.do_contact(argStr)

        self.switch.\
            set_snmp_sys_contact.assert_called_once_with(unquotedArgStr,
                                                         'config')
        self.assertEqual('', result)

    ###
    ###

    def test_do_location_noArgument(self):

        result = self.cmd.do_location('')

        self.switch.set_snmp_sys_location.assert_called_once_with(None,
                                                                  'config')
        self.assertEqual('', result)

    def test_do_location_argumentMissesQuotes(self):
        argStr = "Server Room"

        result = self.cmd.do_location(argStr)

        self.switch.set_snmp_sys_location.assert_called_once_with(argStr,
                                                                  'config')
        self.assertIn('WARN', result)
        self.assertIn('quotes', result)

    def test_do_location_argumentOk(self):
        unquotedArgStr = 'server room'
        argStr = '"' + unquotedArgStr + '"'

        result = self.cmd.do_location(argStr)

        self.switch.\
            set_snmp_sys_location.assert_called_once_with(unquotedArgStr,
                                                          'config')
        self.assertEqual('', result)

    ###
    ###

    def test_do_login_noArgument(self):

        result = self.cmd.do_login('')

        self.assertIn('ERROR', result)
        self.assertIn('argument', result)

    def test_do_login_wrongArgument(self):
        argStr = 'admin user enable password admin'

        result = self.cmd.do_login(argStr)

        self.assertIn('NOTICE', result)
        self.assertIn(argStr, result)

    def test_do_login_accountDoesNotExist(self):
        argStr = 'admin super-user enable password admin'
        self.switch.get_user_account.return_value = None

        result = self.cmd.do_login(argStr)

        self.assertIn('ERROR', result)
        self.assertIn(argStr, result)

    def test_do_login_accountAttribDefaultIsNotSet(self):
        argStr = 'admin super-user enable password admin'
        account = Mock(spec=UserAccount)
        self.switch.get_user_account.return_value = account
        account.get_is_default.return_value = None

        result = self.cmd.do_login(argStr)

        account.set_is_default.assert_called_once_with(False)
        self.assertIn('', result)

    def test_do_login_accountAttribDefaultIsSet(self):
        argStr = 'admin super-user enable password admin'
        account = Mock(spec=UserAccount)
        self.switch.get_user_account.return_value = account
        account.get_is_default.return_value = False

        result = self.cmd.do_login(argStr)

        self.assertEqual(0, account.set_is_default.call_count)
        self.assertIn('', result)

    def test_do_login_accountWithNoPassword(self):
        argStr = 'admin read-only disable'
        account = Mock(spec=UserAccount)
        self.switch.get_user_account.return_value = account
        account.get_is_default.return_value = False

        result = self.cmd.do_login(argStr)

        account.set_name.assert_called_once_with('admin')
        account.set_type.assert_called_once_with('read-only')
        account.set_state.assert_called_once_with('disable')
        self.assertIn('', result)

    def test_do_login_accountWithEncryptedPassword(self):
        argStr = 'admin super-user enable password ' \
                 ':123456789012345678901234567890123456789012345' \
                 '6789012345678901234567890123456789012:'
        account = Mock(spec=UserAccount)
        self.switch.get_user_account.return_value = account

        result = self.cmd.do_login(argStr)

        self.assertEqual(0, account.set_password.call_count)
        self.assertIn('WARN', result)
        self.assertIn('encrypted', result)

    def test_do_login_accountOk(self):
        argStr = 'admin super-user enable password :1234567890:'
        account = Mock(spec=UserAccount)
        self.switch.get_user_account.return_value = account

        result = self.cmd.do_login(argStr)

        self.assertEqual(1, account.set_password.call_count)
        self.assertEqual('', result)

if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
