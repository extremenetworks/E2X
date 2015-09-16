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
from unittest.mock import MagicMock, patch, call

import sys
sys.path.extend(['../src'])

import Port
import Switch
import VLAN
import LAG
import STP
from ACL import ACL


class Switch_test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.portsDict = {"label": {"start": 1, "end": 2},
                         "name": {"start": 1, "end": 2},
                         "data": {}}
        cls.hwDesc = (['{"ports":{"label":{"start":1,"end":2},'
                       ' "name":{"start": 1, "end": 2},"data":{}}}'])

        cls.mockVlan1 = MagicMock(spec=VLAN.VLAN)()
        cls.mockVlan1.get_name.return_value = 'foo'
        cls.mockVlan1.get_tag.return_value = 1

        cls.mockVlan2 = MagicMock(spec=VLAN.VLAN)()
        cls.mockVlan2.get_name.return_value = 'baz'
        cls.mockVlan2.get_tag.return_value = 2

        cls.mockLag = MagicMock(spec=LAG.LAG)
        cls.mockLag.get_name.return_value = 'bar'

        cls.mockStp = MagicMock(spec=STP.STP)
        cls.mockStp.get_mst_instance.return_value = 1

        cls.mockStp2 = MagicMock(spec=STP.STP)
        cls.mockStp2.get_name.return_value = 's2'
        cls.mockStp2.get_mst_instance.return_value = 1

        cls.ErrorStart = 'ERROR: '
        cls.WarnStart = 'WARN: '

    def setUp(self):
        self.sw = Switch.Switch()

    def test_setup_hw(self):
        self.sw._add_ports = MagicMock()
        self.sw._hw_desc.append(self.hwDesc)

        self.sw._setup_hw()

        self.sw._add_ports.assert_called_once_with(self.portsDict, 1)

    def test_is_stack_default_no(self):

        self.assertFalse(self.sw.is_stack())

    #
    # Ports
    #
    def test_add_ports(self):
        self.sw._build_port_name = MagicMock(return_value='name')

        with patch('Port.Port') as port:
            port.return_value = None

            self.sw._add_ports(Switch_test.portsDict, 1)
            expected = [call('1', 'name', {}), call('2', 'name', {})]
            self.assertEqual(expected, port.call_args_list)

        self.assertEqual(2, len(self.sw._ports))
        self.assertIsNone(self.sw._ports[0])
        self.assertIsNone(self.sw._ports[1])

    def test_get_ports(self):
        p = MagicMock(spec=Port.Port)
        self.sw._ports.append(p)

        portList = self.sw.get_ports()

        self.assertEqual(p, portList[0])

    def test_build_port_name(self):
        expected = Switch.Switch.DEFAULT_PORT_NAME

        result = self.sw._build_port_name(-1, {}, 1)

        self.assertEqual(expected, result)

    def _add_ports_to_switch(self, port1Name, port2Name):
        portData = {"type": "rj45",
                    "speedrange": [10, 100, 1000], "PoE": "yes"}
        port1 = Port.Port(1, port1Name, portData)
        port2 = Port.Port(2, port2Name, portData)
        self.sw._ports.append(port1)
        self.sw._ports.append(port2)

    def test_get_ports_by_name(self):
        port1Name = 'ge.1.1'
        port2Name = 'ge.1.2'
        self._add_ports_to_switch(port1Name, port2Name)

        portList = self.sw.get_ports_by_name(port1Name)

        self.assertEqual(1, len(portList))
        self.assertEqual(port1Name, portList[0].get_name())

    def test_get_physical_ports_by_name(self):
        port1Name = 'ge.1.1'
        port2Name = 'ge.1.2'
        self._add_ports_to_switch(port1Name, port2Name)

        portList = self.sw.get_physical_ports_by_name(port1Name)

        self.assertEqual(1, len(portList))
        self.assertEqual(port1Name, portList[0].get_name())

    def test_set_combo_using_sfp_ok(self):
        sfpList = ['ge.1.47', 'ge.1.48']
        port47Name = 'ge.1.47'
        port48Name = 'ge.1.48'
        portData = {"type": "combo",
                    "speedrange": [10, 100, 1000], "PoE": "yes"}
        port48 = Port.Port(47, port47Name, portData)
        port47 = Port.Port(48, port48Name, portData)
        self.sw._ports.append(port47)
        self.sw._ports.append(port48)
        expected = 'sfp'

        self.sw.set_combo_using_sfp(sfpList)

        self.assertEqual(expected, port47.get_connector_used())
        self.assertEqual(expected, port48.get_connector_used())

    def test_set_combo_using_sfp_fail_wrong_port_type(self):
        portName = 'ge.1.1'
        portType = 'rj45'
        sfpList = [portName]

        expected = [self.ErrorStart + 'Port ' + portName +
                    ' cannot use an SFP module']
        p = MagicMock(spec=Port.Port)

        p.get_name.return_value = portName
        p.get_connector_used.return_value = portType
        p.get_connector.return_value = portType
        self.sw._ports.append(p)

        result = self.sw.set_combo_using_sfp(sfpList)

        self.assertEqual(expected, result)

    def test_set_combo_using_sfp_fail_port_does_not_exist(self):
        portName = 'ge.1.1'
        sfpList = [portName]

        expected = [self.ErrorStart + 'Non-existing port "' + portName +
                    '" cannot use an SFP module']

        result = self.sw.set_combo_using_sfp(sfpList)

        self.assertEqual(expected, result)

    #
    # Attributes
    #
    def test_get_model(self):

        self.assertIsNone(self.sw.get_model())

    def test_get_os(self):

        self.assertIsNone(self.sw.get_os())

    def test_str(self):
        p = MagicMock(spec=Port.Port)
        p.__str__.return_value = ''

        l = MagicMock(spec=LAG.LAG)
        l.__str__.return_value = ''

        v = MagicMock(spec=VLAN.VLAN)
        v.__str__.return_value = ''

        self.maxDiff = None

        self.sw._model = 'nn'
        self.sw._os = 'nn'
        self.sw._ports.append(p)
        self.sw._vlans.append(v)
        self.sw._lags.append(l)

        expected = ' Model: nn' + '\n'
        expected += ' OS:    nn' + '\n'
        expected += ' Prompt: (None, None)\n'
        expected += ' SNMP SysName: (None, None)\n'
        expected += ' SNMP SysContact: (None, None)\n'
        expected += ' SNMP SysLocation: (None, None)\n'
        expected += ' Login Banner: (None, None)\n'
        expected += ' Login Banner Acknowledge: (None, None)\n'
        expected += ' MOTD Banner: (None, None)\n'
        expected += ' Inbound Telnet: (None, None)\n'
        expected += ' Outbound Telnet: (None, None)\n'
        expected += ' Inbound SSH: (None, None)\n'
        expected += ' Outbound SSH: (None, None)\n'
        expected += ' SSL: (None, None)\n'
        expected += ' HTTP: (None, None)\n'
        expected += ' HTTPS: (None, None)\n'
        expected += ' Mgmt IP: (None, None)\n'
        expected += ' Mgmt Netmask: (None, None)\n'
        expected += ' Mgmt VLAN: (None, None)\n'
        expected += ' Mgmt Gateway: (None, None)\n'
        expected += ' Mgmt Protocol: (None, None)\n'
        expected += ' Idle Timeout: (None, None)\n'
        expected += ' Syslog Servers:\n'
        expected += ' SNTP Client Mode: (None, None)\n'
        expected += ' SNTP Servers:\n'
        expected += ' Ports:'
        for p in self.sw._ports:
            expected += ' ()'
        expected += '\n VLANs:'
        for v in self.sw._vlans:
            expected += ' ()'
        expected += '\n Loopbacks:'
        expected += '\n'
        expected += ' LAGs:'
        for l in self.sw._lags:
            expected += ' ()'
        expected += '\n'
        expected += ' Global LACP: (None, None)\n'
        expected += ' Max. LAGs: (None, None)\n'
        expected += ' Single Port LAG: (None, None)\n'
        expected += ' Spanning Tree:\n'
        expected += ' ACLs:\n'
        expected += ' IPv4 Routing: (None, None)\n'
        expected += ' IPv4 Static Routes: set()\n'

        result = str(self.sw)

        self.assertEqual(expected, result)

    #
    # Lags
    #
    def _add_lags_to_switch(self, lag1Name, lag2Name):
        lag1 = LAG.LAG(1, name=lag1Name)
        lag2 = LAG.LAG(2, name=lag2Name)
        self.sw._lags.append(lag1)
        self.sw._lags.append(lag2)

    def test_create_lag_name(self):
        lagNr = 1
        expected = '_new_lag_1'

        result = self.sw.create_lag_name(lagNr, [])

        self.assertEqual(expected, result)

    def test_get_lags_by_name(self):
        lag1Name = 'lag.0.1'
        lag2Name = 'lag.0.2'
        self._add_lags_to_switch(lag1Name, lag2Name)

        lagList = self.sw.get_lags_by_name(lag1Name)

        self.assertEqual(1, len(lagList))
        self.assertEqual(lag1Name, lagList[0].get_name())

    def test_set_get_lacp_support_ok(self):
        reason = 'test'

        result = self.sw.set_lacp_support('1', 'test')

        self.assertTrue(result)
        self.assertTrue(self.sw.get_lacp_support())
        self.assertEqual(reason, self.sw.get_lacp_support_reason())

    def test_get_lags(self):
        lag1Name = 'lag.0.1'
        lag2Name = 'lag.0.2'
        self._add_lags_to_switch(lag1Name, lag2Name)

        lagList = self.sw.get_lags()

        self.assertEqual(2, len(lagList))
        self.assertEqual(lag1Name, lagList[0].get_name())
        self.assertEqual(lag2Name, lagList[1].get_name())

    def test_get_lag_by_number_ok(self):
        lagNr = 1
        lag1Name = 'lag.0.' + str(lagNr)
        lag2Name = 'lag.0.2'
        self._add_lags_to_switch(lag1Name, lag2Name)

        lag = self.sw.get_lag_by_number(lagNr)

        self.assertEqual(lag1Name, lag.get_name())

    def test_get_lag_by_number_too_big_fail(self):
        lag1Name = 'lag.0.1'
        lag2Name = 'lag.0.2'
        self._add_lags_to_switch(lag1Name, lag2Name)

        lag = self.sw.get_lag_by_number(3)

        self.assertIsNone(lag)

    def test_get_lag_by_number_too_small_fail(self):
        lag1Name = 'lag.0.1'
        lag2Name = 'lag.0.2'
        self._add_lags_to_switch(lag1Name, lag2Name)

        lag = self.sw.get_lag_by_number(0)

        self.assertIsNone(lag)

    def test_get_lag_ports_fail_wrong_lag_nr(self):
        lag1Name = 'lag.0.1'
        lag2Name = 'lag.0.2'
        self._add_lags_to_switch(lag1Name, lag2Name)
        expected = []

        result = self.sw.get_lag_ports(0)

        self.assertEqual(expected, result)

    def test_get_lag_ports_ok(self):
        lag1Name = 'lag.0.1'
        lag2Name = 'lag.0.2'
        portName = 'ge.1.1'
        self._add_lags_to_switch(lag1Name, lag2Name)
        self.sw.get_lag_by_number(1).add_member_port(portName)
        expected = [portName]

        result = self.sw.get_lag_ports(1)

        self.assertEqual(expected, result)

    def test_set_get_max_lag_ok(self):
        reasen = 'test'
        max_lags = 2

        result = self.sw.set_max_lag(max_lags, 'test')

        self.assertEqual(max_lags, result)
        self.assertEqual(max_lags, self.sw.get_max_lag())
        self.assertEqual(reasen, self.sw.get_max_lag_reason())

    def test_set_max_lag_fail(self):
        max_lags = 'two'

        result = self.sw.set_max_lag(max_lags, 'test')

        self.assertIsNone(result)
        self.assertIsNone(self.sw.get_max_lag_reason())

    def test_add_lag(self):
        expLen = len(self.sw._lags) + 1
        expResult = ''

        result = self.sw.add_lag(self.mockLag)

        self.assertEqual(expResult, result)
        self.assertEqual(expLen, len(self.sw._lags))

    def test_add_lag_lag_exists(self):
        self.sw._lags.append(self.mockLag)
        expLen = len(self.sw._lags)
        expResult = self.ErrorStart + 'LAG with name "' + \
            self.mockLag.get_name() + '" already exists, cannot add it to ' + \
            'switch again'

        result = self.sw.add_lag(self.mockLag)

        self.assertEqual(expResult, result)
        self.assertEqual(expLen, len(self.sw._lags))

    def test_add_lag_max_nr_of_lags_reached(self):
        self.sw._lags.append(self.mockLag)
        self.sw._max_lag = (1, 'test')
        self.sw._model = 'nn'
        expLen = len(self.sw._lags)
        expResult = self.ErrorStart + 'Could not add LAG to nn'

        result = self.sw.add_lag(self.mockLag)

        self.assertEqual(expResult, result)
        self.assertEqual(expLen, len(self.sw._lags))

    # lacp support differs from source sw
    def test_transfer_config_lacp_src_sw_reason_is_default(self):
        src_sw = MagicMock(Switch.Switch)
        src_sw.get_lacp_support.return_value = True
        src_sw.get_lacp_support_reason.return_value = 'default'

        self.sw.transfer_config(src_sw)

        self.assertTrue(self.sw.get_lacp_support())
        self.assertEqual('transfer_def', self.sw.get_lacp_support_reason())

    def test_transfer_config_lacp_src_sw_reason_is_not_default(self):
        src_sw = MagicMock(Switch.Switch)
        src_sw.get_lacp_support.return_value = True
        src_sw.get_lacp_support_reason.return_value = 'test'

        self.sw.transfer_config(src_sw)

        self.assertTrue(self.sw.get_lacp_support())
        self.assertEqual('transfer_conf', self.sw.get_lacp_support_reason())

    # max lag differs from source sw
    def test_transfer_config_max_lag_src_sw_reason_is_default(self):
        max_lag = 1
        src_sw = MagicMock(Switch.Switch)
        src_sw.get_max_lag.return_value = max_lag
        src_sw.get_max_lag_reason.return_value = 'default'

        self.sw.transfer_config(src_sw)

        self.assertEqual(max_lag, self.sw.get_max_lag())
        self.assertEqual('transfer_def', self.sw.get_max_lag_reason())

    def test_transfer_config_max_lag_src_sw_reason_is_not_default(self):
        max_lag = 1
        src_sw = MagicMock(Switch.Switch)
        src_sw.get_max_lag.return_value = max_lag
        src_sw.get_max_lag_reason.return_value = 'test'

        self.sw.transfer_config(src_sw)

        self.assertEqual(max_lag, self.sw.get_max_lag())
        self.assertEqual('transfer_conf', self.sw.get_max_lag_reason())

    # single port lag differs from source sw
    def test_transfer_config_spl_src_sw_reason_is_default(self):
        src_sw = MagicMock(Switch.Switch)
        src_sw.get_single_port_lag.return_value = True
        src_sw.get_single_port_lag_reason.return_value = 'default'

        self.sw.transfer_config(src_sw)

        self.assertTrue(self.sw.get_single_port_lag())
        self.assertEqual('transfer_def', self.sw.get_single_port_lag_reason())

    def test_transfer_config_spl_src_sw_reason_is_not_default(self):
        src_sw = MagicMock(Switch.Switch)
        src_sw.get_single_port_lag.return_value = True
        src_sw.get_single_port_lag_reason.return_value = 'test'

        self.sw.transfer_config(src_sw)

        self.assertTrue(self.sw.get_single_port_lag())
        self.assertEqual('transfer_conf', self.sw.get_single_port_lag_reason())

    #
    # Configuration
    #
    def test_configure_unknown_command(self):
        configline = 'foo'
        expected = 'NOTICE: Ignoring unknown command "' + configline + '"'

        result = self.sw.configure(configline)

        self.assertEqual(expected, result)

    def test_configure_comment(self):
        self.sw._cmd._is_comment = MagicMock(return_value=True)
        configline = '!foo'
        expected = 'INFO: Ignoring comment "' + configline + '"'

        result = self.sw.configure(configline)

        self.assertEqual(expected, result)

    def test_init_conf_values(self):
        p = MagicMock(spec=Port.Port)
        self.sw._ports.append(p)
        self.sw._lags.append(self.mockLag)

        self.sw.init_conf_values()

        p.init_conf_values.assert_called_once_with()
        self.assertEqual(1, self.sw.get_all_vlans()[0].get_tag())

    def test_apply_default_settings(self):
        self.sw.apply_default_settings()

    def test_create_config_no_oob(self):
        self.sw._writer.generate = MagicMock()

        self.sw.create_config(False)

        self.sw._writer.generate.assert_called_once_with()
        self.assertFalse(self.sw._use_oob_mgmt)

    def test_create_config_with_oob(self):
        self.sw._writer.generate = MagicMock()
        self.sw.create_config(True)
        self.sw._writer.generate.assert_called_once_with()
        self.assertTrue(self.sw._use_oob_mgmt)

    def test_expand_macros(self):
        config = 'foo'

        result, errors = self.sw.expand_macros(config)

        self.assertEqual(config, result)
        self.assertEqual(errors, [])

    def test_get_cmd(self):

        result = self.sw.get_cmd()

        self.assertIsInstance(result, Switch.CmdInterpreter)

    #
    # Vlans
    #
    def test_get_vlan_fail_tag_and_name_not_set(self):
        expected = None

        result = self.sw.get_vlan()

        self.assertEqual(expected, result)

    def test_get_vlan_fail_vlan_not_found_tag_and_name_not_equal(self):
        self.sw._vlans.append(self.mockVlan1)
        expected = None

        result = self.sw.get_vlan(name='bah', tag=2)

        self.assertEqual(expected, result)

    def test_get_vlan_ok_tag_not_set(self):
        self.sw._vlans.append(self.mockVlan1)
        expected = self.mockVlan1

        result = self.sw.get_vlan(name='foo')

        self.assertEqual(expected, result)

    def test_get_vlan_ok_name_not_set(self):
        self.sw._vlans.append(self.mockVlan1)
        expected = self.mockVlan1

        result = self.sw.get_vlan(tag=1)

        self.assertEqual(expected, result)

    def test_get_vlan_ok_name_and_tag_set(self):
        self.sw._vlans.append(self.mockVlan1)
        expected = self.mockVlan1

        result = self.sw.get_vlan(name='foo', tag=1)

        self.assertEqual(expected, result)

    def test_get_all_vlans(self):
        self.sw._vlans.append(self.mockVlan1)
        expected = [self.mockVlan1]

        result = self.sw.get_all_vlans()

        self.assertEqual(expected, result)

    def test_add_vlan_vlan_exists(self):
        self.sw._vlans.append(self.mockVlan1)
        expectedLen = len(self.sw._vlans)

        self.sw.add_vlan(self.mockVlan1)

        self.assertEqual(expectedLen, len(self.sw._vlans))

    def test_add_vlan_vlan_does_not_exist(self):
        expectedLen = len(self.sw._vlans) + 1

        self.sw.add_vlan(self.mockVlan1)

        self.assertEqual(expectedLen, len(self.sw._vlans))

    def test_is_port_in_non_default_vlan_no_vlans(self):
        port1Name = 'ge.1.1'
        self.assertFalse(self.sw.is_port_in_non_default_vlan(port1Name))

    def test_is_port_in_non_default_vlan_default_vlan_only(self):
        port1Name = 'ge.1.1'
        self.mockVlan1.contains_port.return_value = True
        self.sw.add_vlan(self.mockVlan1)
        self.assertFalse(self.sw.is_port_in_non_default_vlan(port1Name))

    def test_is_port_in_non_default_vlan_port_in_vlan_1(self):
        port1Name = 'ge.1.1'
        self.mockVlan1.contains_port.return_value = True
        self.mockVlan2.contains_port.return_value = False
        self.sw.add_vlan(self.mockVlan1)
        self.sw.add_vlan(self.mockVlan2)
        self.assertFalse(self.sw.is_port_in_non_default_vlan(port1Name))

    def test_is_port_in_non_default_vlan_port_in_vlan_2(self):
        port1Name = 'ge.1.1'
        self.mockVlan1.contains_port.return_value = False
        self.mockVlan2.contains_port.return_value = True
        self.sw.add_vlan(self.mockVlan1)
        self.sw.add_vlan(self.mockVlan2)
        self.assertTrue(self.sw.is_port_in_non_default_vlan(port1Name))

    def test_is_port_in_non_default_vlan_port_in_vlans_1_and_2(self):
        port1Name = 'ge.1.1'
        self.mockVlan1.contains_port.return_value = True
        self.mockVlan2.contains_port.return_value = True
        self.sw.add_vlan(self.mockVlan1)
        self.sw.add_vlan(self.mockVlan2)
        self.assertTrue(self.sw.is_port_in_non_default_vlan(port1Name))

    #
    #   Stps
    #
    def test_get_stp_by_mst_instance_no_stps_defined(self):

        self.assertIsNone(self.sw.get_stp_by_mst_instance(1))

    def test_add_stp(self):
        nrOfStps = len(self.sw.get_stps())
        expectedLen = nrOfStps + 1

        self.sw.add_stp(self.mockStp)

        self.assertEqual(expectedLen, len(self.sw.get_stps()))

    def test_add_stp_stp_already_defined(self):
        self.sw.add_stp(self.mockStp)
        nrOfStps = len(self.sw.get_stps())
        expectedLen = nrOfStps

        self.sw.add_stp(self.mockStp)

        self.assertEqual(expectedLen, len(self.sw.get_stps()))

    def test_get_stp_by_mst_instance_single_stp(self):
        self.sw.add_stp(self.mockStp)

        result = \
            self.sw.get_stp_by_mst_instance(self.mockStp.get_mst_instance())

        self.assertEqual(self.mockStp, result)

    def test_get_stp_multiple_stps_defined(self):
        stp = STP.STP()
        id = 2
        stp.set_mst_instance(id, 'test')
        self.sw.add_stp(self.mockStp)
        self.sw.add_stp(stp)

        result = \
            self.sw.get_stp_by_mst_instance(id)

        self.assertEqual(stp, result)

    def test_delete_stp_by_instance_id_id_not_present(self):
        id = 2
        self.sw.add_stp(self.mockStp)
        nrOfStps = len(self.sw.get_stps())
        expectedLen = nrOfStps
        expWarnStr = self.WarnStart + 'Cannot delete MST instance "' + \
            str(id) + '":  Instance does not exist'

        result = self.sw.delete_stp_by_instance_id(id)

        self.assertEqual(expectedLen, len(self.sw.get_stps()))
        self.assertEqual(expWarnStr, result)

    def test_delete_stp_by_instance_id_several_ids_present(self):
        id = self.mockStp.get_mst_instance()
        self.sw.add_stp(self.mockStp)
        self.sw.add_stp(self.mockStp2)
        nrOfStps = len(self.sw.get_stps())
        expectedLen = nrOfStps - 2
        expWarnStr = self.WarnStart + 'Found more than 1 MST instance "' + \
            str(id) + '": Deleting all'

        result = self.sw.delete_stp_by_instance_id(id)

        self.assertEqual(expectedLen, len(self.sw.get_stps()))
        self.assertEqual(expWarnStr, result)

    def test_delete_stp_by_instance_id_id_present_once(self):
        id = self.mockStp.get_mst_instance()
        self.sw.add_stp(self.mockStp)
        nrOfStps = len(self.sw.get_stps())
        expectedLen = nrOfStps - 1
        expected = ''

        result = self.sw.delete_stp_by_instance_id(id)

        self.assertEqual(expectedLen, len(self.sw.get_stps()))
        self.assertEqual(expected, result)

    def test_add_acl_parametersValid(self):
        nr_of_acls = len(self.sw._acls)

        result = self.sw.add_acl(number=1)

        self.assertEqual(nr_of_acls + 1, len(self.sw._acls))
        self.assertEqual('', result)

    def test_add_acl_parametersMissing(self):
        nr_of_acls = len(self.sw._acls)

        result = self.sw.add_acl()

        self.assertEqual(nr_of_acls, len(self.sw._acls))
        self.assertIn('ERROR', result)

    def test_add_acl_bothParametersSet(self):
        nr_of_acls = len(self.sw._acls)

        result = self.sw.add_acl(1, 'test')

        self.assertEqual(nr_of_acls, len(self.sw._acls))
        self.assertIn('ERROR', result)

    def test_add_acl_aclWithSameNameAlreadyExists(self):
        acl = ACL(name='test')
        self.sw.add_complete_acl(acl)
        nr_of_acls = len(self.sw._acls)

        result = self.sw.add_acl(name='test')

        self.assertEqual(nr_of_acls, len(self.sw._acls))
        self.assertIn('ERROR', result)

    def test_add_acl_aclWithSameNumberAlreadyExists(self):
        acl = ACL(number=1)
        self.sw.add_complete_acl(acl)
        nr_of_acls = len(self.sw._acls)

        result = self.sw.add_acl(number=1)

        self.assertEqual(nr_of_acls, len(self.sw._acls))
        self.assertIn('ERROR', result)

if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
