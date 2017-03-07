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

import Port
import Switch
import XOS
import XOS_write
import VLAN
import LAG
import STP
from ACL import ACL
from ACL import ACE

from unittest.mock import MagicMock


class XosConfigWriter_test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.portName = 'ge.1.1'
        cls.lagName = 'lag1'
        cls.stpName = 'stp1'

        cls.mockStp = MagicMock(spec=STP.STP)
        cls.mockStp.get_name.return_value = cls.stpName

        cls.mockLag = MagicMock(spec=LAG.LAG)
        cls.mockLag.get_name.return_value = cls.lagName

        cls.mockVlan = MagicMock(spec=VLAN.VLAN)

        cls.mockPort = MagicMock(spec=Port.Port)
        cls.mockPort.get_name.return_value = cls.portName

        cls.mockTargetPort1 = MagicMock(spec=Port.Port)
        cls.mockTargetPort1.get_name.return_value = '1'

        cls.mockTargetPort2 = MagicMock(spec=Port.Port)
        cls.mockTargetPort2.get_name.return_value = '2'

        cls.mockTargetPort3 = MagicMock(spec=Port.Port)
        cls.mockTargetPort3.get_name.return_value = '3'

        cls.mockTargetPort4 = MagicMock(spec=Port.Port)
        cls.mockTargetPort4.get_name.return_value = '4'

        cls.mockTargetSwitch = MagicMock(spec=Switch.Switch)

        cls.mockSwitch = MagicMock(spec=Switch.Switch)
        cls.mockSwitch.get_ports.return_value = [cls.mockPort]
        cls.mockSwitch.is_stack.return_value = False

        cls.confPortsStr = 'configure ports ' + cls.portName
        cls.enablePortsStr = 'enable ports ' + cls.portName
        cls.disablePortsStr = 'disable ports ' + cls.portName
        cls.confPortsAutoStr = cls.confPortsStr + ' auto '
        cls.confPortsDisplStr = cls.confPortsStr + ' display-string '
        cls.confPortsDescrStr = cls.confPortsStr + ' description-string ""'
        cls.disableJumboStr = 'disable jumbo-frame ports ' + cls.portName
        cls.enableJumboStr = 'enable jumbo-frame ports ' + cls.portName
        cls.confAcl42Str = ('configure access-list acl_42 ports ' +
                            cls.portName + ' ingress')

        cls.WarningStart = 'WARN: '
        cls.ErrorStart = 'ERROR: '
        cls.InfoStart = 'INFO: '
        cls.NoticeStart = 'NOTICE: '

        cls.errXosNeedsOneInstance = cls.ErrorStart + \
            'XOS needs at least one MST instance, CIST only is not possible'
        cls.errNoVlansAssoc = cls.ErrorStart + 'No VLANs associated with ' + \
            'any MST instance'
        cls.warnDefVlanNotInInstance = cls.WarningStart + 'VLAN "Default"' + \
            ' with tag "1" is not part of any MST instance'
        cls.noticeStackingModeNeeded1 = cls.NoticeStart + 'Creating' + \
            ' configuration for switch / stack in stacking mode'
        cls.noticeStackingModeNeeded2 = cls.NoticeStart + 'Stacking must' + \
            ' be configured before applying this configuration'
        cls.noticeStackingModeNeeded3 = cls.NoticeStart + 'See the' + \
            ' ExtremeXOS Configuration Guide on how to configure stacking'

    def setUp(self):
        self.cw = XOS_write.XosConfigWriter(self.mockSwitch)

        self.vlan = VLAN.VLAN(name='foo_bar', tag=100)
        self.lag = LAG.LAG(1, name='lag1', use_lacp=True, aadminkey=100)
        self.stp = STP.STP()

    def test_port_ok_reason_is_default(self):
        reason = 'default'
        expectedConf = [self.confPortsDisplStr,
                        self.confPortsDescrStr,
                        self.disableJumboStr,
                        self.confAcl42Str]
        expectedErr = []
        expected = (expectedConf, expectedErr)

        self.mockPort.get_auto_neg_reason.return_value = reason
        self.mockPort.get_admin_state_reason.return_value = reason
        self.mockPort.get_ipv4_acl_in.return_value = [42]

        result = self.cw.port()

        self.assertEqual(expected, result)

    def test_port_ok_auto_neg(self):
        reason = 'transfer_conf'
        expectedConf = [self.enablePortsStr,
                        self.confPortsAutoStr + 'on',
                        self.confPortsDisplStr,
                        self.confPortsDescrStr,
                        self.disableJumboStr,
                        self.confAcl42Str]
        expectedErr = []
        expected = (expectedConf, expectedErr)

        self.mockPort.get_auto_neg.return_value = True
        self.mockPort.get_admin_state.return_value = True
        self.mockPort.get_auto_neg_reason.return_value = reason
        self.mockPort.get_jumbo.return_value = False
        self.mockPort.get_ipv4_acl_in.return_value = [42]

        result = self.cw.port()

        self.assertEqual(expected, result)

    def test_port_ok_auto_neg_no_acl(self):
        reason = 'transfer_conf'
        expectedConf = [self.enablePortsStr,
                        self.confPortsAutoStr + 'on',
                        self.confPortsDisplStr,
                        self.confPortsDescrStr,
                        self.disableJumboStr]
        expectedErr = []
        expected = (expectedConf, expectedErr)

        self.mockPort.get_auto_neg.return_value = True
        self.mockPort.get_admin_state.return_value = True
        self.mockPort.get_auto_neg_reason.return_value = reason
        self.mockPort.get_jumbo.return_value = False
        self.mockPort.get_ipv4_acl_in.return_value = []

        result = self.cw.port()

        self.assertEqual(expected, result)

    def test_port_fail_auto_neg_is_false_speed_is_none(self):
        reason = 'transfer_conf'
        expectedConf = [self.enablePortsStr,
                        self.confPortsDisplStr,
                        self.confPortsDescrStr,
                        self.disableJumboStr,
                        self.confAcl42Str]
        expectedErr = ['ERROR: Auto-negotiation of port "' + self.portName +
                       '" disabled, but speed or duplex not defined']
        expected = (expectedConf, expectedErr)

        self.mockPort.get_auto_neg_reason.return_value = reason
        self.mockPort.get_auto_neg.return_value = False
        self.mockPort.get_speed.return_value = None
        self.mockPort.get_admin_state.return_value = True
        self.mockPort.get_description.return_value = ''
        self.mockPort.get_short_description.return_value = ''
        self.mockPort.get_jumbo.return_value = False
        self.mockPort.get_ipv4_acl_in.return_value = [42]

        result = self.cw.port()

        self.assertEqual(expected, result)

    def test_port_ok_admin_state(self):
        reason = 'transfer_def'
        expectedConf = [self.disablePortsStr,
                        self.confPortsAutoStr + 'off speed 100 duplex half',
                        self.confPortsDisplStr,
                        self.confPortsDescrStr,
                        self.enableJumboStr,
                        self.confAcl42Str]
        expectedErr = []
        expected = (expectedConf, expectedErr)

        self.mockPort.get_admin_state_reason.return_value = reason
        self.mockPort.get_admin_state.return_value = False
        self.mockPort.get_speed.return_value = 100
        self.mockPort.get_duplex.return_value = 'half'
        self.mockPort.get_auto_neg.return_value = False
        self.mockPort.get_description_reason.return_value = reason
        self.mockPort.get_description.return_value = ''
        self.mockPort.get_short_description_reason.return_value = reason
        self.mockPort.get_short_description.return_value = ''
        self.mockPort.get_jumbo_reason.return_value = reason
        self.mockPort.get_jumbo.return_value = True
        self.mockPort.get_ipv4_acl_in.return_value = [42]

        result = self.cw.port()

        self.assertEqual(expected, result)

    def test_normalize_default_vlan_vlan_has_no_name(self):
        self.vlan._name = None
        expected = []

        result = self.cw._normalize_default_vlan(self.vlan)

        self.assertEqual(expected, result)

    def test_normalize_default_vlan_vlan_has_a_name_and_it_is_default(self):
        self.vlan._name_is_default = True
        self.vlan._tag = 1
        expected = [self.InfoStart +
                    'Cannot rename VLAN ' + str(self.vlan.get_tag()) +
                    ' from "Default" to "' + self.vlan.get_name() + '"']

        result = self.cw._normalize_default_vlan(self.vlan)

        self.assertEqual(expected, result)

    def test_normalize_default_vlan_vlans_name_is_not_default(self):
        self.vlan._tag = 1
        expected = [self.ErrorStart +
                    'Cannot rename VLAN ' + str(self.vlan.get_tag()) +
                    ' from "Default" to "' + self.vlan.get_name() + '"']

        result = self.cw._normalize_default_vlan(self.vlan)

        self.assertEqual(expected, result)

    def test_normalize_default_vlan_vlan_is_default(self):
        self.mockVlan.get_name.return_value = 'Default'
        expected = []

        result = self.cw._normalize_default_vlan(self.mockVlan)

        self.assertEqual(expected, result)

    def test_normalize_vlan_name_contains_spaces(self):
        name = 'foo bar'
        self.mockVlan.get_name.return_value = name
        expected = [self.NoticeStart +
                    'Replaced " " with "_" in VLAN name "' + name + '"']

        result = self.cw._normalize_vlan(self.mockVlan)

        self.assertEqual(expected, result)
        self.mockVlan.set_name.assert_called_once_with('foo_bar')
        self.mockVlan.reset_mock()

    def test_normalize_vlan_reserved_keyword_name(self):
        self.mockVlan.reset_mock()
        name = 'management'
        self.mockVlan.get_name.return_value = name
        self.mockVlan.get_egress_ports.return_value = []
        expected = [self.NoticeStart +
                    'Replaced VLAN name "' + name + '" with "vl_' + name + '"'
                    ' because "' + name + '" is a reserved keyword in XOS']

        result = self.cw._normalize_vlan(self.mockVlan)

        self.assertEqual(expected, result)
        self.mockVlan.set_name.assert_called_once_with('vl_' + name)
        self.mockVlan.reset_mock()

    def test_normalize_vlan_vlan_has_no_name_and_no_tag(self):
        vlan = VLAN.VLAN()
        expected = [self.ErrorStart + 'VLAN cannot have neither ' +
                    'tag nor name, removing all ports']

        result = self.cw._normalize_vlan(vlan)

        self.assertEqual(expected, result)

    def test_normalize_vlan_name_is_Mgmt(self):
        name = 'Mgmt'
        self.mockVlan.get_name.return_value = name
        expected = [self.ErrorStart +
                    'Cannot use name "Mgmt" for regular VLAN']

        result = self.cw._normalize_vlan(self.mockVlan)

        self.assertEqual(expected, result)
        self.mockVlan.set_name.assert_called_once_with(None)
        self.mockVlan.reset_mock()

    def test_normalize_vlan_no_tag_but_egress_ports(self):
        name = 'foo_bar'
        self.mockVlan.get_name.return_value = name
        self.mockVlan.get_tag.return_value = None
        self.mockVlan.get_egress_ports.return_value = [('1', 'tagged')]
        expectedErr = self.ErrorStart + \
            'VLAN "' + name + '" without tag cannot have tagged egress ports'

        result = self.cw._normalize_vlan(self.mockVlan)

        self.assertIn(expectedErr, result)

    # Note: That cannot be configured in EOS!
    #       Test just documents current behavior.
    def test_normalize_vlan_egress_same_port_tagged_untagged(self):
        self.vlan._egress_ports = [('1', 'untagged'), ('1', 'tagged')]
        self.vlan._ingress_ports = [('1', 'untagged')]

        expectedErr = self.ErrorStart + \
            'Port "1" in tagged egress list of VLAN "' + \
            self.vlan.get_name() + '" but missing from tagged ingress: ' + \
            'adding ingress'
        expectedWarn1 = self.WarningStart + \
            'Port "1" both untagged and tagged in VLAN "' + \
            self.vlan.get_name() + '" (tag ' + str(self.vlan.get_tag()) + ')'
        expectedWarn2 = self.WarningStart + \
            'Removing untagged ingress of "' + self.vlan.get_name() + \
            '" VLAN (tag ' + str(self.vlan.get_tag()) + ') from port "1"'

        result = self.cw._normalize_vlan(self.vlan)

        self.assertIn(expectedErr, result)
        self.assertIn(expectedWarn1, result)
        self.assertIn(expectedWarn2, result)
        # TODO: remove untagged egress as well
        self.assertEqual(2, len(self.vlan._egress_ports))
        self.assertEqual(self.vlan._egress_ports,
                         [('1', 'untagged'), ('1', 'tagged')])
        self.assertEqual(1, len(self.vlan._ingress_ports))
        self.assertEqual(self.vlan._ingress_ports, [('1', 'tagged')])

    # Note: That cannot be configured in EOS!
    #       Test just documents current behavior.
    def test_normalize_vlan_egress_untagged_port_not_in_ingress_untagged(self):
        self.vlan._egress_ports = [('1', 'untagged')]
        self.vlan._ingress_ports = []

        result = self.cw._normalize_vlan(self.vlan)

        self.assertEqual([], result)
        self.assertEqual(1, len(self.vlan._egress_ports))

    def test_normalize_vlan_egress_tagged_port_not_in_ingress_tagged(self):
        self.vlan._egress_ports = [('1', 'tagged')]
        self.vlan._ingress_ports = []

        expectedErr = self.ErrorStart + \
            'Port "1" in tagged egress list of VLAN "' + \
            self.vlan._name + '" but missing from tagged ingress: adding ' + \
            'ingress'

        result = self.cw._normalize_vlan(self.vlan)

        self.assertIn(expectedErr, result)
        self.assertEqual(1, len(self.vlan._egress_ports))

    def test_normalize_vlan_ingress_same_port_tagged_untagged(self):
        self.vlan._ingress_ports = [('1', 'untagged'), ('1', 'tagged')]
        self.vlan._egress_ports = [('1', 'untagged')]

        expectedWarn = self.WarningStart + \
            'Port "1" both untagged and tagged in VLAN "' + \
            self.vlan.get_name() + '" (tag ' + str(self.vlan.get_tag()) + ')'

        result = self.cw._normalize_vlan(self.vlan)

        self.assertIn(expectedWarn, result)
        self.assertEqual(1, len(self.vlan._ingress_ports))

    # Note: That situation can be created in EOS by using 'set port discard',
    #       but that is not yet supported by E2X and highly uncommon.
    #       XOS does not support this AFAIK, so a modified translation seems OK
    def test_normalize_vlan_ingress_untagged_port_not_in_egress_untagged(self):
        self.vlan._ingress_ports = [('1', 'untagged')]
        self.vlan._egress_ports = [('1', 'tagged')]

        expectedErr = self.ErrorStart + \
            'Port "1" in tagged egress list of VLAN "' + \
            self.vlan._name + '" but missing from tagged ingress: adding ' + \
            'ingress'
        expectedWarn1 = self.WarningStart + \
            'Port "1" both untagged and tagged in VLAN "' + \
            self.vlan.get_name() + '" (tag ' + str(self.vlan.get_tag()) + ')'
        expectedWarn2 = self.WarningStart + \
            'Removing untagged ingress of "' + self.vlan.get_name() + \
            '" VLAN (tag ' + str(self.vlan.get_tag()) + ') from port "1"'

        result = self.cw._normalize_vlan(self.vlan)
        self.assertIn(expectedWarn1, result)
        self.assertIn(expectedWarn2, result)

        self.assertIn(expectedErr, result)
        self.assertEqual(1, len(self.vlan._egress_ports))
        self.assertEqual(self.vlan._ingress_ports, [('1', 'tagged')])
        self.assertEqual(1, len(self.vlan._ingress_ports))
        self.assertEqual(self.vlan._egress_ports, [('1', 'tagged')])

    def test_normalize_ok(self):
        self.vlan._egress_ports = [('1', 'untagged'), ('2', 'tagged')]
        self.vlan._ingress_ports = [('1', 'untagged'), ('2', 'tagged')]

        expected = []

        result = self.cw._normalize_vlan(self.vlan)

        self.assertEqual(expected, result)

    def test_handle_default_vlan_single_port_to_conf(self):
        self.vlan.set_name('Default')
        self.cw._switch = self.mockTargetSwitch
        self.mockTargetSwitch.get_ports.return_value = [self.mockTargetPort1,
                                                        self.mockTargetPort2]
        self.vlan._egress_ports = [('1', 'untagged')]
        self.vlan._ingress_ports = [('1', 'untagged')]
        expectedConf = ['configure vlan ' + self.vlan.get_name() +
                        ' delete ports 2']
        expectedErr = []
        expected = (expectedConf, expectedErr)

        result = self.cw._handle_default_vlan(self.vlan)

        self.assertEqual(expected, result)

    def test_handle_default_vlan_contiguous_ports_to_conf(self):
        self.vlan.set_name('Default')
        self.cw._switch = self.mockTargetSwitch
        self.mockTargetSwitch.get_ports.return_value = [self.mockTargetPort1,
                                                        self.mockTargetPort2,
                                                        self.mockTargetPort3]
        self.vlan._egress_ports = [('1', 'untagged')]
        self.vlan._ingress_ports = [('1', 'untagged')]
        expectedConf = ['configure vlan ' + self.vlan.get_name() +
                        ' delete ports 2-3']
        expectedErr = []
        expected = (expectedConf, expectedErr)

        result = self.cw._handle_default_vlan(self.vlan)

        self.assertEqual(expected, result)

    def test_handle_default_vlan_not_contiguous_ports_to_conf(self):
        self.cw._switch = self.mockTargetSwitch
        self.mockTargetSwitch.get_ports.return_value = [self.mockTargetPort1,
                                                        self.mockTargetPort2,
                                                        self.mockTargetPort4]
        self.vlan._egress_ports = [('1', 'untagged')]
        self.vlan._ingress_ports = [('1', 'untagged')]
        expectedConf = ['configure vlan ' + self.vlan.get_name() +
                        ' delete ports 2,4']
        expectedErr = []
        expected = (expectedConf, expectedErr)

        result = self.cw._handle_default_vlan(self.vlan)

        self.assertEqual(expected, result)

    def test_handle_default_vlan_tagged_not_continuous_ports_to_conf(self):
        self.cw._switch = self.mockTargetSwitch
        self.mockTargetSwitch.get_ports.return_value = [self.mockTargetPort1,
                                                        self.mockTargetPort2,
                                                        self.mockTargetPort4]
        self.vlan._egress_ports = [('1', 'tagged'), ('3', 'tagged')]
        self.vlan._ingress_ports = [('1', 'tagged'), ('3', 'tagged')]
        expectedConf = ['configure vlan ' + self.vlan.get_name() +
                        ' delete ports 2,4',
                        'configure vlan ' + self.vlan.get_name() +
                        ' add ports 1,3 tagged']
        expectedErr = []
        expected = (expectedConf, expectedErr)

        result = self.cw._handle_default_vlan(self.vlan)

        self.assertEqual(expected, result)

    def test_handle_additional_vlan_no_name(self):
        self.vlan.set_name(None)

        expectedConf = ['create vlan VLAN_0100 tag ' +
                        str(self.vlan.get_tag())]
        expectedErr = []
        expected = (expectedConf, expectedErr)

        result = self.cw._handle_additional_vlan(self.vlan)

        self.assertEqual(expected, result)

    def test_handle_additional_vlan_no_tag(self):
        self.vlan._tag = None

        expectedConf = ['create vlan ' + self.vlan.get_name()]
        expectedErr = []
        expected = (expectedConf, expectedErr)

        result = self.cw._handle_additional_vlan(self.vlan)

        self.assertEqual(expected, result)

    def test_handle_additional_vlan_egress_tagged_untagged(self):
        self.vlan._egress_ports = [('1', 'tagged'), ('3', 'tagged'),
                                   ('2', 'untagged'), ('4', 'untagged')]

        expectedConf = ['create vlan ' + self.vlan.get_name() +
                        ' tag ' + str(self.vlan.get_tag()),
                        'configure vlan ' + self.vlan.get_name() +
                        ' add ports 2,4 untagged',
                        'configure vlan ' + self.vlan.get_name() +
                        ' add ports 1,3 tagged']
        expectedErr = []
        expected = (expectedConf, expectedErr)

        result = self.cw._handle_additional_vlan(self.vlan)

        self.assertEqual(expected, result)

    def test_vlan_is_default(self):
        self.vlan.set_tag('1')
        self.cw._switch = self.mockTargetSwitch
        self.mockTargetSwitch.get_all_vlans.return_value = [self.vlan]
        self.mockTargetSwitch.get_ports.return_value = [self.mockTargetPort1,
                                                        self.mockTargetPort2,
                                                        self.mockTargetPort4]

        expectedConf = ['configure vlan Default delete ports 1-2,4']
        expectedErr = ['ERROR: Cannot rename VLAN 1 from "Default" to ' +
                       '"foo_bar"']
        expected = (expectedConf, expectedErr)

        result = self.cw.vlan()

        self.assertEqual(expected, result)

    def test_vlan_is_not_default(self):
        self.cw._switch = self.mockTargetSwitch
        self.mockTargetSwitch.get_all_vlans.return_value = [self.vlan]

        expectedConf = ['create vlan foo_bar tag 100']
        expectedErr = []
        expected = (expectedConf, expectedErr)

        result = self.cw.vlan()

        self.assertEqual(expected, result)

    def test_verify_untagged_ports_same_port_in_multiple_vlans(self):
        vlan2 = VLAN.VLAN('baz', '102')
        vlan2EntryStr = str((vlan2.get_name(), vlan2.get_tag()))
        vlanEntryStr = str((self.vlan.get_name(), self.vlan.get_tag()))
        port1Name = self.mockTargetPort1.get_name()
        self.vlan._egress_ports = [('1', 'untagged')]
        vlan2._egress_ports = [('1', 'untagged')]
        self.vlan._ingress_ports = [('1', 'untagged')]
        vlan2._ingress_ports = [('1', 'untagged')]
        self.mockSwitch.get_all_vlans.return_value = [self.vlan, vlan2]
        self.mockSwitch.get_ports.return_value = [self.mockTargetPort1,
                                                  self.mockTargetPort2,
                                                  self.mockTargetPort3]
        errStr = self.ErrorStart + \
            'Port "{}" has multiple untagged {} VLANs: {} {}'
        expected = [errStr.format(port1Name,
                                  'egress',
                                  vlanEntryStr,
                                  vlan2EntryStr),
                    errStr.format(port1Name,
                                  'ingress',
                                  vlanEntryStr,
                                  vlan2EntryStr)]

        result = self.cw._verify_untagged_ports()

        self.assertEqual(expected, result)

    def test_verify_untagged_ports_ingress_egress_differ(self):
        vlan2 = VLAN.VLAN('baz', '102')
        vlan2EntryStr = str((vlan2.get_name(), vlan2.get_tag()))
        vlanEntryStr = str((self.vlan.get_name(), self.vlan.get_tag()))
        port1Name = self.mockTargetPort1.get_name()
        port2Name = self.mockTargetPort2.get_name()
        self.vlan._egress_ports = [('1', 'untagged')]
        vlan2._egress_ports = [('1', 'untagged')]
        self.vlan._ingress_ports = [('2', 'untagged')]
        vlan2._ingress_ports = [('2', 'untagged')]
        self.mockSwitch.get_all_vlans.return_value = [self.vlan, vlan2]
        self.mockSwitch.get_ports.return_value = [self.mockTargetPort1,
                                                  self.mockTargetPort2,
                                                  self.mockTargetPort3]
        errStr = self.ErrorStart + \
            'Port "{}" has multiple untagged {} VLANs: {} {}'
        errStrListsDiffer = self.ErrorStart + \
            'Untagged VLAN egress and ingress differs for port "{}"'
        expected = [errStr.format(port1Name,
                                  'egress',
                                  vlanEntryStr,
                                  vlan2EntryStr),
                    errStr.format(port2Name,
                                  'ingress',
                                  vlanEntryStr,
                                  vlan2EntryStr),
                    errStrListsDiffer.format(port1Name),
                    errStrListsDiffer.format(port2Name)
                    ]

        result = self.cw._verify_untagged_ports()

        self.maxDiff = None
        self.assertEqual(expected, result)

    def test_populate_lag_member_ports_lacp_enabled_on_port_and_lag(self):
        self.mockPort.reset_mock()
        aadminKey = self.lag.get_lacp_aadminkey()
        self.mockSwitch.get_lags.return_value = [self.lag]
        self.mockPort.get_lacp_aadminkey.return_value = aadminKey
        self.mockPort.get_lacp_enabled.return_value = True
        exp = []

        result = self.cw._populate_lag_member_ports()

        self.assertEqual(exp, result)
        self.mockPort.set_lacp_aadminkey.assert_called_once_with(aadminKey,
                                                                 'written')
        self.mockPort.set_lacp_enabled.assert_called_once_with(True, 'written')
        self.assertEqual(1, len(self.lag._members))

    def test_populate_lag_member_ports_lacp_disabled_on_port_and_lag(self):
        self.mockPort.reset_mock()
        aadminKey = self.lag.get_lacp_aadminkey()
        self.lag.set_lacp_enabled(False, 'test')
        self.mockSwitch.get_lags.return_value = [self.lag]
        self.mockPort.get_lacp_aadminkey.return_value = aadminKey
        self.mockPort.get_lacp_enabled.return_value = False
        exp = []

        result = self.cw._populate_lag_member_ports()

        self.assertEqual(exp, result)
        self.mockPort.set_lacp_aadminkey.assert_called_once_with(aadminKey,
                                                                 'written')
        self.mockPort.set_lacp_enabled.assert_called_once_with(False,
                                                               'written')

    def test_populate_lag_member_ports_lacp_enabled_only_on_port(self):
        self.mockPort.reset_mock()
        aadminKey = self.lag.get_lacp_aadminkey()
        self.lag.set_lacp_enabled(False, 'test')
        self.mockSwitch.get_lags.return_value = [self.lag]
        self.mockPort.get_lacp_aadminkey.return_value = aadminKey
        self.mockPort.get_lacp_enabled.return_value = True
        exp = [self.ErrorStart + 'LAG "' + self.lagName + '" configured ' +
               'with LACP disabled, but member port "' + self.portName +
               '" has LACP enabled']

        result = self.cw._populate_lag_member_ports()

        self.assertEqual(exp, result)
        self.mockPort.set_lacp_aadminkey.assert_called_once_with(aadminKey,
                                                                 'written')
        self.mockPort.reset_mock()

    def test_populate_lag_member_ports_lacp_aadminkeys_differ(self):
        aadminKey = 100
        self.mockSwitch.get_lags.return_value = [self.mockLag]
        self.mockLag.get_lacp_aadminkey.return_value = aadminKey
        self.mockLag.get_members.return_value = None
#        self.mockLag.get_lacp_enabled.return_value = False
        self.mockPort.get_lacp_aadminkey.return_value = aadminKey + 1
#        self.mockPort.get_lacp_enabled.return_value = True
        exp = [self.WarningStart + 'LAG with key "' + str(aadminKey) +
               '" configured, but no ports associated']

        result = self.cw._populate_lag_member_ports()

        self.assertEqual(exp, result)

    def test_get_all_non_master_lag_ports_only_one_port_in_lag(self):
        self.mockSwitch.get_lags.return_value = [self.mockLag]

        result = self.cw._get_all_non_master_lag_ports()

        self.assertEqual([], result)

    def test_get_all_non_master_lag_ports_two_ports_in_lag(self):
        nonMasterPortName = 'ge.1.2'
        self.mockSwitch.get_lags.return_value = [self.lag]
        self.lag.add_member_port(self.portName)
        self.lag.add_member_port(nonMasterPortName)

        result = self.cw._get_all_non_master_lag_ports()

        self.assertEqual([nonMasterPortName], result)

    def _create_tmp_switch(self):
        tmpSwitch = Switch.Switch()
        tmpSwitch.set_single_port_lag(True, 'test')
        tmpSwitch.set_max_lag(2, 'test')
        tmpSwitch.set_lacp_support(True, 'test')
        return tmpSwitch

    def test_lag_fail_single_port_lag(self):
        self.cw._switch = self._create_tmp_switch()
        self.cw._switch.set_single_port_lag(False, 'transfer_conf')
        expErrList = [self.ErrorStart + 'XOS always allows single port LAGs']
        expConfLst = []
        exp = (expConfLst, expErrList)

        result = self.cw.lag()

        self.assertEqual(exp, result)

    def test_lag_notice_single_port_lag(self):
        self.cw._switch = self._create_tmp_switch()
        self.cw._switch.set_single_port_lag(False, 'test')
        self.cw._switch._applied_defaults = True
        expErrList = [self.NoticeStart + 'XOS always allows single port LAGs']
        expConfLst = []
        exp = (expConfLst, expErrList)

        result = self.cw.lag()

        self.assertEqual(exp, result)

    def test_lag_notice_single_port_lag_suppressed(self):
        self.cw._switch = self._create_tmp_switch()
        self.cw._switch.set_single_port_lag(False, 'test')
        expErrList = []
        expConfLst = []
        exp = (expConfLst, expErrList)

        result = self.cw.lag()

        self.assertEqual(exp, result)

    def test_lag_warn_max_lag_reason(self):
        self.cw._switch = self._create_tmp_switch()
        self.cw._switch.set_max_lag(2, 'transfer_conf')
        expErrList = [self.WarningStart +
                      'Maximum number of LAGs cannot be configured on XOS']
        expConfLst = []
        exp = (expConfLst, expErrList)

        result = self.cw.lag()

        self.assertEqual(exp, result)

    def test_lag_warn_lacp_support_reason(self):
        self.cw._switch = self._create_tmp_switch()
        self.cw._switch.set_lacp_support(True, 'transfer_conf')
        expErrList = [self.ErrorStart +
                      'LACP cannot be enabled/disabled globally on XOS']
        expConfLst = []
        exp = (expConfLst, expErrList)

        result = self.cw.lag()

        self.assertEqual(exp, result)

    def test_lag_master_port_undefined(self):
        self.cw._switch = self._create_tmp_switch()
        self.cw._switch.add_lag(self.mockLag)
        self.mockLag.get_master_port.return_value = None
        expErrList = []
        expConfLst = []
        exp = (expConfLst, expErrList)

        result = self.cw.lag()

        self.assertEqual(exp, result)

    def test_lag_master_one_member_port_single_port_lag_true(self):
        self.cw._switch = self.mockSwitch
        self.mockSwitch.get_ports.return_value = [self.mockPort]
        self.mockSwitch.get_lags.return_value = [self.lag]
        self.mockSwitch.get_single_port_lag.return_value = True
        self.mockPort.get_lacp_aadminkey.return_value = \
            self.lag.get_lacp_aadminkey()
        self.mockPort.get_lacp_enabled.return_value = True
        expErrList = []
        expConfLst = ['enable sharing ' + self.portName + ' grouping ' +
                      self.portName + ' algorithm address-based L3 lacp']
        exp = (expConfLst, expErrList)

        result = self.cw.lag()

        self.assertEqual(exp, result)

    def test_lag_master_one_member_port_single_port_lag_false(self):
        self.cw._switch = self.mockSwitch
        self.mockSwitch.get_ports.return_value = [self.mockPort]
        self.mockSwitch.get_lags.return_value = [self.lag]
        self.mockSwitch.get_single_port_lag.return_value = False
        self.mockPort.get_lacp_aadminkey.return_value = \
            self.lag.get_lacp_aadminkey()
        self.mockPort.get_lacp_enabled.return_value = True
        expErrList = [self.NoticeStart + 'XOS always allows single port LAGs',
                      self.ErrorStart + 'LAG consisting of one port ("' +
                      self.portName + '") only, but single port LAG not' +
                      ' enabled on source switch']
        expConfLst = ['enable sharing ' + self.portName + ' grouping ' +
                      self.portName + ' algorithm address-based L3 lacp']
        exp = (expConfLst, expErrList)

        result = self.cw.lag()

        self.assertEqual(exp, result)

    def test_get_stp_processes_for_port(self):
        self.mockSwitch.get_all_vlans.return_value = [self.vlan]
        self.vlan.add_egress_port(self.portName)
        self.mockSwitch.get_stps.return_value = [self.stp]
        self.stp.set_version('mstp', 'test')
        self.stp.add_vlan(self.vlan.get_tag(), 'test')
        self.stp.set_name(self.stpName, 'test')
        self.mockSwitch.get_stp_by_mst_instance.return_value = self.mockStp
        expected = [self.stpName]

        result = self.cw._get_stp_processes_for_port(self.portName)

        self.assertEqual(expected, result)

    def test_stp_fail_stp_list_empty(self):
        self.cw._switch = self.mockSwitch
        self.mockSwitch.get_stps.return_value = []
        expErr = self.WarningStart + 'Cannot delete STP process "s0", ' + \
            'but it is disabled by default'
        expConf = []
        expected = (expConf, [expErr])

        result = self.cw.stp()

        self.assertEqual(expected, result)

    def test_stp_name_s0_enabled_basic_cfg_vers_stp_rstp_mstp_no_prio(self):
        self.cw._switch = self.mockSwitch
        self.mockSwitch.get_stps.return_value = [self.stp]
        self.mockSwitch.get_all_vlans.return_value = [self.vlan]
        self.stp.set_name('s0', 'test')
        self.stp.set_enabled(True, 'test')
        self.stp.set_version('mstp', 'test')
        self.stp.is_basic_stp_config = MagicMock(return_value=True)

        expErrLst = [self.InfoStart + 'Creating XOS equivalent of EOS ' +
                     'default MSTP respectively RSTP configuration']
        expConf = ['configure stpd s0 delete vlan Default ports all',
                   'disable stpd s0 auto-bind vlan Default',
                   'configure stpd s0 mode mstp cist',
                   'create stpd s1',
                   'configure stpd s1 mode mstp msti 1',
                   'enable stpd s1 auto-bind vlan foo_bar',
                   'enable stpd s0',
                   'enable stpd s1']

        expected = (expConf, expErrLst)

        result = self.cw.stp()

        self.assertEqual(expected, result)

    def test_stp_name_s0_enabled_basic_cfg_vers_stp_rstp_mstp_prio_trans(self):
        self.cw._switch = self.mockSwitch
        self.mockSwitch.get_stps.return_value = [self.stp]
        self.mockSwitch.get_all_vlans.return_value = [self.vlan]
        self.stp.set_name('s0', 'test')
        self.stp.set_enabled(True, 'test')
        self.stp.set_version('mstp', 'test')
        self.stp.set_priority(100, 'transfer_conf')
        self.stp.is_basic_stp_config = MagicMock(return_value=True)

        expErrLst = [self.InfoStart + 'Creating XOS equivalent of EOS ' +
                     'default MSTP respectively RSTP configuration']
        expConf = ['configure stpd s0 delete vlan Default ports all',
                   'disable stpd s0 auto-bind vlan Default',
                   'configure stpd s0 mode mstp cist',
                   'create stpd s1',
                   'configure stpd s1 mode mstp msti 1',
                   'enable stpd s1 auto-bind vlan foo_bar',
                   'configure stpd s0 priority 100',
                   'enable stpd s0',
                   'enable stpd s1']

        expected = (expConf, expErrLst)

        result = self.cw.stp()

        self.assertEqual(expected, result)

    def test_stp_name_s0_enabled_not_basic_cfg(self):
        self.cw._switch = self.mockSwitch
        self.mockSwitch.get_stps.return_value = [self.stp]
        self.stp.set_name('s0', 'test')
        self.stp.set_enabled(True, 'test')
        self.stp.set_version('mstp', 'test')
        self.stp.is_basic_stp_config = MagicMock(return_value=False)

        expErrLst = [self.errXosNeedsOneInstance,
                     self.errNoVlansAssoc,
                     self.warnDefVlanNotInInstance]

        expConf = []

        expected = (expConf, expErrLst)

        result = self.cw.stp()

        self.assertEqual(expected, result)

    def test_stp_name_s0_disabled(self):
        self.cw._switch = self.mockSwitch
        self.mockSwitch.get_stps.return_value = [self.stp]
        self.stp.set_name('s0', 'test')
        self.stp.set_enabled(False, 'test')
        self.stp.is_basic_stp_config = MagicMock(return_value=False)

        expErrLst = []
        expConf = []

        expected = (expConf, expErrLst)

        result = self.cw.stp()

        self.assertEqual(expected, result)

    def test_stp_name_not_set_vers_not_set_no_instance(self):
        self.cw._switch = self.mockSwitch
        self.mockSwitch.get_stps.return_value = [self.stp]
        self.stp.set_enabled(True, 'test')

        expErr = self.ErrorStart + 'XOS STP processes need a name'
        expErrLst = [expErr,
                     self.errXosNeedsOneInstance,
                     self.errNoVlansAssoc,
                     self.warnDefVlanNotInInstance]

        expConf = []
        expected = (expConf, expErrLst)

        result = self.cw.stp()

        self.assertEqual(expected, result)

    def test_stp_name_not_set_vers_mstp_no_instance(self):
        self.cw._switch = self.mockSwitch
        self.mockSwitch.get_stps.return_value = [self.stp]
        self.stp.set_version('mstp', 'test')
        expErr = self.ErrorStart + 'XOS STP processes need a name'
        expErrLst = [expErr,
                     self.errXosNeedsOneInstance,
                     self.errNoVlansAssoc,
                     self.warnDefVlanNotInInstance]

        expConf = []
        expected = (expConf, expErrLst)

        result = self.cw.stp()

        self.assertEqual(expected, result)

    def test_stp_name_not_set_vers_mstp_instance_set(self):
        mst_instance = 1
        self.cw._switch = self.mockSwitch
        self.mockSwitch.get_stps.return_value = [self.stp]
        self.stp.set_version('mstp', 'test')
        self.stp.set_mst_instance(mst_instance, 'test')
        expInfoStr = self.InfoStart + 'Generated name "s1" for ' + \
            'MST instance ' + str(mst_instance)
        expErrLst = [expInfoStr,
                     self.errXosNeedsOneInstance,
                     self.errNoVlansAssoc,
                     self.warnDefVlanNotInInstance]
        expConfLst = ['create stpd s1',
                      'configure stpd s1 default-encapsulation dot1d']
        expected = (expConfLst, expErrLst)

        result = self.cw.stp()

        self.assertEqual(expected, result)

    def test_stp_name_s1(self):
        self.cw._switch = self.mockSwitch
        self.mockSwitch.get_stps.return_value = [self.stp]
        self.stp.set_name('s1', 'test')
        expErrLst = [self.errXosNeedsOneInstance,
                     self.errNoVlansAssoc,
                     self.warnDefVlanNotInInstance]
        expConfLst = ['create stpd s1',
                      'configure stpd s1 default-encapsulation dot1d']
        expected = (expConfLst, expErrLst)

        result = self.cw.stp()

        self.assertEqual(expected, result)

    def test_stp_name_s1_vers_reas_transf_vers_none(self):
        self.cw._switch = self.mockSwitch
        self.mockSwitch.get_stps.return_value = [self.stp]
        self.stp.set_name('s1', 'test')
        self.stp.set_version(None, 'transfer_def')
        expErrLst = [self.ErrorStart + 'STP version must be specified, ' +
                     'but missing from STP process "s1"']
        expErrLst += [self.errXosNeedsOneInstance,
                      self.errNoVlansAssoc,
                      self.warnDefVlanNotInInstance]
        expConfLst = ['create stpd s1',
                      'configure stpd s1 default-encapsulation dot1d']
        expected = (expConfLst, expErrLst)

        result = self.cw.stp()

        self.assertEqual(expected, result)

    def test_stp_name_s1_vers_reas_transf_vers_stp(self):
        self.cw._switch = self.mockSwitch
        self.mockSwitch.get_stps.return_value = [self.stp]
        self.stp.set_name('s1', 'test')
        self.stp.set_version('stp', 'transfer_def')
        expErrLst = [self.errXosNeedsOneInstance,
                     self.errNoVlansAssoc,
                     self.warnDefVlanNotInInstance]
        expConfLst = ['create stpd s1',
                      'configure stpd s1 default-encapsulation dot1d',
                      'configure stpd s1 mode dot1d']
        expected = (expConfLst, expErrLst)

        result = self.cw.stp()

        self.assertEqual(expected, result)

    def test_stp_name_s0_enabled_not_basic_cfg_vers_reas_transf_vers_stp(self):
        self.cw._switch = self.mockSwitch
        self.mockSwitch.get_stps.return_value = [self.stp]
        self.stp.set_name('s0', 'test')
        self.stp.set_version('stp', 'transfer_def')
        self.stp.set_enabled(True, 'test')
        self.stp.is_basic_stp_config = MagicMock(return_value=False)
        expErrLst = [self.errXosNeedsOneInstance,
                     self.errNoVlansAssoc,
                     self.warnDefVlanNotInInstance]
        expConfLst = []
        expected = (expConfLst, expErrLst)

        result = self.cw.stp()

        self.assertEqual(expected, result)

    def test_stp_name_s1_vers_reas_transf_vers_rstp(self):
        self.cw._switch = self.mockSwitch
        self.mockSwitch.get_stps.return_value = [self.stp]
        self.stp.set_name('s1', 'test')
        self.stp.set_version('rstp', 'transfer_def')
        expErrLst = [self.errXosNeedsOneInstance,
                     self.errNoVlansAssoc,
                     self.warnDefVlanNotInInstance]
        expConfLst = ['create stpd s1',
                      'configure stpd s1 default-encapsulation dot1d',
                      'configure stpd s1 mode dot1w']
        expected = (expConfLst, expErrLst)

        result = self.cw.stp()

        self.assertEqual(expected, result)

    def test_stp_name_s1_vers_reas_transf_vers_mstp_sid_ne_0(self):
        self.cw._switch = self.mockSwitch
        self.mockSwitch.get_stps.return_value = [self.stp]
        self.stp.set_name('s1', 'test')
        self.stp.set_version('mstp', 'transfer_def')
        self.stp.set_mst_instance(1, 'test')
        expErrLst = [self.errXosNeedsOneInstance,
                     self.errNoVlansAssoc,
                     self.warnDefVlanNotInInstance]
        expConfLst = ['create stpd s1',
                      'configure stpd s1 default-encapsulation dot1d',
                      'configure stpd s1 mode mstp msti 1']
        expected = (expConfLst, expErrLst)

        result = self.cw.stp()

        self.assertEqual(expected, result)

    def test_stp_name_s1_vers_reas_transf_vers_mstp_sid_eq_0(self):
        self.cw._switch = self.mockSwitch
        self.mockSwitch.get_stps.return_value = [self.stp]
        self.stp.set_name('s1', 'test')
        self.stp.set_version('mstp', 'transfer_def')
        self.stp.set_mst_instance(0, 'test')
        errStr = self.ErrorStart + 'E2X expects "s0" as CIST'
        expErrLst = [errStr,
                     self.errXosNeedsOneInstance,
                     self.errNoVlansAssoc,
                     self.warnDefVlanNotInInstance]
        expConfLst = ['create stpd s1',
                      'configure stpd s1 default-encapsulation dot1d',
                      ]
        expected = (expConfLst, expErrLst)

        result = self.cw.stp()

        self.assertEqual(expected, result)

    def test_stp_name_s1_vers_reas_transf_vers_foo(self):
        self.cw._switch = self.mockSwitch
        self.mockSwitch.get_stps.return_value = [self.stp]
        self.stp.set_name('s1', 'test')
        self.stp.set_version('foo', 'transfer_def')
        errStr = self.ErrorStart + 'STP process "s1" has unsupported ' + \
            'version "foo"'
        expErrLst = [errStr,
                     self.errXosNeedsOneInstance,
                     self.errNoVlansAssoc,
                     self.warnDefVlanNotInInstance]
        expConfLst = ['create stpd s1',
                      'configure stpd s1 default-encapsulation dot1d']
        expected = (expConfLst, expErrLst)

        result = self.cw.stp()

        self.assertEqual(expected, result)

    def test_stp_name_s1_vers_reas_transf_vers_mstp_vtags_match(self):
        self.cw._switch = self.mockSwitch
        self.mockSwitch.get_stps.return_value = [self.stp]
        self.mockSwitch.get_all_vlans.return_value = [self.vlan]
        self.stp.set_name('s1', 'test')
        self.stp.add_vlan(self.vlan.get_tag(), 'test')
        self.stp.set_version('mstp', 'transfer_def')
        self.stp.set_mst_instance(1, 'test')
        expErrLst = [self.errXosNeedsOneInstance,
                     self.warnDefVlanNotInInstance]
        expConfLst = ['create stpd s1',
                      'configure stpd s1 default-encapsulation dot1d',
                      'configure stpd s1 mode mstp msti 1',
                      'enable stpd s1 auto-bind vlan foo_bar']
        expected = (expConfLst, expErrLst)

        result = self.cw.stp()

        self.assertEqual(expected, result)

    def test_stp_name_s1_vers_reas_transf_vers_mstp_vtags_mtch_are_1(self):
        self.cw._switch = self.mockSwitch
        self.mockSwitch.get_stps.return_value = [self.stp]
        self.mockSwitch.get_all_vlans.return_value = [self.vlan]
        self.vlan.set_tag(1)
        self.stp.set_name('s1', 'test')
        self.stp.add_vlan(self.vlan.get_tag(), 'test')
        self.stp.set_version('mstp', 'transfer_def')
        self.stp.set_mst_instance(1, 'test')
        expErrLst = [self.errXosNeedsOneInstance]
        expConfLst = ['create stpd s1',
                      'configure stpd s1 default-encapsulation dot1d',
                      'configure stpd s1 mode mstp msti 1',
                      'enable stpd s1 auto-bind vlan foo_bar']
        expected = (expConfLst, expErrLst)

        result = self.cw.stp()

        self.assertEqual(expected, result)

    def test_stp_name_s0_vers_reas_transf_vers_mstp(self):
        self.cw._switch = self.mockSwitch
        self.mockSwitch.get_stps.return_value = [self.stp]
        self.stp.set_name('s0', 'test')
        self.stp.set_version('mstp', 'transfer_def')
        self.stp.set_enabled(True, 'transfer_def')
        expErrLst = [self.errXosNeedsOneInstance,
                     self.errNoVlansAssoc,
                     self.warnDefVlanNotInInstance]
        expConfLst = ['configure stpd s0 delete vlan Default ports all',
                      'disable stpd s0 auto-bind vlan Default',
                      'configure stpd s0 mode mstp cist',
                      'enable stpd s0']
        expected = (expConfLst, expErrLst)

        result = self.cw.stp()

        self.assertEqual(expected, result)

    def test_stp_name_s0_vers_reas_transf_vers_mstp_reas_cfgn_transf(self):
        self.cw._switch = self.mockSwitch
        self.mockSwitch.get_stps.return_value = [self.stp]
        self.stp.set_name('s0', 'test')
        self.stp.set_version('mstp', 'transfer_def')
        self.stp.set_mst_cfgname('foo', 'transfer_def')
        self.stp.set_enabled(True, 'transfer_def')
        expErrLst = [self.errXosNeedsOneInstance,
                     self.errNoVlansAssoc,
                     self.warnDefVlanNotInInstance]
        expConfLst = ['configure mstp region foo',
                      'configure stpd s0 delete vlan Default ports all',
                      'disable stpd s0 auto-bind vlan Default',
                      'configure stpd s0 mode mstp cist',
                      'enable stpd s0']
        expected = (expConfLst, expErrLst)

        result = self.cw.stp()

        self.assertEqual(expected, result)

    def test_stp_name_s0_vers_reas_transf_vers_mstp_reas_rev_transf(self):
        self.cw._switch = self.mockSwitch
        self.mockSwitch.get_stps.return_value = [self.stp]
        self.stp.set_name('s0', 'test')
        self.stp.set_version('mstp', 'transfer_def')
        self.stp.set_mst_rev(1, 'transfer_def')
        self.stp.set_enabled(True, 'transfer_def')
        expErrLst = [self.errXosNeedsOneInstance,
                     self.errNoVlansAssoc,
                     self.warnDefVlanNotInInstance]
        expConfLst = ['configure mstp revision 1',
                      'configure stpd s0 delete vlan Default ports all',
                      'disable stpd s0 auto-bind vlan Default',
                      'configure stpd s0 mode mstp cist',
                      'enable stpd s0']
        expected = (expConfLst, expErrLst)

        result = self.cw.stp()

        self.assertEqual(expected, result)

    def test_stp_name_s1_prio_reas_transf(self):
        self.cw._switch = self.mockSwitch
        self.mockSwitch.get_stps.return_value = [self.stp]
        self.stp.set_name('s1', 'test')
        self.stp.set_priority(1, 'transfer_def')
#        self.stp.set_enabled(False, 'transfer_def')
        expErrLst = [self.errXosNeedsOneInstance,
                     self.errNoVlansAssoc,
                     self.warnDefVlanNotInInstance]
        expConfLst = ['create stpd s1',
                      'configure stpd s1 default-encapsulation dot1d',
                      'configure stpd s1 priority 1']
        expected = (expConfLst, expErrLst)

        result = self.cw.stp()

        self.assertEqual(expected, result)

    def test_stp_name_s1_prio_reas_transf_prio_default(self):
        self.cw._switch = self.mockSwitch
        self.mockSwitch.get_stps.return_value = [self.stp]
        self.stp.set_name('s1', 'test')
        self.stp.set_priority(32768, 'transfer_def')
#        self.stp.set_enabled(False, 'transfer_def')
        expErrLst = [self.errXosNeedsOneInstance,
                     self.errNoVlansAssoc,
                     self.warnDefVlanNotInInstance]
        expConfLst = ['create stpd s1',
                      'configure stpd s1 default-encapsulation dot1d']
        expected = (expConfLst, expErrLst)

        result = self.cw.stp()

        self.assertEqual(expected, result)

    def test_stp_name_s1_enable_reas_transf_enable(self):
        self.cw._switch = self.mockSwitch
        self.mockSwitch.get_stps.return_value = [self.stp]
        self.stp.set_name('s1', 'test')
        self.stp.set_enabled(True, 'transfer_def')
#        self.stp.set_enabled(False, 'transfer_def')
        expErrLst = [self.errXosNeedsOneInstance,
                     self.errNoVlansAssoc,
                     self.warnDefVlanNotInInstance]
        expConfLst = ['create stpd s1',
                      'configure stpd s1 default-encapsulation dot1d',
                      'enable stpd s1']
        expected = (expConfLst, expErrLst)

        result = self.cw.stp()

        self.assertEqual(expected, result)

    def test_stp_name_s1_enable_reas_transf_disable(self):
        self.cw._switch = self.mockSwitch
        self.mockSwitch.get_stps.return_value = [self.stp]
        self.stp.set_name('s1', 'test')
        self.stp.set_enabled(False, 'transfer_def')
#        self.stp.set_enabled(False, 'transfer_def')
        expErrLst = [self.errXosNeedsOneInstance,
                     self.errNoVlansAssoc,
                     self.warnDefVlanNotInInstance]
        expConfLst = ['create stpd s1',
                      'configure stpd s1 default-encapsulation dot1d',
                      'disable stpd s1']
        expected = (expConfLst, expErrLst)

        result = self.cw.stp()

        self.assertEqual(expected, result)

    def _createMockPort(self, stp_enabled=False):
        reason = 'transfer_def'
        port = MagicMock(spec=Port.Port)
        port.get_name.return_value = 'ge.1.1'
        port.get_stp_enabled.return_value = stp_enabled
        port.get_stp_enabled_reason.return_value = reason
        self.mockSwitch.get_logical_ports.return_value = [port]
        return port

    def test_stp_port_stp_disabled(self):
        self.cw._switch = self.mockSwitch
        self.mockSwitch.get_stps.return_value = [self.stp]
        self.stp.set_name('s0', 'test')
        self.stp.disable('test')
        self.cw._get_stp_processes_for_port = \
            MagicMock(return_value=[self.stp.get_name()])
        self._createMockPort()
        expErrLst = []
        expConfLst = ['disable stpd s0 ports ' + self.portName]
        expected = (expConfLst, expErrLst)

        result = self.cw.stp()

        self.assertEqual(expected, result)

    def test_stp_port_stp_enabled_edge_false_auto_false(self):
        self.cw._switch = self.mockSwitch
        self.mockSwitch.get_stps.return_value = [self.stp]
        self.stp.set_name('s0', 'test')
        self.stp.disable('test')
        self.cw._get_stp_processes_for_port = \
            MagicMock(return_value=[self.stp.get_name()])
        port = self._createMockPort(True)
        port.get_stp_edge.return_value = False
        port.get_stp_auto_edge.return_value = False
        expErrLst = []
        expConfLst = []
        expected = (expConfLst, expErrLst)

        result = self.cw.stp()

        self.assertEqual(expected, result)

    def test_stp_port_stp_enabled_edge_false_auto_true(self):
        self.cw._switch = self.mockSwitch
        self.mockSwitch.get_stps.return_value = [self.stp]
        self.stp.set_name('s0', 'test')
        self.stp.disable('test')
        self.cw._get_stp_processes_for_port = \
            MagicMock(return_value=[self.stp.get_name()])
        port = self._createMockPort(True)
        port.get_stp_edge.return_value = False
        port.get_stp_auto_edge.return_value = True
        expErrLst = [self.InfoStart + 'XOS does not support automatic ' +
                     'RSTP/MSTP edge port detection']
        expConfLst = []
        expected = (expConfLst, expErrLst)

        result = self.cw.stp()

        self.assertEqual(expected, result)

    def test_stp_port_stp_enabled_edge_false_auto_true_reas_transf_conf(self):
        self.cw._switch = self.mockSwitch
        self.mockSwitch.get_stps.return_value = [self.stp]
        self.stp.set_name('s0', 'test')
        self.stp.disable('test')
        self.cw._get_stp_processes_for_port = \
            MagicMock(return_value=[self.stp.get_name()])
        port = self._createMockPort(True)
        port.get_stp_edge.return_value = False
        port.get_stp_auto_edge.return_value = True
        port.get_stp_auto_edge_reason.return_value = 'transfer_conf'
        expErrLst = [self.WarningStart + 'XOS does not support automatic ' +
                     'edge port detection']
        expConfLst = []
        expected = (expConfLst, expErrLst)

        result = self.cw.stp()

        self.assertEqual(expected, result)

    def test_stp_port_stp_enabled_edge_true_no_bpdu_grd(self):
        self.cw._switch = self.mockSwitch
        self.mockSwitch.get_stps.return_value = [self.stp]
        self.stp.set_name('s0', 'test')
        self.stp.disable('test')
        self.cw._get_stp_processes_for_port = \
            MagicMock(return_value=[self.stp.get_name()])
        port = self._createMockPort(True)
        port.get_stp_edge.return_value = True
        port.get_stp_bpdu_guard.return_value = False
        expErrLst = [self.WarningStart + 'XOS does not send BPDUs on ' +
                     'RSTP/MSTP edge ports without edge-safeguard']
        expConfLst = ['configure stpd s0 ports link-type edge ' +
                      self.portName]
        expected = (expConfLst, expErrLst)

        result = self.cw.stp()

        self.assertEqual(expected, result)

    def test_stp_port_stp_enabled_edge_bpdu_grd_recov_none(self):
        self.cw._switch = self.mockSwitch
        self.mockSwitch.get_stps.return_value = [self.stp]
        self.stp.set_name('s0', 'test')
        self.stp.disable('test')
        self.cw._get_stp_processes_for_port = \
            MagicMock(return_value=[self.stp.get_name()])
        port = self._createMockPort(True)
        port.get_stp_edge.return_value = True
        port.get_stp_bpdu_guard.return_value = True
        port.get_stp_bpdu_guard_recovery_time.return_value = None
        expErrLst = []
        expConfLst = ['configure stpd s0 ports link-type edge ' +
                      self.portName + ' edge-safeguard enable']
        expected = (expConfLst, expErrLst)

        result = self.cw.stp()

        self.assertEqual(expected, result)

    def test_stp_port_stp_enabled_edge_bpdu_grd_recov_set_reas_transf(self):
        recov_timeout = 100
        self.cw._switch = self.mockSwitch
        self.mockSwitch.get_stps.return_value = [self.stp]
        self.stp.set_name('s0', 'test')
        self.stp.disable('test')
        self.cw._get_stp_processes_for_port = \
            MagicMock(return_value=[self.stp.get_name()])
        port = self._createMockPort(True)
        port.get_stp_edge.return_value = True
        port.get_stp_bpdu_guard.return_value = True
        port.get_stp_bpdu_guard_recovery_time.return_value = recov_timeout
        port.get_stp_bpdu_guard_recovery_time_reason.return_value = 'transfer'

        expErrLst = []
        expConfLst = ['configure stpd s0 ports link-type edge ' +
                      self.portName + ' edge-safeguard enable' +
                      ' recovery-timeout ' + str(recov_timeout)]
        expected = (expConfLst, expErrLst)

        result = self.cw.stp()

        self.assertEqual(expected, result)

    def test_acl_aclHasNeitherNameNorNumber(self):
        self.cw._switch = Switch.Switch()
        self.cw._switch.add_complete_acl(ACL())
        expErrorLst = []
        expConfList = [['acl_nr1']]
        expected = (expConfList, expErrorLst)

        result = self.cw.acl()

        self.assertEqual(expected, result)

    def test_acl_aclHasName(self):
        self.cw._switch = Switch.Switch()
        self.cw._switch.add_complete_acl(ACL(name='foo'))
        expErrorLst = []
        expConfList = [['acl_foo']]
        expected = (expConfList, expErrorLst)

        result = self.cw.acl()

        self.assertEqual(expected, result)

    def test_acl_aclHasNumber(self):
        self.cw._switch = Switch.Switch()
        self.cw._switch.add_complete_acl(ACL(number='100'))
        expErrorLst = []
        expConfList = [['acl_100']]
        expected = (expConfList, expErrorLst)

        result = self.cw.acl()

        self.assertEqual(expected, result)

    def test_acl_aceHasNoNumber(self):
        self.cw._switch = XOS.XosSwitch()
        acl = ACL(number='100')
        ace = ACE()
        acl.add_ace(ace)
        self.cw._switch.add_complete_acl(acl)
        expErrorLst = []

        confList, errList = self.cw.acl()

        self.assertEqual(expErrorLst, errList)
        self.assertIn('entry 10', confList[0][1])

    def test_acl_aceHasNumber(self):
        self.cw._switch = XOS.XosSwitch()
        acl = ACL(number='100')
        ace = ACE(number=200)
        acl.add_ace(ace)
        self.cw._switch.add_complete_acl(acl)
        expErrorLst = []

        confList, errList = self.cw.acl()

        self.assertEqual(expErrorLst, errList)
        self.assertIn('entry 200', confList[0][1])

    def test_acl_srcOpNotEqualEq(self):
        self.cw._switch = XOS.XosSwitch()
        acl = ACL(number='100')
        ace = ACE(number=200, source_op='ne', source_port=53)
        acl.add_ace(ace)
        self.cw._switch.add_complete_acl(acl)
        expErrList = ['ERROR: ACL source operator "ne" not supported']

        confList, errList = self.cw.acl()

        self.assertEqual(expErrList, errList)
        self.assertIn('entry 200', confList[0][1])

    def test_acl_destOpNotEqualEq(self):
        self.cw._switch = XOS.XosSwitch()
        acl = ACL(number='100')
        ace = ACE(number=200, dest_op='ne', dest_port=53)
        acl.add_ace(ace)
        self.cw._switch.add_complete_acl(acl)
        expErrList = ['ERROR: ACL destination operator "ne" not supported']

        confList, errList = self.cw.acl()

        self.assertEqual(expErrList, errList)
        self.assertIn('entry 200', confList[0][1])

    def test_stack_notice(self):
        reason = 'default'
        self.cw._switch = self.mockTargetSwitch
        self.mockTargetSwitch.get_ports.return_value = [self.mockTargetPort1]
        self.mockTargetPort1.get_admin_state_reason.return_value = reason
        self.mockTargetPort1.get_auto_neg_reason.return_value = reason
        self.mockTargetPort1.get_short_description_reason.return_value = \
            reason
        self.mockTargetPort1.get_description_reason.return_value = reason
        self.mockTargetPort1.get_description_reason.return_value = reason
        self.mockTargetPort1.get_jumbo_reason.return_value = reason
        self.mockTargetPort1.get_ipv4_acl_in_reason.return_value = reason
        self.mockTargetSwitch.is_stack.return_value = True
        expectedConf = []
        expectedErr = [self.noticeStackingModeNeeded1,
                       self.noticeStackingModeNeeded2,
                       self.noticeStackingModeNeeded3]
        expected = (expectedConf, expectedErr)

        result = self.cw.port()

        self.assertEqual(expected, result)


if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
