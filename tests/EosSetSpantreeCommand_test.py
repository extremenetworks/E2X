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

import EOS_read
import Switch
import STP
import Port

from unittest.mock import MagicMock


class EosSetSpantreeCommand_test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.mockSwitch = MagicMock(spec=Switch.Switch)
        cls.mockStp = MagicMock(spec=STP.STP)
        cls.mockPort = MagicMock(spec=Port.Port)

        cls.WarningStart = 'WARN: '
        cls.ErrorStart = 'ERROR: '
        cls.NoticeStart = 'NOTICE: '

        cls.IgnoreUnknownCmdStr = cls.NoticeStart + \
            'Ignoring unknown command'

    def setUp(self):
        self.cmd = EOS_read.EosSetSpantreeCommand(self.mockSwitch)

    def test_default(self):
        line = 'foo'
        expected = self.NoticeStart + \
            'Ignoring unknown command "set spantree ' + line + '"'

        result = self.cmd.onecmd(line)

        self.assertEqual(expected, result)

    def test_do_disable_fail_arg_given(self):
        arg = 'dont'
        expected = self.ErrorStart + '"set spantree disable" takes no argument'

        result = self.cmd.do_disable(arg)

        self.assertEqual(expected, result)

    def test_do_disable_fail_stp_does_not_exist(self):

        self.mockSwitch.get_stps.return_value = []
        expected = self.WarningStart + 'Cannot disable non-existing STP'

        result = self.cmd.do_disable('')

        self.assertEqual(expected, result)

    def test_do_disable_ok(self):
        self.mockSwitch.get_stps.return_value = [self.mockStp]
        expected = ''

        result = self.cmd.do_disable('')

        self.assertEqual(expected, result)
        self.mockStp.disable.assert_called_once_with('config')

    def test_do_enable_fail_arg_given(self):
        arg = 'dont'
        expected = self.ErrorStart + '"set spantree enable" takes no argument'

        result = self.cmd.do_enable(arg)

        self.assertEqual(expected, result)

    def test_do_enable_fail_stp_does_not_exist(self):

        self.mockSwitch.get_stps.return_value = []
        expected = self.ErrorStart + 'Cannot enable non-existing STP'

        result = self.cmd.do_enable('')

        self.assertEqual(expected, result)

    def test_do_enable_ok(self):
        self.mockSwitch.get_stps.return_value = [self.mockStp]
        expected = ''

        result = self.cmd.do_enable('')

        self.assertEqual(expected, result)
        self.mockStp.enable.assert_called_once_with('config')

    def test_do_version(self):
        codeFragemnt = 'vers'
        expResultStart = self.IgnoreUnknownCmdStr

        result = self.cmd.do_version(codeFragemnt)

        self.assertTrue(result.startswith(expResultStart))
        self.assertIn(codeFragemnt, result)

    def test_do_msti(self):
        codeFragemnt = 'msti'
        expResultStart = self.IgnoreUnknownCmdStr

        result = self.cmd.do_msti(codeFragemnt)

        self.assertTrue(result.startswith(expResultStart))
        self.assertIn(codeFragemnt, result)

    def test_do_mstcfgid(self):
        codeFragemnt = 'mstcfgid'
        expResultStart = self.IgnoreUnknownCmdStr

        result = self.cmd.do_mstcfgid(codeFragemnt)

        self.assertTrue(result.startswith(expResultStart))
        self.assertIn(codeFragemnt, result)

    def test_do_mstmap_fail_no_arg(self):
        arg = ''
        expected = self.ErrorStart + \
            '"set spantree mstmap" needs a FID argument'

        result = self.cmd.do_mstmap(arg)

        self.assertEqual(expected, result)

    def test_do_mstmap_fail_wrong_nr_of_args(self):
        arg = 'fid sid'
        expected = self.ErrorStart + \
            'Wrong number of arguments to "set spantree mstmap"'

        result = self.cmd.do_mstmap(arg)

        self.assertEqual(expected, result)

    def test_do_mstmap_fail_wrong_syntax_of_args(self):
        arg = 'fid foo 1'
        expected = self.ErrorStart + \
            'Second argument to "set spantree mstmap" must be "sid"'

        result = self.cmd.do_mstmap(arg)

        self.assertEqual(expected, result)

    def test_do_mstmap_fail_wrong_fid_syntax(self):
        fid_sequence = 'fid'
        arg = fid_sequence + ' sid 1'
        expected = self.ErrorStart + \
            'Illegal FID "' + fid_sequence + '"'

        result = self.cmd.do_mstmap(arg)

        self.assertEqual(expected, result)

    def test_do_mstmap_fail_fid_out_of_bounds(self):
        fid_lowest, fid_highest = 1, 4094
        errStr = self.ErrorStart + 'Illegal FID "{}"'
        fid_sequence = '0'
        arg = fid_sequence + ' sid 1'
        expErrLower = errStr.format(fid_sequence)

        result_lower = self.cmd.do_mstmap(arg)

        fid_sequence = '4095'
        arg = fid_sequence + ' sid 1'
        expErrHigher = errStr.format(fid_sequence)

        result_higher = self.cmd.do_mstmap(arg)

        self.assertEqual(expErrLower, result_lower)
        self.assertEqual(expErrHigher, result_higher)

    def test_do_mstmap_fail_sid_no_int(self):
        fid_sequence = '1'
        arg = fid_sequence + ' sid a'
        expected = self.ErrorStart + \
            'MST instance ID must be an integer'

        result = self.cmd.do_mstmap(arg)

        self.assertEqual(expected, result)

    def test_do_mstmap_ok(self):
        fid_sequence = '1'
        arg = fid_sequence + ' sid 1'
        self.mockSwitch.get_stps.return_value = [self.mockStp]
        self.mockSwitch.get_stp_by_mst_instance.return_value = self.mockStp
        expected = ''

        result = self.cmd.do_mstmap(arg)

        self.assertEqual(expected, result)
        self.mockStp.del_vlans.assert_called_once_with([1], 'config')
        self.mockStp.add_vlans.assert_called_once_with([1], 'config')

    def test_do_priority_fail_no_arg(self):
        arg = ''
        expected = self.ErrorStart + \
            '"set spantree priority" needs a priority'

        result = self.cmd.do_priority(arg)

        self.assertEqual(expected, result)

    def test_do_priority_fail_wrong_nr_of_args(self):
        arg = 'foo bar baz'
        expected = self.ErrorStart + \
            'Wrong number of arguments to "set spantree priority"'

        result = self.cmd.do_priority(arg)

        self.assertEqual(expected, result)

    def test_do_priority_fail_priority_no_int(self):
        priority = 'a'
        arg = priority
        expected = self.ErrorStart + \
            'Priority must be an integer (set spantree priority)'

        result = self.cmd.do_priority(arg)

        self.assertEqual(expected, result)

    def test_do_priority_fail_priority_out_of_bounds(self):
        prio_lowest, prio_highest = 0, 61440
        errStr = self.ErrorStart + 'Priority must be in [0,61440] ' + \
            '(set spantree priority)'
        arg = str(prio_lowest - 1)
        expErrLower = errStr

        result_lower = self.cmd.do_priority(arg)

        arg = str(prio_highest + 1)
        expErrHigher = errStr

        result_higher = self.cmd.do_priority(arg)

        self.assertEqual(expErrLower, result_lower)
        self.assertEqual(expErrHigher, result_higher)

    def test_do_priorty_fail_sid_no_int(self):
        prio = '1'
        arg = prio + ' a'
        expected = self.ErrorStart + \
            'MST instance ID must be an integer (set spantree priority)'

        result = self.cmd.do_priority(arg)

        self.assertEqual(expected, result)

    def test_do_priority_fail_stp_not_found(self):
        prio, sid = '1', '1'
        arg = prio + ' 1'
        self.mockSwitch.get_stps.return_value = [self.mockStp]
        self.mockSwitch.get_stp_by_mst_instance.return_value = None
        expected = self.ErrorStart + 'MST instance with ID "' + sid + \
            '" not found (set spantree priority)'

        result = self.cmd.do_priority(arg)

        self.assertEqual(expected, result)

    def test_do_priority_fail_stp_set_priority_fails(self):
        prio, sid = '1', '1'
        arg = prio + ' 1'
        self.mockSwitch.get_stps.return_value = [self.mockStp]
        self.mockSwitch.get_stp_by_mst_instance.return_value = self.mockStp
        self.mockStp.set_priority.return_value = None
        expected = self.ErrorStart + 'Could not set priority "' + prio + \
            '" (set spantree priority)'

        result = self.cmd.do_priority(arg)

        self.assertEqual(expected, result)

    def test_do_priority_ok(self):
        prio, sid = '1', '1'
        arg = prio + ' 1'
        self.mockSwitch.get_stps.return_value = [self.mockStp]
        self.mockSwitch.get_stp_by_mst_instance.return_value = self.mockStp
        self.mockStp.set_priority.return_value = int(prio)
        expected = ''

        result = self.cmd.do_priority(arg)

        self.assertEqual(expected, result)

    def test_do_spanguard(self):
        arg = 'foo'
        self.cmd._set_spantree_spanguard.onecmd = MagicMock()

        self.cmd.do_spanguard(arg)

        self.cmd._set_spantree_spanguard.onecmd.assert_called_once_with(arg)

    def test_do_autoedge(self):
        arg = 'bah'
        self.cmd._set_spantree_autoedge.onecmd = MagicMock()

        self.cmd.do_autoedge(arg)

        self.cmd._set_spantree_autoedge.onecmd.assert_called_once_with(arg)

    def test_do_portadmin_fail_wrong_nr_of_args(self):
        args = 'foo'
        expected = self.ErrorStart + \
            'Wrong number of arguments to "set spantree portadmin"'

        result = self.cmd.do_portadmin(args)

        self.assertEqual(expected, result)

    def test_do_portadmin_fail_port_not_found(self):
        portStr, cmd = 'ge.1.1', 'foo'
        args = portStr + ' ' + cmd
        self.mockSwitch.get_ports_by_name.return_value = []
        expected = self.ErrorStart + \
            'Port ' + portStr + ' not found (set spantree portadmin)'

        result = self.cmd.do_portadmin(args)

        self.assertEqual(expected, result)

    def test_do_portadmin_fail_wrong_cmd(self):
        portStr, cmd = 'ge.1.1', 'foo'
        args = portStr + ' ' + cmd
        self.mockSwitch.get_ports_by_name.return_value = [self.mockPort]
        expected = self.ErrorStart + \
            'Unknown argument "' + cmd + '" to "set spantree portadmin ' + \
            portStr + '"'

        result = self.cmd.do_portadmin(args)

        self.assertEqual(expected, result)

    def test_do_portadmin_ok_cmd_enable(self):
        self.mockPort.reset_mock()
        portStr, cmd = 'ge.1.1', 'enable'
        args = portStr + ' ' + cmd
        self.mockSwitch.get_ports_by_name.return_value = [self.mockPort]
        expected = ''

        result = self.cmd.do_portadmin(args)

        self.mockPort.set_stp_enabled.assert_called_once_with(True, 'config')
        self.assertEqual(expected, result)

    def test_do_portadmin_ok_cmd_disable(self):
        self.mockPort.reset_mock()
        portStr, cmd = 'ge.1.1', 'disable'
        args = portStr + ' ' + cmd
        self.mockSwitch.get_ports_by_name.return_value = [self.mockPort]
        expected = ''

        result = self.cmd.do_portadmin(args)

        self.mockPort.set_stp_enabled.assert_called_once_with(False, 'config')
        self.assertEqual(expected, result)

    def test_do_adminedge_fail_wrong_nr_of_args(self):
        args = 'foo'
        expected = self.ErrorStart + \
            'Wrong number of arguments to "set spantree adminedge"'

        result = self.cmd.do_adminedge(args)

        self.assertEqual(expected, result)

    def test_do_adminedge_fail_port_not_found(self):
        portStr, cmd = 'ge.1.1', 'foo'
        args = portStr + ' ' + cmd
        self.mockSwitch.get_ports_by_name.return_value = []
        expected = self.ErrorStart + \
            'Port ' + portStr + ' not found (set spantree adminedge)'

        result = self.cmd.do_adminedge(args)

        self.assertEqual(expected, result)

    def test_do_adminedge_fail_wrong_cmd(self):
        portStr, cmd = 'ge.1.1', 'foo'
        args = portStr + ' ' + cmd
        self.mockSwitch.get_ports_by_name.return_value = [self.mockPort]
        expected = self.ErrorStart + \
            'Unknown argument "' + cmd + '" to "set spantree adminedge ' + \
            portStr + '"'

        result = self.cmd.do_adminedge(args)

        self.assertEqual(expected, result)

    def test_do_adminedge_ok_cmd_true(self):
        self.mockPort.reset_mock()
        portStr, cmd = 'ge.1.1', 'true'
        args = portStr + ' ' + cmd
        self.mockSwitch.get_ports_by_name.return_value = [self.mockPort]
        expected = ''

        result = self.cmd.do_adminedge(args)

        self.mockPort.set_stp_edge.assert_called_once_with(True, 'config')
        self.assertEqual(expected, result)

    def test_do_adminedge_ok_cmd_false(self):
        self.mockPort.reset_mock()
        portStr, cmd = 'ge.1.1', 'false'
        args = portStr + ' ' + cmd
        self.mockSwitch.get_ports_by_name.return_value = [self.mockPort]
        expected = ''

        result = self.cmd.do_adminedge(args)

        self.mockPort.set_stp_edge.assert_called_once_with(False, 'config')
        self.assertEqual(expected, result)

if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
