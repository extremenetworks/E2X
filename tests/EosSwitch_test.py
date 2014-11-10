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

from unittest.mock import patch, call, Mock

import EOS
from Port import Port
from VLAN import VLAN


class EosSwitch_test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gePortNameDict = {"prefix": "ge", "start": 1, "end": 2}
        cls.gePortsDict = {"label": {"start": 1, "end": 2},
                           "name": cls.gePortNameDict, "data": {}}
        cls.gePortsLabelStart = cls.gePortsDict['label']['start']
        cls.gePortsLabelEnd = cls.gePortsDict['label']['end']
        cls.nrOfPortsInGePortsDict = \
            cls.gePortsLabelEnd - cls.gePortsLabelStart \
            + 1

        cls.tePortNameDict = {"prefix": "te", "start": 1, "end": 1}
        cls.tePortsDict = {"label": {"start": 49, "end": 49},
                           "name": cls.tePortNameDict, "data": {}}
        cls.tePortsLabelStart = cls.tePortsDict['label']['start']
        cls.tePortsLabelEnd = cls.tePortsDict['label']['end']
        cls.nrOfPortsInTePortsDict = \
            cls.tePortsLabelEnd - cls.tePortsLabelStart \
            + 1

        cls.ErrorStart = 'ERROR:'
        cls.DebugStart = 'DEBUG:'

        cls.MacroExpDebugStr = cls.DebugStart + ' Macro expansion of: {}'
        cls.MacroExpErrStr = cls.ErrorStart + \
            ' Could not expand "set lacp static" macro'

    def setUp(self):
        self.sw = EOS.EosSwitch()
        self.firstGePortName = \
            self.sw._build_port_name(str(self.gePortNameDict['start']),
                                     self.gePortNameDict)
        self.lastGePortName = \
            self.sw._build_port_name(str(self.gePortNameDict['end']),
                                     self.gePortNameDict)
        self.firstTePortName = \
            self.sw._build_port_name(str(self.tePortNameDict['start']),
                                     self.tePortNameDict)

    def removeLinesStartingWithStrFromList(self, str, lst):
        result = [el for el in lst if not el.startswith(str)]
        return result

    def test_build_port_name(self):
        label = 1
        sep = self.sw._sep
        expected = self.gePortNameDict['prefix']
        expected += sep
        expected += str(self.sw.DEFAULT_SLOT_NR)
        expected += sep
        expected += str(label)

        result = self.sw._build_port_name(1, self.gePortNameDict)

        self.assertEqual(expected, result)

    def test_add_ports(self):
        with patch('Port.Port') as port:
            port.return_value = None

            self.sw.add_ports(self.gePortsDict)

            expected = [call(str(self.gePortsLabelStart),
                        self.firstGePortName, {}),
                        call(str(self.gePortsLabelEnd),
                             self.lastGePortName, {})]
            self.assertEqual(expected, port.call_args_list)

        self.assertEqual(self.nrOfPortsInGePortsDict, len(self.sw._ports))

    def test_add_ports_with_label_ne_index(self):
        expected = [call(str(self.tePortsLabelStart),
                    self.firstTePortName, {})]

        with patch('Port.Port') as port:
            port.return_value = None

            self.sw.add_ports(self.tePortsDict)

            self.assertEqual(expected, port.call_args_list)

        self.assertEqual(self.nrOfPortsInTePortsDict, len(self.sw._ports))

    def test_apply_default_settings(self):
        mockPort = Mock(spec=Port)
        self.sw._ports.append(mockPort)
        mockVlan = Mock(spec=VLAN)
        mockVlan.get_tag.return_value = 1
        self.sw._vlans.append((mockVlan))

        self.sw.apply_default_settings()

        methodCalls = [call.set_speed(10, 'default'),
                       call.set_duplex('half', 'default'),
                       call.set_auto_neg(True, 'default'),
                       call.set_admin_state(True, 'default'),
                       call.set_jumbo(True, 'default'),
                       call.set_lacp_enabled(False, 'default'),
                       call.set_lacp_aadminkey(32768, 'default'),
                       call.set_stp_enabled(True, 'default'),
                       call.set_stp_auto_edge(True, 'default'),
                       call.set_stp_edge(False, 'default'),
                       call.set_stp_bpdu_guard(False, 'default'),
                       call.set_stp_bpdu_guard_recovery_time(300, 'default'),
                       ]

        self.assertEqual(methodCalls, mockPort.method_calls)
        mockVlan.set_name.assert_called_with('DEFAULT VLAN', True)

    def test_port_name_matches_description(self):
        portName = 'ge.1.1'
        failures = ['', ' ', 'ge.1.2', 'ge.2.1', 'te.1.1', 'ge11',
                    'ge.1.2-3;ge.1.4;ge.1.5']
        successes = ['*.*.*', 'ge.*.*', '*.1.*', '*.*.1', 'ge.*.1', 'ge.1.*',
                     'ge.1.1', 'ge.1.1-10', 'ge.1.5;ge.1.4;ge.1.1']
#                    'ge.1.5-6;ge.1.2,ge.1.1-4']
        for d in failures:
            self.assertFalse(self.sw._port_name_matches_description(portName,
                                                                    d), d)
        for d in successes:
            self.assertTrue(self.sw._port_name_matches_description(portName,
                                                                   d), d)

    def test_expand_set_lacp_static_variant_1_ok(self):
        arg = 'set lacp static lag.0.5'
        expectedErrList = [arg]
        expExpandedList = ['set lacp static lag.0.5',
                           'set lacp aadminkey lag.0.5 5']
        expected = (expExpandedList, expectedErrList)

        (expandedList, errList) = self.sw._expand_set_lacp_static(arg)

        self.assertEqual(expExpandedList, expandedList)

    def test_expand_set_lacp_static_variant_2_ok(self):
        arg = 'set lacp static lag.0.6 ge.1.6'
        expectedErrList = [arg]
        expExpandedList = ['set lacp static lag.0.6',
                           'set lacp aadminkey lag.0.6 6',
                           'set port lacp port ge.1.6 aadminkey 6',
                           'set port lacp port ge.1.6 disable']
        expected = (expExpandedList, expectedErrList)

        (expandedList, errList) = self.sw._expand_set_lacp_static(arg)

        self.assertEqual(expExpandedList, expandedList)

    def test_expand_set_lacp_static_variant_3_ok(self):
        arg = 'set lacp static lag.0.5 key 42'
        expectedErrList = [arg]
        expExpandedList = ['set lacp static lag.0.5',
                           'set lacp aadminkey lag.0.5 42']
        expected = (expExpandedList, expectedErrList)

        (expandedList, errList) = self.sw._expand_set_lacp_static(arg)

        self.assertEqual(expExpandedList, expandedList)

    def test_expand_set_lacp_static_variant_4_ok(self):
        arg = 'set lacp static lag.0.5 key 4711 tg.1.49-50'
        expectedErrList = [arg]
        expExpandedList = ['set lacp static lag.0.5',
                           'set lacp aadminkey lag.0.5 4711',
                           'set port lacp port tg.1.49-50 aadminkey 4711',
                           'set port lacp port tg.1.49-50 disable']
        expected = (expExpandedList, expectedErrList)

        (expandedList, errList) = self.sw._expand_set_lacp_static(arg)

        self.assertEqual(expExpandedList, expandedList)

    def test_expand_set_lacp_static_fail_too_few_parameter(self):
        arg = 'set lacp static'
        debugStr = self.DebugStart + ' Macro expansion of: ' + arg
        errStr1 = self.ErrorStart + ' Incomplete "set lacp static" macro'
        errStr2 = self.ErrorStart + ' Could not expand "set lacp static" macro'
        expectedErrList = [debugStr, errStr1, errStr2]
        expExpandedList = [arg]
        expected = (expExpandedList, expectedErrList)

        result = self.sw._expand_set_lacp_static(arg)

        self.assertEqual(expected, result)

    def test_expand_set_lacp_static_fail_too_many_parameter(self):
        arg = 'set lacp static lag.0.1 key 4712 ge.1.1 ge.1.2'
        debugStr = self.DebugStart + ' Macro expansion of: ' + arg
        errStr1 = (self.ErrorStart +
                   ' Too many arguments to "set lacp static" macro')
        errStr2 = self.ErrorStart + ' Could not expand "set lacp static" macro'
        expectedErrList = [debugStr, errStr1, errStr2]
        expExpandedList = [arg]
        expected = (expExpandedList, expectedErrList)

        result = self.sw._expand_set_lacp_static(arg)

        self.assertEqual(expected, result)

    def test_expand_set_lacp_static_fail_lag_str_too_small(self):
        lagStr = 'lag.0'
        arg = 'set lacp static ' + lagStr

        expErrorList = [self.MacroExpDebugStr.format(arg),
                        self.ErrorStart + ' Illegal LAG string "' + lagStr +
                        '" in "set lacp static" macro',
                        self.MacroExpErrStr]
        expExpandedList = [arg]
        expected = (expExpandedList, expErrorList)

        result = self.sw._expand_set_lacp_static(arg)

        self.assertEqual(expected, result)

    def test_expand_set_lacp_static_fail_lag_nr_is_wildcard(self):
        lagNr = '*'
        lagStr = 'lag.0.' + lagNr
        arg = 'set lacp static ' + lagStr

        expErrorList = [self.MacroExpDebugStr.format(arg),
                        self.ErrorStart + ' Illegal LAG string "' + lagStr +
                        '" in "set lacp static" macro',
                        self.MacroExpErrStr]
        expExpandedList = [arg]
        expected = (expExpandedList, expErrorList)

        result = self.sw._expand_set_lacp_static(arg)

        self.assertEqual(expected, result)

    def test_expand_set_lacp_static_fail_lag_nr_is_no_int(self):
        lagNr = 'a'
        lagStr = 'lag.0.' + lagNr
        arg = 'set lacp static ' + lagStr

        expErrorList = [self.MacroExpDebugStr.format(arg),
                        self.ErrorStart + ' Illegal LAG number "' + lagNr +
                        '" in "set lacp static" macro',
                        self.MacroExpErrStr]
        expExpandedList = [arg]
        expected = (expExpandedList, expErrorList)

        result = self.sw._expand_set_lacp_static(arg)

        self.assertEqual(expected, result)

    def test_expand_set_lacp_static_fail_wrong_parameter_variant_1(self):
        arg = 'set lacp static lag.0.1 key ge.1.1 ge.1.2'
        debugStr = self.DebugStart + ' Macro expansion of: ' + arg
        errStr1 = self.ErrorStart + ' LACP actor key must be an integer'
        errStr2 = self.ErrorStart + ' Could not expand "set lacp static" macro'
        expectedErrList = [debugStr, errStr1, errStr2]
        expExpandedList = [arg]
        expected = (expExpandedList, expectedErrList)

        result = self.sw._expand_set_lacp_static(arg)

        self.assertEqual(expected, result)

    def test_expand_set_lacp_static_fail_wrong_parameter_variant_2(self):
        arg = 'set lacp static lag.0.1 key ge.1.1'
        debugStr = self.DebugStart + ' Macro expansion of: ' + arg
        errStr1 = self.ErrorStart + ' LACP actor key must be an integer'
        errStr2 = self.ErrorStart + ' Could not expand "set lacp static" macro'
        expectedErrList = [debugStr, errStr1, errStr2]
        expExpandedList = [arg]
        expected = (expExpandedList, expectedErrList)

        result = self.sw._expand_set_lacp_static(arg)

        self.assertEqual(expected, result)

    def test_expand_set_lacp_static_fail_wrong_parameter_variant_3(self):
        arg = 'set lacp static lag.0.1 ge.1.1 key 2'
        debugStr = self.DebugStart + ' Macro expansion of: ' + arg
        errStr1 = self.ErrorStart + ' Keyword "key" expected, got "ge.1.1"'
        errStr2 = self.ErrorStart + ' Could not expand "set lacp static" macro'
        expectedErrList = [debugStr, errStr1, errStr2]
        expExpandedList = [arg]
        expected = (expExpandedList, expectedErrList)

        result = self.sw._expand_set_lacp_static(arg)

        self.assertEqual(expected, result)

    def test_expand_set_lacp_static_fail_wrong_parameter_variant_4(self):
        arg = 'set lacp static lag.0.1 ge.1.1 key'
        debugStr = self.DebugStart + ' Macro expansion of: ' + arg
        errStr1 = self.ErrorStart + ' Keyword "key" expected, got "ge.1.1"'
        errStr2 = self.ErrorStart + ' Could not expand "set lacp static" macro'
        expectedErrList = [debugStr, errStr1, errStr2]
        expExpandedList = [arg]
        expected = (expExpandedList, expectedErrList)

        result = self.sw._expand_set_lacp_static(arg)

        self.assertEqual(expected, result)

    def test_expand_set_lacp_static_fail_wrong_parameter_variant_5(self):
        arg = 'set lacp static lag.0.1 ge.1.1 2'
        debugStr = self.DebugStart + ' Macro expansion of: ' + arg
        errStr1 = self.ErrorStart + ' Keyword "key" expected, got "ge.1.1"'
        errStr2 = self.ErrorStart + ' Could not expand "set lacp static" macro'
        expectedErrList = [debugStr, errStr1, errStr2]
        expExpandedList = [arg]
        expected = (expExpandedList, expectedErrList)

        result = self.sw._expand_set_lacp_static(arg)

        self.assertEqual(expected, result)

    def test_expand_set_lacp_static_fail_wrong_parameter_variant_6(self):
        arg = 'set lacp static lag.0.1 42 ge.1.1'
        debugStr = self.DebugStart + ' Macro expansion of: ' + arg
        errStr1 = self.ErrorStart + ' Keyword "key" expected, got "42"'
        errStr2 = self.ErrorStart + ' Could not expand "set lacp static" macro'
        expectedErrList = [debugStr, errStr1, errStr2]
        expExpandedList = [arg]
        expected = (expExpandedList, expectedErrList)

        result = self.sw._expand_set_lacp_static(arg)

        self.assertEqual(expected, result)

    def test_expand_set_lacp_static_fail_wrong_parameter_variant_7(self):
        arg = 'set lacp static lag.0.1 42'
        debugStr = self.DebugStart + ' Macro expansion of: ' + arg
        errStr1 = self.ErrorStart + ' Port string expected, but got "42"'
        errStr2 = self.ErrorStart + ' Could not expand "set lacp static" macro'
        expectedErrList = [debugStr, errStr1, errStr2]
        expExpandedList = [arg]
        expected = (expExpandedList, expectedErrList)

        result = self.sw._expand_set_lacp_static(arg)

        self.assertEqual(expected, result)

    def test_expand_set_lacp_static_fail_wrong_parameter_variant_8(self):
        arg = 'set lacp static lag.0.1 key'
        debugStr = self.DebugStart + ' Macro expansion of: ' + arg
        errStr1 = self.ErrorStart + ' Port string expected, but got "key"'
        errStr2 = self.ErrorStart + ' Could not expand "set lacp static" macro'
        expectedErrList = [debugStr, errStr1, errStr2]
        expExpandedList = [arg]
        expected = (expExpandedList, expectedErrList)

        result = self.sw._expand_set_lacp_static(arg)

        self.assertEqual(expected, result)

    def test_expand_set_lacp_static_fail_wrong_parameter_variant_9(self):
        arg = 'set lacp static lag.0.1 ge-te.*.*'
        debugStr = self.DebugStart + ' Macro expansion of: ' + arg
        errStr1 = (self.ErrorStart +
                   ' Port string expected, but got "ge-te.*.*"')
        errStr2 = self.ErrorStart + ' Could not expand "set lacp static" macro'
        expectedErrList = [debugStr, errStr1, errStr2]
        expExpandedList = [arg]
        expected = (expExpandedList, expectedErrList)

        result = self.sw._expand_set_lacp_static(arg)

        self.assertEqual(expected, result)

    def test_expand_macros_ok(self):
        confLst = ['set lacp static lag.0.5']
        expectedErrList = []
        expExpandedList = ['set lacp static lag.0.5',
                           'set lacp aadminkey lag.0.5 5']
        expected = (expExpandedList, expectedErrList)

        expandedLst, errList = self.sw.expand_macros(confLst)
        errList = \
            self.removeLinesStartingWithStrFromList(self.DebugStart,
                                                    errList)
        result = (expandedLst, errList)

        self.assertEqual(expected, result)

    def test_expand_macros_fail(self):
        confLst = ['not to expand']
        expectedErrList = []
        expExpandedList = confLst
        expected = (expExpandedList, expectedErrList)

        expandedLst, errList = self.sw.expand_macros(confLst)
        result = (expandedLst, errList)

        self.assertEqual(expected, result)

    def test_verify_port_string_syntax_ok(self):
        argList = ['fe.2.1-10', 'ge.3.14', 'ge.3.*', '*.*.*',
                   'fe,ge,tg,host,vlan,lag.*.1', 'ge.1.1;ge.2.2',
                   'ge.1,4-5,7.10,13,14-15,20', 'ge.1.1-2;lag.0.1',
                   'lag.0.2', '*.0.*', 'host.*.*', '*.*.20-23']
        for arg in argList:
            result = self.sw._verify_port_string_syntax(arg)
            self.assertTrue(result)

    def test_verify_port_string_syntax_fail(self):
        argList = ['fe.2.1+10', 'ge.3.14.15', 'ge.3.*,1', 'ge,*.*.*',
                   'fe,ge-tg,host,vlan,lag.*.1', 'ge.1.1,ge.2.2',
                   'ge.1,4-5-7.10,13,14-15,20', '*.a.*', '*.*.b', '..',
                   '*.*.', '*.*.*.', 'ge.1.1,', 'ge.1,.1', 'ge.1.1;',
                   ';ge.1.1', ',ge.1.1', '*,*.*', '*,.*.*', '*.*,.*',
                   '*.,*.*', '1.2.3', '1,2,3', '1-3', '1:1', '1-2:3-4']
        for arg in argList:
            result = self.sw._verify_port_string_syntax(arg)
            self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
