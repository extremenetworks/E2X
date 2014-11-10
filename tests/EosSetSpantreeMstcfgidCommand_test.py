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

# Copyright 2014 Extreme Networks, Inc.  All rights reserved.
# Use is subject to license terms.

# This file is part of e2x (translate EOS switch configuration to ExtremeXOS)

import unittest
import sys

sys.path.extend(['../src'])

import EOS_read
import Switch
import STP

from unittest.mock import MagicMock


class EosSetSpantreeMstcfgidCommand_test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.mockSwitch = MagicMock(spec=Switch.Switch)
        cls.mockStp = MagicMock(spec=STP.STP)

        cls.ErrorStart = 'ERROR: '

    def setUp(self):
        self.cmd = EOS_read.EosSetSpantreeMstcfgidCommand(self.mockSwitch)

    def test_do_cfgname_fail_no_arg(self):
        arg = ''
        expected = self.ErrorStart + \
            '"set spantree mstcfgid cfgname" needs a name'

        result = self.cmd.do_cfgname(arg)

        self.assertEqual(expected, result)

    def test_do_cfgname_fail_wrong_nr_of_args(self):
        arg = 'cfgname mst1'
        expected = self.ErrorStart + \
            'Wrong number of arguments to "set spantree mstcfgid cfgname"' + \
            ' (' + arg + ')'

        result = self.cmd.do_cfgname(arg)

        self.assertEqual(expected, result)

    def test_do_cfgname_fail_no_stp_with_id_0(self):
        arg = 'mst1'
        self.mockSwitch.get_stp_by_mst_instance.return_value = None
        expected = self.ErrorStart + \
            'MST instance 0 missing (set spantree mstcfgid cfgname)'\

        result = self.cmd.do_cfgname(arg)

        self.assertEqual(expected, result)

    def test_do_cfgname_ok(self):
        self.mockStp.reset_mock()
        arg = 'mst1'
        self.mockSwitch.get_stp_by_mst_instance.return_value = self.mockStp
        expected = ''

        result = self.cmd.do_cfgname(arg)

        self.mockStp.set_mst_cfgname.assert_callaed_once_with(arg, 'config')
        self.assertEqual(expected, result)

    def test_do_cfgname_three_args(self):
        self.mockStp.reset_mock()
        self.cmd.onecmd = MagicMock()
        cfg_name = 'mst1'
        rev = 'rev 1'
        arg = cfg_name + ' ' + rev
        self.mockSwitch.get_stp_by_mst_instance.return_value = self.mockStp

        self.cmd.do_cfgname(arg)

        self.mockStp.set_mst_cfgname.assert_called_once_with(cfg_name,
                                                             'config')
        self.cmd.onecmd.assert_called_once_with(rev)

    def test_do_rev_fail_no_arg(self):
        arg = ''
        expected = self.ErrorStart + \
            '"set spantree mstcfgid rev" needs a revision number'

        result = self.cmd.do_rev(arg)

        self.assertEqual(expected, result)

    def test_do_rev_fail_wrong_nr_of_args(self):
        arg = '1 mst1'
        expected = self.ErrorStart + \
            'Wrong number of arguments to "set spantree mstcfgid rev"' + \
            ' (' + arg + ')'

        result = self.cmd.do_rev(arg)

        self.assertEqual(expected, result)

    def test_do_rev_fail_rev_no_int(self):
        args = 'a'
        expected = self.ErrorStart + 'Revision number must be an integer ' + \
            '(set spantree mstcfgid rev ' + args + ')'

        result = self.cmd.do_rev(args)

        self.assertEqual(expected, result)

    def test_do_rev_fail_rev_nr_out_of_bounds(self):
        rev_lowest, rev_highest = 0, 65535
        errStr = self.ErrorStart + 'Revision number must be in [0,65535] ' + \
            '(set spantree mstcfgid rev {})'

        arg = str(rev_lowest - 1)
        expErrLower = errStr.format(arg)

        result_lower = self.cmd.do_rev(arg)

        arg = str(rev_highest + 1)
        expErrHigher = errStr.format(arg)

        result_higher = self.cmd.do_rev(arg)

        self.assertEqual(expErrLower, result_lower)
        self.assertEqual(expErrHigher, result_higher)

    def test_do_rev_fail_no_stp_with_id_0(self):
        arg = '1'
        self.mockSwitch.get_stp_by_mst_instance.return_value = None
        expected = self.ErrorStart + \
            'MST instance 0 missing (set spantree mstcfgid rev)'\

        result = self.cmd.do_rev(arg)

        self.assertEqual(expected, result)

    def test_do_rev_ok(self):
        self.mockStp.reset_mock()
        arg = '1'
        self.mockSwitch.get_stp_by_mst_instance.return_value = self.mockStp
        expected = ''

        result = self.cmd.do_rev(arg)

        self.mockStp.set_mst_rev.assert_callaed_once_with(arg, 'config')
        self.assertEqual(expected, result)

    def test_do_rev_three_args(self):
        self.mockStp.reset_mock()
        self.cmd.onecmd = MagicMock()
        rev = '1'
        cfg_name = 'cfgname mst1'
        arg = rev + ' ' + cfg_name
        self.mockSwitch.get_stp_by_mst_instance.return_value = self.mockStp

        self.cmd.do_rev(arg)

        self.mockStp.set_mst_rev.assert_called_once_with(int(rev),
                                                         'config')
        self.cmd.onecmd.assert_called_once_with(cfg_name)

if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
