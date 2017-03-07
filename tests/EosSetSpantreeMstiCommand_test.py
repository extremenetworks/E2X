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

# Copyright 2014-2017 Extreme Networks, Inc.  All rights reserved.
# Use is subject to license terms.

# This file is part of e2x (translate EOS switch configuration to ExtremeXOS)

import unittest
import sys

sys.path.extend(['../src'])

import EOS_read
import Switch
import STP

from unittest.mock import MagicMock


class EosSetSpantreeMstiCommand_test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.mockSwitch = MagicMock(spec=Switch.Switch)
        cls.mockStp = MagicMock(spec=STP.STP)

        cls.ErrorStart = 'ERROR: '

    def setUp(self):
        self.cmd = EOS_read.EosSetSpantreeMstiCommand(self.mockSwitch)

    def test_do_sid_fail_wrong_nr_of_args(self):
        args = '1'
        expected = self.ErrorStart + \
            'Incorrect command "set spantree msti sid ' + args + '"'

        result = self.cmd.do_sid(args)

        self.assertEqual(expected, result)

    def test_do_sid_fail_sid_no_int(self):
        args = 'a create'
        expected = self.ErrorStart + \
            'SID must be an integer (set spantree msti sid ' + args + ')'

        result = self.cmd.do_sid(args)

        self.assertEqual(expected, result)

    def test_do_sid_fail_sid_out_of_bounds(self):
        sid_lowest, sid_highest = 1, 4094
        errStr = self.ErrorStart + \
            'SID must be in [1,4094] (set spantree msti sid {})'

        arg = str(sid_lowest - 1) + ' create'
        expErrLower = errStr.format(arg)

        result_lower = self.cmd.do_sid(arg)

        arg = str(sid_highest + 1) + ' delete'
        expErrHigher = errStr.format(arg)

        result_higher = self.cmd.do_sid(arg)

        self.assertEqual(expErrLower, result_lower)
        self.assertEqual(expErrHigher, result_higher)

    def test_do_sid_fail_wrong_action(self):
        arg = '1 foo'
        expected = self.ErrorStart + \
            'Wrong number of arguments to "set spantree msti"'

        result = self.cmd.do_sid(arg)

        self.assertEqual(expected, result)

    def test_do_sid_ok_action_create(self):
        arg = '1 create'
        expected = ''

        result = self.cmd.do_sid(arg)

        self.assertTrue(self.mockSwitch.add_stp.called)
        self.assertEqual(expected, result)

    def test_do_sid_ok_action_delete(self):
        sid = 1
        arg = str(sid) + ' delete'
        self.mockSwitch.delete_stp_by_instance_id.return_value = self.mockStp
        expected = self.mockStp

        result = self.cmd.do_sid(arg)

        self.mockSwitch.delete_stp_by_instance_id.assert_called_once_with(sid)
        self.assertEqual(expected, result)

if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
