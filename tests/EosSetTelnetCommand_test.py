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

from EOS_read import EosSetTelnetCommand
from Switch import Switch

from unittest.mock import Mock


class EosSetTelnetCommand_test(unittest.TestCase):

    def setUp(self):
        self.switch = Mock(spec=Switch)
        self.cmd = EosSetTelnetCommand(self.switch)

    def test_default_unknownCommand(self):
        argStr = 'unknown'

        result = self.cmd.onecmd(argStr)

        self.assertIn('NOTICE', result)
        self.assertIn('unknown command', result)

    def test_do_disable_noArgument(self):

        result = self.cmd.do_disable('')

        self.assertIn('ERROR', result)
        self.assertIn('argument', result)

    def test_do_disable_unknownArgument(self):
        argStr = "both directions"

        result = self.cmd.do_disable(argStr)

        self.assertIn('NOTICE', result)
        self.assertIn('unknown', result)

    def test_do_disable_argumentAll(self):
        argStr = 'all'

        result = self.cmd.do_disable(argStr)

        self.switch.set_telnet_inbound.assert_called_once_with(False,
                                                               'config')
        self.switch.set_telnet_outbound.assert_called_once_with(False,
                                                                'config')
        self.assertEqual('', result)

    def test_do_disable_argumentInbound(self):
        argStr = 'inbound'

        result = self.cmd.do_disable(argStr)

        self.switch.set_telnet_inbound.assert_called_once_with(False,
                                                               'config')
        self.assertEqual('', result)

    def test_do_disable_argumentOutbound(self):
        argStr = 'outbound'

        result = self.cmd.do_disable(argStr)

        self.switch.set_telnet_outbound.assert_called_once_with(False,
                                                                'config')
        self.assertEqual('', result)

    ###
    ###

    def test_do_enable_noArgument(self):

        result = self.cmd.do_enable('')

        self.assertIn('ERROR', result)
        self.assertIn('argument', result)

    def test_do_enable_unknownArgument(self):
        argStr = "both directions"

        result = self.cmd.do_enable(argStr)

        self.assertIn('NOTICE', result)
        self.assertIn('unknown', result)

    def test_do_enable_argumentAll(self):
        argStr = 'all'

        result = self.cmd.do_enable(argStr)

        self.switch.set_telnet_inbound.assert_called_once_with(True,
                                                               'config')
        self.switch.set_telnet_outbound.assert_called_once_with(True,
                                                                'config')
        self.assertEqual('', result)

    def test_do_enable_argumentInbound(self):
        argStr = 'inbound'

        result = self.cmd.do_enable(argStr)

        self.switch.set_telnet_inbound.assert_called_once_with(True,
                                                               'config')
        self.assertEqual('', result)

    def test_do_enable_argumentOutbound(self):
        argStr = 'outbound'

        result = self.cmd.do_enable(argStr)

        self.switch.set_telnet_outbound.assert_called_once_with(True,
                                                                'config')
        self.assertEqual('', result)

if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
