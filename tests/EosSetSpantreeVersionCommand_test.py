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
import STP

from unittest.mock import MagicMock


class EosSetSpantreeVersionCommand_test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.mockSwitch = MagicMock(spec=Switch.Switch)
        cls.mockStp = MagicMock(spec=STP.STP)

        cls.ErrorStart = 'ERROR: '

    def setUp(self):
        self.cmd = EOS_read.EosSetSpantreeVersionCommand(self.mockSwitch)

    def test_set_version_fail_no_stps(self):
        version = 'mstp'
        self.mockSwitch.get_stps.return_value = []
        expected = self.ErrorStart + \
            'Cannot configure version of non-existing STP'

        result = self.cmd._set_version(version)

        self.assertEqual(expected, result)

    def test_set_version_fail_stp_set_version_fails(self):
        version = 'mstp'
        self.mockSwitch.get_stps.return_value = [self.mockStp]
        self.mockStp.set_version.return_value = None
        expected = self.ErrorStart + \
            'Could not apply "set spantree version ' + version + '"'

        result = self.cmd._set_version(version)

        self.assertEqual(expected, result)

    def test_set_version_ok(self):
        self.mockStp.reset_mock()
        version = 'mstp'
        self.mockSwitch.get_stps.return_value = [self.mockStp]
        self.mockStp.set_version.return_value = version
        expected = ''

        result = self.cmd._set_version(version)

        self.assertEqual(expected, result)
        self.mockStp.set_version.assert_called_once_with(version, 'config')

    def test_do_mstp(self):
        arg = 'dont matter'
        version = 'mstp'
        self.mockSwitch.get_stps.return_value = [self.mockStp]
        self.mockStp.set_version.return_value = version
        expected = ''

        result = self.cmd.do_mstp(arg)

        self.assertEqual(expected, result)

    def test_do_rstp(self):
        arg = 'dont matter'
        version = 'rstp'
        self.mockSwitch.get_stps.return_value = [self.mockStp]
        self.mockStp.set_version.return_value = version
        expected = ''

        result = self.cmd.do_rstp(arg)

        self.assertEqual(expected, result)

    def test_do_stpcompatible(self):
        arg = 'dont matter'
        version = 'stp'
        self.mockSwitch.get_stps.return_value = [self.mockStp]
        self.mockStp.set_version.return_value = version
        expected = ''

        result = self.cmd.do_stpcompatible(arg)

        self.assertEqual(expected, result)

if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
