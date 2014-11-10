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

from unittest.mock import Mock

import CM
from Switch import Switch
from Switch import CmdInterpreter
from Port import Port
from VLAN import VLAN
from LAG import LAG
from STP import STP


class CM_Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.sourcePortName = 'ge.1.1'
        cls.targetPortName = '1'
        cls.sourceLagName = 'lag.0.1'
        cls.targetLagName = '1'

        cls.mockCmd = Mock(spec=CmdInterpreter)

        cls.mockSourceStp = Mock(name='SourceSTP', spec=STP)
        cls.mockTargetStp = Mock(name='TargetStp', spec=STP)

        cls.mockSourceVlan = Mock(name='SourceVlan', spec=VLAN)
        cls.mockTargetVlan = Mock(name='TargetVlan', spec=VLAN)

        cls.mockSourceLag = Mock(name='SourceLag', spec=LAG)
        cls.mockSourceLag.get_name.return_value = cls.sourceLagName
        cls.mockSourceLag.is_configured.return_value = True
        cls.mockSourceLag.is_disabled_only.return_value = False

        cls.mockTargetLag = Mock(name='TargetLag', spec=LAG)
        cls.mockTargetLag.get_name.return_value = cls.targetLagName

        cls.mockSourcePort = Mock(name='SourcePort', spec=Port)
        cls.mockSourcePort.get_name.return_value = cls.sourcePortName

        cls.mockTargetPort = Mock(name='TargetPort', spec=Port)
        cls.mockTargetPort.get_name.return_value = cls.targetPortName

        cls.mockSourceSwitch = Mock(name="Source", spec=Switch)
        cls.mockSourceSwitch.get_ports.return_value = [cls.mockSourcePort]
        cls.mockSourceSwitch.get_all_vlans.return_value = [cls.mockSourceVlan]

        cls.mockTargetSwitch = Mock(name='Target', spec=Switch)
        cls.mockTargetSwitch.get_ports.return_value = [cls.mockTargetPort]
        cls.mockTargetSwitch.get_cmd.return_value = cls.mockCmd
        cls.mockTargetSwitch.get_vlan.return_value = cls.mockTargetVlan
        cls.mockTargetSwitch.get_lags_by_name.return_value = \
            [cls.mockTargetLag]

        CM._devices = {'C5K125-48P2': {'use_as': 'source',
                                       'class': cls.mockSourceSwitch},
                       'SummitX460-48p': {'use_as': 'target',
                                          'class': cls.mockTargetSwitch},
                       'NoClass': {'use_as': 'target',
                                   'class': None}}
        cls.WarningStart = 'WARN: '
        cls.ErrorStart = 'ERROR: '
        cls.NoticeStart = 'NOTICE: '
        cls.InfoStart = 'INFO: '
        cls.DebugStart = 'DEBUG: '
        cls.ErrNoMapConfStr = cls.ErrorStart + '{} "{}" is configured, ' + \
            'but not mapped to target switch'
        cls.InfoNoConfTransferStr = cls.InfoStart + \
            '{} "{}" not mapped to target switch, no config transferred'

    def setUp(self):
        self.cm = CM.CoreModule()
        self.cm.source = self.mockSourceSwitch
        self.mockSourceSwitch.get_ports_by_name.return_value = \
            [self.mockSourcePort]
        self.cm.target = self.mockTargetSwitch
        self.mockTargetSwitch.get_ports_by_name.return_value = \
            [self.mockTargetPort]

    def test_get_source_switches(self):

        result = self.cm.get_source_switches()

        self.assertIsInstance(result, list)

    def test_get_target_switches(self):

        result = self.cm.get_target_switches()

        self.assertIsInstance(result, list)

    def test_set_source_switch_OK(self):
        sourceSwitch = 'C5K125-48P2'

        result = self.cm.set_source_switch(sourceSwitch)

        self.assertTrue(result)
        self.assertIsInstance(self.cm.source, Mock)

    def test_set_source_switch_Fail(self):
        sourceSwitch = 'Foo'
        self.cm.source = None

        result = self.cm.set_source_switch(sourceSwitch)

        self.assertFalse(result)
        self.assertIsNone(self.cm.source)

    def test_set_target_switch(self):
        targetSwitch = 'SummitX460-48p'

        self.cm.set_target_switch(targetSwitch)

        self.assertIsInstance(self.cm.target, Mock)

    def test_set_target_switch_Fail_Wrong_Model(self):
        targetSwitch = 'Foo'
        self.cm.target = None

        result = self.cm.set_target_switch(targetSwitch)

        self.assertFalse(result)
        self.assertIsNone(self.cm.target)

    def test_set_target_switch_Fail_No_Class(self):
        targetSwitch = 'NoClass'
        self.cm.target = None

        result = self.cm.set_target_switch(targetSwitch)

        self.assertFalse(result)
        self.assertIsNone(self.cm.target)

    def test_set_target_switch_Fail_No_Class_with_debug_enabled(self):
        targetSwitch = 'NoClass'
        self.cm.target = None
        self.cm.enable_debug()

        result = self.cm.set_target_switch(targetSwitch)

        self.assertFalse(result)
        self.assertIsNone(self.cm.target)

    def test_create_port_mapping_ok_debug_enabled(self):
        self.cm.enable_debug()
        expectedMappingList = {self.sourcePortName: self.targetPortName}
        self.mockTargetPort.is_equivalent.return_value = True

        (result, strList) = self.cm._create_port_mapping()

        self.assertEqual(expectedMappingList, self.cm._port_mapping_s2t)
        self.assertTrue(result)
        self.assertTrue(strList[0].startswith(self.NoticeStart))

    def test_create_port_mapping_fails(self):
        expectedWarning = self.WarningStart + 'Could not map port ' + \
            self.sourcePortName
        self.mockTargetPort.is_equivalent.return_value = False

        (result, strList) = self.cm._create_port_mapping()

        self.assertTrue(result)
        self.assertEqual(expectedWarning, strList[0])
        self.assertTrue(strList[1].startswith(self.NoticeStart))

    def test_translate_fails_because_source_or_target_not_specified(self):
        self.cm.source, self.cm.target = None, None
        translateList = ['set port disable ge.1.1']
        expected = [self.ErrorStart +
                    'Source and target switch needed for translation']

        translatedList, errorList = self.cm.translate(translateList)

        self.assertEqual(expected, errorList)

    def test_translate_fails_because_port_mapping_fails(self):
        translateList = ['set port disable ge.1.1']
        self.cm._create_port_mapping = Mock(return_value=(False, []))
        self.cm.source.expand_macros.return_value = [], []
        self.mockTargetPort.is_equivalent.return_value = False
        expected = [self.ErrorStart + 'Could not create valid port ' +
                    'mapping from source to target.']

        translatedList, errorList = self.cm.translate(translateList)

        self.assertEqual(expected, errorList)

    def test_translate_ok(self):
        translateList = ['set port disable ge.1.1']
        self.cm._create_port_mapping = Mock(return_value=(True, []))
        self.cm.source.configure.return_value = []
        self.cm.source.expand_macros.return_value = [], []
        self.cm.source.get_lags.return_value = []
        self.cm.target.configure.return_value = []
        self.cm.target.create_config.return_value = ([], [])

        self.cm.transfer_config = Mock(return_value=[])

        expected = [], []

        result = self.cm.translate(translateList)

        self.assertEqual(expected, result)

    def test_translate_copy_unknown_command(self):
        cmd = 'unknown command'
        translateList = [cmd]
        ignoringUnknownCmd = \
            'NOTICE: Ignoring unknown command "' + cmd + '"'
        self.cm.enable_copy_unknown()
        self.cm._create_port_mapping = Mock(return_value=(True, []))
        self.cm.source.configure.return_value = ignoringUnknownCmd
        self.cm.source.expand_macros.return_value = [cmd], []
        self.cm.source.get_lags.return_value = []
        self.cm.target.configure.return_value = []
        self.cm.target.create_config.return_value = ([], [])
        self.cm.transfer_config = Mock(return_value=[])
        expectedErr = [ignoringUnknownCmd]
        expectedTranslation = ['', cmd]
        expected = (expectedTranslation, expectedErr)

        result = self.cm.translate(translateList)

        self.assertEqual(expected, result)

    def test_translate_copy_unknown_command_and_comment_it(self):
        cmd = 'unknown command'
        commentChar = '#'
        translateList = [cmd]
        ignoringUnknownCmd = \
            'NOTICE: Ignoring unknown command "' + cmd + '"'
        self.cm.enable_copy_unknown()
        self.cm.enable_comment_unknown()
        self.cm._create_port_mapping = Mock(return_value=(True, []))
        self.cm.source.configure.return_value = ignoringUnknownCmd
        self.cm.source.expand_macros.return_value = [cmd], []
        self.cm.source.get_lags.return_value = []
        self.cm.target.configure.return_value = []
        self.cm.target.create_config.return_value = ([], [])
        self.cm.transfer_config = Mock(return_value=[])
        self.mockCmd.get_comment.return_value = commentChar
        expectedErrList = [ignoringUnknownCmd]
        expectedTranslationList = ['', commentChar + ' ' + cmd]
        expected = (expectedTranslationList, expectedErrList)

        result = self.cm.translate(translateList)

        self.assertEqual(expected, result)

    def test_translate_copy_unknown_command_and_comment_char_undef(self):
        cmd = 'unknown command'
        translateList = [cmd]
        ignoringUnknownCmd = \
            'NOTICE: Ignoring unknown command "' + cmd + '"'
        self.cm.enable_copy_unknown()
        self.cm.enable_comment_unknown()
        self.cm._create_port_mapping = Mock(return_value=(True, []))
        self.cm.source.configure.return_value = ignoringUnknownCmd
        self.cm.target.configure.return_value = []
        self.cm.target.create_config.return_value = ([], [])
        self.cm.transfer_config = Mock(return_value=[])
        self.mockCmd.get_comment.return_value = None
        expectedErr = self.ErrorStart + \
            'Cannot create comment line for unknown command'
        expectedTranslation = []
        expected = (expectedTranslation, [ignoringUnknownCmd, expectedErr])

        result = self.cm.translate(translateList)

        self.assertEqual(expected, result)

    def test_disable_enable_defaults(self):

        self.cm.disable_defaults()

        self.assertFalse(self.cm._apply_defaults)

        self.cm.enable_defaults()

        self.assertTrue(self.cm._apply_defaults)

    def test_disable_unused_ports(self):

        self.assertFalse(self.cm._disable_unused_ports)

        self.cm.disable_unused_ports()

        self.assertTrue(self.cm._disable_unused_ports)

    def test_enable_debug(self):

        self.assertFalse(self.cm._debug)

        self.cm.enable_debug()

        self.assertTrue(self.cm._debug)

    def test_enable_copy_unknown(self):

        self.assertFalse(self.cm._copy_unknown)

        self.cm.enable_copy_unknown()

        self.assertTrue(self.cm._copy_unknown)

    def test_enable_comment_unknown(self):

        self.assertFalse(self.cm._comment_unknown)

        self.cm.enable_comment_unknown()

        self.assertTrue(self.cm._comment_unknown)

    def _setUpSrcSwitch(self):
        srcSw = Switch()
        srcSw._ports.append(self.mockSourcePort)
        srcSw._lags.append(self.mockSourceLag)
        srcSw._stps.append(self.mockSourceStp)
        return srcSw

    def _setUpTargetSwitch(self):
        targetSw = Switch()
        targetSw._ports.append(self.mockTargetPort)
        targetSw._lags.append(self.mockTargetLag)
        targetSw._stps.append(self.mockTargetStp)
        return targetSw

    def test_transfer_config_mapped_port(self):
        self.cm.source = self._setUpSrcSwitch()
        self.cm.source._lags = []
        self.cm.target = self._setUpTargetSwitch()
        self.cm._port_mapping_s2t = {self.sourcePortName: self.targetPortName}
        self.cm._port_mapping_t2s = {self.targetPortName: self.sourcePortName}
        self.mockTargetPort.transfer_config.return_value = None
        self.mockTargetVlan.transfer_config.return_value = []

        expected = []

        result = self.cm.transfer_config()

        self.assertEquals(expected, result)

    def test_transfer_config_unmapped_configured_port(self):
        self.cm.source = self._setUpSrcSwitch()
        self.cm.source._lags = []
        self.cm.target = self._setUpTargetSwitch()
        self.cm._port_mapping_s2t = {self.sourcePortName: ''}
        self.cm._port_mapping_t2s = {self.targetPortName: ''}
        self.mockSourcePort.is_configured.return_value = True
        infoExpected = self.InfoNoConfTransferStr.format('Port',
                                                         self.sourcePortName)
        errorExpected = self.ErrNoMapConfStr.format('Port',
                                                    self.sourcePortName)
        expected = [infoExpected, errorExpected]

        result = self.cm.transfer_config()

        self.assertEquals(expected, result)

    def test_transfer_config_lag_ok(self):
        self.cm.source = self._setUpSrcSwitch()
        self.cm.target = self._setUpTargetSwitch()
        self.mockTargetLag.reset_mock()
        self.cm._port_mapping_s2t = {self.sourcePortName: self.targetPortName}
        self.cm._port_mapping_t2s = {self.targetPortName: self.sourcePortName}
        self.mockTargetPort.transfer_config.return_value = None
        self.mockTargetVlan.transfer_config.return_value = []
        self.cm._lag_mapping_s2t = {self.sourceLagName: self.targetLagName}
        self.cm._lag_mapping_t2s = {self.targetLagName: self.sourceLagName}
        expected = []

        result = self.cm.transfer_config()

        self.assertEqual(expected, result)
        self.mockTargetLag.transfer_config.assert_called_once_with(
            self.mockSourceLag)

    def test_transfer_config_lag_fail_src_lag_not_mpd_but_configured(self):
        self.cm.source = self._setUpSrcSwitch()
        self.cm.target = self._setUpTargetSwitch()
        self.cm._port_mapping_s2t = {self.sourcePortName: self.targetPortName}
        self.cm._port_mapping_t2s = {self.targetPortName: self.sourcePortName}
        self.mockTargetPort.transfer_config.return_value = None
        self.mockTargetVlan.transfer_config.return_value = []
        self.cm._lag_mapping_s2t = {self.sourceLagName: ''}
        self.mockSourceLag.is_disabled_only.return_value = False
        expInfoStr = self.InfoStart + 'LAG "' + self.sourceLagName + \
            '" not mapped to target switch, no config transferred'
        expErrStr = self.ErrorStart + 'LAG "' + self.sourceLagName + \
            '" is configured, but not mapped to target switch'
        expected = [expInfoStr, expErrStr]

        result = self.cm.transfer_config()

        self.assertEqual(expected, result)

    def test_transfer_config_lag_fail_src_lag_not_mpd_but_conf_disabled(self):
        self.cm.source = self._setUpSrcSwitch()
        self.cm.target = self._setUpTargetSwitch()
        self.cm._port_mapping_s2t = {self.sourcePortName: self.targetPortName}
        self.cm._port_mapping_t2s = {self.targetPortName: self.sourcePortName}
        self.mockTargetPort.transfer_config.return_value = None
        self.mockTargetVlan.transfer_config.return_value = []
        self.cm._lag_mapping_s2t = {self.sourceLagName: ''}
        self.mockSourceLag.is_disabled_only.return_value = True

        expInfoStr = self.InfoStart + 'LAG "' + self.sourceLagName + \
            '" not mapped to target switch, no config transferred'
        expNoticeStr = self.NoticeStart + 'LAG "' + self.sourceLagName + \
            '" is disabled, but not mapped to target switch'
        expected = [expInfoStr, expNoticeStr]

        result = self.cm.transfer_config()

        self.assertEqual(expected, result)

    def test_transfer_config_stp_ok_nr_of_stps_equal(self):
        self.mockTargetStp.reset_mock()
        self.cm.source = self._setUpSrcSwitch()
        self.cm.source._ports = []
        self.cm.source._lags = []
        self.cm.target = self._setUpTargetSwitch()
        self.cm._port_mapping_s2t = {}
        self.cm._port_mapping_t2s = {}

        expected = []

        result = self.cm.transfer_config()

        self.assertEqual(expected, result)
        self.mockTargetStp.transfer_config.assert_called_once_with(
            self.mockSourceStp)

    def test_transfer_config_stp_ok_nr_of_src_stps_greater(self):
        self.mockTargetStp.reset_mock()
        self.cm.source = self._setUpSrcSwitch()
        self.cm.source._ports = []
        self.cm.source._lags = []
        self.cm.source._stps.append(self.mockSourceStp)
        self.cm.target = self._setUpTargetSwitch()
        self.cm._port_mapping_s2t = {}
        self.cm._port_mapping_t2s = {}

        expected = []

        result = self.cm.transfer_config()

        self.assertEqual(expected, result)
        self.mockTargetStp.transfer_config.assert_called_once_with(
            self.mockSourceStp)

    def test_transfer_config_stp_ok_nr_of_target_stps_greater(self):
        self.mockTargetStp.reset_mock()
        self.cm.source = self._setUpSrcSwitch()
        self.cm.source._ports = []
        self.cm.source._lags = []
        self.cm.target = self._setUpTargetSwitch()
        self.cm.target._stps.append(self.mockTargetStp)
        self.cm._port_mapping_s2t = {}
        self.cm._port_mapping_t2s = {}

        expected = []

        result = self.cm.transfer_config()

        self.assertEqual(expected, result)
        self.mockTargetStp.transfer_config.assert_called_once_with(
            self.mockSourceStp)

    def test_check_mapping_consistency_debug(self):
        name = 'foo'
        self.cm._debug = True
        s2t, t2s = {'ge.1.1': '1'}, {'1': 'ge.1.1'}
        expectedRet = True
        expectedErrLst = [self.DebugStart + 'mapping ' + name +
                          ' ge.1.1 <-> 1']

        ret, errLst = self.cm._check_mapping_consistency(name, s2t, t2s)

        self.assertEqual(expectedRet, ret)
        self.assertEqual(expectedErrLst, errLst)

    def test_check_mapping_consistency_not_reflexive(self):
        name = 'foo'
        s2t, t2s = {'ge.1.1': '1'}, {'2': 'ge.1.1'}
        expectedRet = False
        expectedErrLst = [self.ErrorStart + name + ' mapping ' +
                          'is not reflexive']

        ret, errLst = self.cm._check_mapping_consistency('foo', s2t, t2s)

        self.assertEqual(expectedRet, ret)
        self.assertEqual(expectedErrLst, errLst)

    def test_check_mapping_consistency_source_ports_not_unique(self):
        name = 'foo'
        self.mockSourceSwitch.get_ports_by_name.return_value = \
            [self.mockSourcePort, self.mockSourcePort]
        s2t, t2s = {self.sourcePortName: '1'}, {'1': self.sourcePortName}
        expectedRet = True
        expectedErrLst = [self.DebugStart + name + ' name "' +
                          self.sourcePortName + '" not unique']

        ret, errLst = self.cm._check_mapping_consistency('foo', s2t, t2s)

        self.assertEqual(expectedRet, ret)
        self.assertEqual(expectedErrLst, errLst)

    def test_check_mapping_consistency_target_ports_not_unique(self):
        name = 'foo'
        self.mockTargetSwitch.get_ports_by_name.return_value = \
            [self.mockTargetPort, self.mockTargetPort]
        s2t, t2s = {'ge.1.1': self.targetPortName}, \
                   {self.targetPortName: 'ge.1.1'}
        expectedRet = True
        expectedErrLst = [self.DebugStart + name + ' name "' +
                          self.targetPortName + '" not unique']

        ret, errLst = self.cm._check_mapping_consistency('foo', s2t, t2s)

        self.assertEqual(expectedRet, ret)
        self.assertEqual(expectedErrLst, errLst)

    def test_create_lag_mapping_ok_target_lag_not_mapped(self):
        expectedRet = True
        expectedErrLst = []
        expected_s2t_LagMap = {self.sourceLagName: self.targetLagName}
        expected_t2s_LagMap = {self.targetLagName: self.sourceLagName}
        self.mockSourceSwitch.get_lags.return_value = [self.mockSourceLag]
        self.mockTargetSwitch.get_lags.return_value = [self.mockTargetLag]

        ret, errLst = self.cm._create_lag_mapping()

        self.assertEqual(expectedRet, ret)
        self.assertEqual(expectedErrLst, errLst)
        self.assertEqual(expected_s2t_LagMap, self.cm._lag_mapping_s2t)
        self.assertEqual(expected_t2s_LagMap, self.cm._lag_mapping_t2s)

    def test_create_lag_mapping_fails_srclag_unmpd_max_nr_targetlags_1(self):
        expectedRet = False
        expectedErrLst = []
        srcLag2 = Mock(spec=LAG)
        srcLag2.get_name.return_value = 'lag.0.2'
        srcLag2.is_configured.return_value = True
        srcLag2.is_disabled_only.return_value = False
        self.cm._lag_mapping_s2t = {self.sourceLagName: self.targetLagName}
        self.cm._lag_mapping_t2s = {self.targetLagName: self.sourceLagName}
        self.mockSourceSwitch.get_lags.return_value = [self.mockSourceLag,
                                                       srcLag2]
        self.mockTargetSwitch.get_lags.return_value = [self.mockTargetLag]
        self.mockTargetSwitch.get_max_lag.return_value = 1

        ret, errLst = self.cm._create_lag_mapping()

        self.assertEqual(expectedRet, ret)
        self.assertEqual(expectedErrLst, errLst)

    def test_create_lag_mapping_srclag_unmapped_add_lag_fails(self):
        expectedRet = False
        expectedErrLst = ['ERROR: Could not add LAG to ']
        srcLag2 = Mock(spec=LAG)
        srcLag2.get_name.return_value = 'lag.0.2'
        srcLag2.is_configured.return_value = True
        srcLag2.is_disabled_only.return_value = False
        self.cm._lag_mapping_s2t = {self.sourceLagName: self.targetLagName}
        self.cm._lag_mapping_t2s = {self.targetLagName: self.sourceLagName}
        self.mockSourceSwitch.get_lags.return_value = [self.mockSourceLag,
                                                       srcLag2]
        self.mockTargetSwitch.get_lags.return_value = [self.mockTargetLag]
        self.mockTargetSwitch.get_max_lag.return_value = 2
        self.mockTargetSwitch.add_lag.return_value = expectedErrLst[0]

        ret, errLst = self.cm._create_lag_mapping()

        self.assertEqual(expectedRet, ret)
        self.assertEqual(expectedErrLst, errLst)

    def test_create_lag_mapping_srclag_unmapped_ok(self):
        expectedRet = True
        expectedErrLst = []
        srcLag2_Name = 'lag.0.2'
        targetLag2_Name = 'tgt_lag_2'
        srcLag2 = Mock(spec=LAG)
        srcLag2.get_name.return_value = srcLag2_Name
        srcLag2.is_configured.return_value = True
        srcLag2.is_disabled_only.return_value = False
        self.cm._lag_mapping_s2t = {self.sourceLagName: self.targetLagName}
        self.cm._lag_mapping_t2s = {self.targetLagName: self.sourceLagName}
        expLagMapping_s2t = {self.sourceLagName: self.targetLagName,
                             srcLag2_Name: targetLag2_Name}
        self.mockSourceSwitch.get_lags.return_value = [self.mockSourceLag,
                                                       srcLag2]
        self.mockTargetSwitch.get_lags.return_value = [self.mockTargetLag]
        self.mockTargetSwitch.get_max_lag.return_value = 2
        self.mockTargetSwitch.add_lag.return_value = ''
        self.mockTargetSwitch.create_lag_name.return_value = targetLag2_Name

        ret, errLst = self.cm._create_lag_mapping()

        self.assertEqual(expectedRet, ret)
        self.assertEqual(expectedErrLst, errLst)
        self.assertEqual(expLagMapping_s2t, self.cm._lag_mapping_s2t)

    if __name__ == '__main__':
        unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
