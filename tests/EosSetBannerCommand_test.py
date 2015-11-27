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

from EOS_read import EosSetBannerCommand
from Switch import Switch

from unittest.mock import Mock


class EosSetBannerCommand_test(unittest.TestCase):

    def setUp(self):
        self.switch = Mock(spec=Switch)
        self.cmd = EosSetBannerCommand(self.switch)

    def test_default_unknownCommand(self):
        argStr = 'unknown'

        result = self.cmd.onecmd(argStr)

        self.assertIn('NOTICE', result)
        self.assertIn('unknown command', result)

    def test_do_login_noArgument(self):

        result = self.cmd.do_login('')

        self.assertIn('ERROR', result)
        self.assertIn('argument', result)

    def test_do_login_argumentMissesQuotes(self):
        argStr = "authorized access"

        result = self.cmd.do_login(argStr)

        self.switch.set_banner_login.assert_called_once_with(argStr, 'config')
        self.assertIn('WARN', result)
        self.assertIn('quotes', result)

    def test_do_login_argumentOk(self):
        unquotedArgStr = 'authorized access'
        argStr = '"' + unquotedArgStr + '"'

        result = self.cmd.do_login(argStr)

        self.switch.set_banner_login.assert_called_once_with(unquotedArgStr,
                                                             'config')
        self.assertEqual('', result)

    def test_do_login_argumentOkUnquoteNewline(self):
        unquotedArgStr = 'authorized\naccess'
        argStr = '"' + unquotedArgStr.replace(r'\n', r'\\n') + '"'

        result = self.cmd.do_login(argStr)

        self.switch.set_banner_login.assert_called_once_with(unquotedArgStr,
                                                             'config')
        self.assertEqual('', result)

    def test_do_login_argumentOkUnquoteTab(self):
        unquotedArgStr = 'authorized\taccess'
        argStr = '"' + unquotedArgStr.replace(r'\t', r'\\t') + '"'

        result = self.cmd.do_login(argStr)

        self.switch.set_banner_login.assert_called_once_with(unquotedArgStr,
                                                             'config')
        self.assertEqual('', result)

    ###
    ###

    def test_do_motd_noArgument(self):

        result = self.cmd.do_motd('')

        self.assertIn('ERROR', result)
        self.assertIn('argument', result)

    def test_do_motd_argumentMissesQuotes(self):
        argStr = "welcome home"

        result = self.cmd.do_motd(argStr)

        self.switch.set_banner_motd.assert_called_once_with(argStr, 'config')
        self.assertIn('WARN', result)
        self.assertIn('quotes', result)

    def test_do_motd_argumentOk(self):
        unquotedArgStr = 'welcome home'
        argStr = '"' + unquotedArgStr + '"'

        result = self.cmd.do_motd(argStr)

        self.switch.set_banner_motd.assert_called_once_with(unquotedArgStr,
                                                            'config')
        self.assertEqual('', result)

    def test_do_motd_argumentOkUnquoteNewline(self):
        unquotedArgStr = 'authorized\naccess'
        argStr = '"' + unquotedArgStr.replace(r'\n', r'\\n') + '"'

        result = self.cmd.do_motd(argStr)

        self.switch.set_banner_motd.assert_called_once_with(unquotedArgStr,
                                                            'config')
        self.assertEqual('', result)

    def test_do_motd_argumentOkUnquoteTab(self):
        unquotedArgStr = 'authorized\taccess'
        argStr = '"' + unquotedArgStr.replace(r'\t', r'\\t') + '"'

        result = self.cmd.do_motd(argStr)

        self.switch.set_banner_motd.assert_called_once_with(unquotedArgStr,
                                                            'config')
        self.assertEqual('', result)

if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
