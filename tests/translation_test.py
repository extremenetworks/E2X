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

import CM


class Translation_test(unittest.TestCase):

    def setUp(self):
        self.cm = CM.CoreModule()

    def test_translate_fails_because_of_missing_feature_module(self):
        cmd = 'set snmp group company security-model v1'
        translateList = [cmd]
        expected = 'NOTICE: Ignoring unknown command "' + cmd + '"'
        self.cm.set_source_switch('C5K125-48P2')
        self.cm.set_target_switch('SummitX460-48p+2xf')
        self.maxDiff = None

        translatedList, result = self.cm.translate(translateList)

        self.assertIn(expected, result)

    def test_translate_ok(self):
        translateList = ['set port disable ge.1.1']
        expected = 'disable ports 1'

        self.cm.set_source_switch('C5K125-48P2')
        self.cm.set_target_switch('SummitX460-48p+2xf')

        translatedList, err = self.cm.translate(translateList)

        self.assertIn(expected, translatedList)

    def test_translate_2sf_ok(self):
        translateList = ['set port disable ge.1.1']
        expected = 'disable ports 1'
        self.cm.set_source_switch('C5K125-48P2')
        self.cm.set_target_switch('SummitX460-48p+2sf')
        translatedList, err = self.cm.translate(translateList)
        self.assertIn(expected, translatedList)

    def test_translate_4sf_ok(self):
        translateList = ['set port disable ge.1.1']
        expected = 'disable ports 1'
        self.cm.set_source_switch('C5K125-48P2')
        self.cm.set_target_switch('SummitX460-48p+4sf')
        translatedList, err = self.cm.translate(translateList)
        self.assertIn(expected, translatedList)

    def test_translate_2sf_4sf_ok(self):
        translateList = ['set port disable ge.1.1']
        expected = 'disable ports 1'
        self.cm.set_source_switch('C5K125-48P2')
        self.cm.set_target_switch('SummitX460-48p+2sf+4sf')
        translatedList, err = self.cm.translate(translateList)
        self.assertIn(expected, translatedList)

    def test_translate_no_poe_ok(self):
        translateList = ['set port disable ge.1.1']
        expected = 'disable ports 1'
        self.cm.set_source_switch('C5K125-48')
        self.cm.set_target_switch('SummitX460-48p+2xf')
        translatedList, err = self.cm.translate(translateList)
        self.assertIn(expected, translatedList)

    def test_translate_24_ports_ok(self):
        translateList = ['set port disable ge.1.1']
        expected = 'disable ports 1'
        self.cm.set_source_switch('C5G124-24')
        self.cm.set_target_switch('SummitX460-24t')
        translatedList, err = self.cm.translate(translateList)
        self.assertIn(expected, translatedList)

    def test_translate_fails_because_missing_port(self):
        translateList = ['set port disable ge.1.25']
        expected = 'ERROR: Port ge.1.25 not found (set port disable)'
        self.cm.set_source_switch('C5G124-24')
        self.cm.set_target_switch('SummitX460-24t')
        self.maxDiff = None
        translatedList, result = self.cm.translate(translateList)
        self.assertIn(expected, result)

    def test_translate_fails_because_missing_combo_port(self):
        translateList = ['set port disable tg.1.49']
        expected = 'ERROR: Port tg.1.49 not found (set port disable)'
        self.cm.set_source_switch('C5G124-24')
        self.cm.set_target_switch('SummitX460-24t')
        self.maxDiff = None
        translatedList, result = self.cm.translate(translateList)
        self.assertIn(expected, result)

    def test_translate_to_empty_ok(self):
        translateList = ['set port disable ge.1.1',
                         'set port enable ge.1.1']
        expected = []
        unexpected = 'enable ports 1'
        self.cm.set_source_switch('C5K125-48P2')
        self.cm.set_target_switch('SummitX460-48p+2xf')
        translatedList, err = self.cm.translate(translateList)
        self.assertNotIn(unexpected, translatedList)

    def test_translate_two_commands_ok(self):
        translateList = ['set port disable ge.1.1',
                         'set port disable tg.1.50',
                         ]
        expected = ['disable ports 1',
                    'disable ports 54',
                    ]
        self.cm.set_source_switch('C5K125-48P2')
        self.cm.set_target_switch('SummitX460-48p+2xf')
        translatedList, err = self.cm.translate(translateList)
        for exp in expected:
            self.assertIn(exp, translatedList)

    def test_translate_to_three_commands_ok(self):
        translateList = ['set port disable ge.1.1',
                         'set port disable tg.1.50',
                         'set port speed ge.1.2 100',
                         'set port duplex ge.1.2 full',
                         'set port negotiation ge.1.2 disable',
                         ]
        expected = ['disable ports 1',
                    'disable ports 54',
                    'configure ports 2 auto off speed 100 duplex full',
                    ]
        self.cm.set_source_switch('C5K125-48P2')
        self.cm.set_target_switch('SummitX460-48p+2xf')
        translatedList, err = self.cm.translate(translateList)
        for exp in expected:
            self.assertIn(exp, translatedList)

    def test_translate_alias_ok(self):
        translateList = ['set port alias ge.1.1 "Port alias"']
        expected = ['configure ports 1 display-string Port_alias',
                    'configure ports 1 description-string "Port_alias"']
        self.cm.set_source_switch('C5K125-48P2')
        self.cm.set_target_switch('SummitX460-48p+2sf')
        translatedList, err = self.cm.translate(translateList)
        for exp in expected:
            self.assertIn(exp, translatedList)

    def test_translate_disable_jumbo_ok(self):
        translateList = ['set port jumbo disable *.*.*']
        expected = []
        self.cm.set_source_switch('C5K125-48P2')
        self.cm.set_target_switch('SummitX460-48p+2sf')
        translatedList, err = self.cm.translate(translateList)
        translatedList = [l for l in translatedList if 'jumbo-frame' in l]
        self.assertEqual(expected, translatedList)

    def test_translate_default_jumbo_ok(self):
        translateList = []
        command = 'enable jumbo-frame ports '
        expected = [command + str(i) for i in range(1, 49)]
        expected.extend([command + str(i) for i in range(53, 55)])
        self.cm.set_source_switch('C5K125-48P2')
        self.cm.set_target_switch('SummitX460-48p+2sf')
        translatedList, err = self.cm.translate(translateList)
        translatedList = [l for l in translatedList if 'jumbo-frame' in l]
        self.assertEqual(expected, translatedList)

    def test_translate_vlan_create_tag_only_ok(self):
        translateList = ['set vlan create 2',
                         ]
        expected = ['create vlan SYS_NLD_0002 tag 2',
                    ]
        self.cm.set_source_switch('C5K125-48P2')
        self.cm.set_target_switch('SummitX460-48p+2sf')
        translatedList, err = self.cm.translate(translateList)
        for exp in expected:
            self.assertIn(exp, translatedList)

    def test_translate_vlan_create_many_tag_only_ok(self):
        translateList = ['set vlan create 2,5,10-13,100,2001',
                         ]
        expected = ['create vlan SYS_NLD_0002 tag 2',
                    'create vlan SYS_NLD_0005 tag 5',
                    'create vlan SYS_NLD_0010 tag 10',
                    'create vlan SYS_NLD_0011 tag 11',
                    'create vlan SYS_NLD_0012 tag 12',
                    'create vlan SYS_NLD_0013 tag 13',
                    'create vlan SYS_NLD_0100 tag 100',
                    'create vlan SYS_NLD_2001 tag 2001',
                    ]
        self.cm.set_source_switch('C5K125-48P2')
        self.cm.set_target_switch('SummitX460-48p+2sf')
        translatedList, err = self.cm.translate(translateList)
        for exp in expected:
            self.assertIn(exp, translatedList)

    def test_translate_vlan_create_tag_name_ok(self):
        translateList = ['set vlan create 2',
                         'set vlan name 2 vl_two',
                         ]
        expected = ['create vlan vl_two tag 2',
                    ]
        self.cm.set_source_switch('C5K125-48P2')
        self.cm.set_target_switch('SummitX460-48p+2sf')
        translatedList, err = self.cm.translate(translateList)
        for exp in expected:
            self.assertIn(exp, translatedList)

    def test_translate_vlan_create_tag_empty_name_ok(self):
        translateList = ['set vlan create 2',
                         'set vlan name 2 ""',
                         ]
        expected = ['create vlan SYS_NLD_0002 tag 2',
                    ]
        self.cm.set_source_switch('C5K125-48P2')
        self.cm.set_target_switch('SummitX460-48p+2sf')
        translatedList, err = self.cm.translate(translateList)
        for exp in expected:
            self.assertIn(exp, translatedList)

    def test_translate_vlan_create_many_tag_name_ok(self):
        translateList = ['set vlan create 2-5',
                         'set vlan name 2 vl_two',
                         'set vlan name 3 vl_three',
                         'set vlan name 4 vl_four',
                         'set vlan name 5 vl_five',
                         ]
        expected = ['create vlan vl_two tag 2',
                    'create vlan vl_three tag 3',
                    'create vlan vl_four tag 4',
                    'create vlan vl_five tag 5',
                    ]
        self.cm.set_source_switch('C5K125-48P2')
        self.cm.set_target_switch('SummitX460-48p+2sf')
        translatedList, err = self.cm.translate(translateList)
        for exp in expected:
            self.assertIn(exp, translatedList)

    def test_translate_vlan_pvid_mod_ok(self):
        translateList = ['set vlan create 2',
                         'set vlan name 2 vl_two',
                         'set port vlan ge.1.1 2 modify-egress',
                         ]
        expected = ['create vlan vl_two tag 2',
                    'configure vlan Default delete ports 1',
                    'configure vlan vl_two add ports 1 untagged',
                    ]
        self.cm.set_source_switch('C5K125-48P2')
        self.cm.set_target_switch('SummitX460-48p+2sf')
        translatedList, err = self.cm.translate(translateList)
        for exp in expected:
            self.assertIn(exp, translatedList)

    def test_translate_vlan_pvid_manual_ok(self):
        translateList = ['set vlan create 2',
                         'set vlan name 2 vl_two',
                         'set port vlan ge.1.1 2',
                         'set vlan egress 2 ge.1.1 untagged',
                         'clear vlan egress 1 ge.1.1',
                         ]
        expected = ['create vlan vl_two tag 2',
                    'configure vlan Default delete ports 1',
                    'configure vlan vl_two add ports 1 untagged',
                    ]
        self.cm.set_source_switch('C5K125-48P2')
        self.cm.set_target_switch('SummitX460-48p+2sf')
        translatedList, err = self.cm.translate(translateList)
        for exp in expected:
            self.assertIn(exp, translatedList)

    def test_translate_vlan_tagged_egress_ok(self):
        translateList = ['set vlan create 2',
                         'set vlan name 2 vl_two',
                         'set vlan egress 2 ge.1.1 tagged',
                         ]
        expected = ['create vlan vl_two tag 2',
                    'configure vlan vl_two add ports 1 tagged',
                    ]
        unexpected = ['configure vlan vl_two delete ports 1',
                      ]
        self.cm.set_source_switch('C5K125-48P2')
        self.cm.set_target_switch('SummitX460-48p+2sf')
        translatedList, err = self.cm.translate(translateList)
        for exp in expected:
            self.assertIn(exp, translatedList)
        for unexp in unexpected:
            self.assertNotIn(unexp, translatedList)

    # I think this is the best translation of 'clear vlan egress 1 ...'
    def test_translate_vlan_clear_egress_one_ok(self):
        translateList = ['clear vlan egress 1 ge.1.1',
                         ]
        expected = ['configure vlan Default delete ports 1',
                    ]
        self.cm.set_source_switch('C5K125-48P2')
        self.cm.set_target_switch('SummitX460-48p+2sf')
        translatedList, err = self.cm.translate(translateList)
        for exp in expected:
            self.assertIn(exp, translatedList)

    def test_translate_vlan_clear_egress_one_all_ok(self):
        translateList = ['clear vlan egress 1 *.*.*',
                         ]
        expected = ['configure vlan Default delete ports 1-48,53-54',
                    ]
        self.cm.set_source_switch('C5K125-48P2')
        self.cm.set_target_switch('SummitX460-48p+2sf')
        translatedList, err = self.cm.translate(translateList)
        for exp in expected:
            self.assertIn(exp, translatedList)

    def test_translate_vlan_clear_egress_one_all_4sf_ok(self):
        translateList = ['clear vlan egress 1 *.*.*',
                         ]
        expected = ['configure vlan Default delete ports 1-48,55-56',
                    ]
        self.cm.set_source_switch('C5K125-48P2')
        self.cm.set_target_switch('SummitX460-48p+4sf')
        translatedList, err = self.cm.translate(translateList)
        for exp in expected:
            self.assertIn(exp, translatedList)

    def test_translate_fails_because_two_untagged_vlans(self):
        translateList = ['set vlan create 2',
                         'set vlan egress 2 ge.1.1 untagged',
                         'set port vlan ge.1.1 2',
                         ]
        expected = ('ERROR: Port "1" has multiple untagged egress VLANs: '
                    "('Default', 1) ('SYS_NLD_0002', 2)")
        self.cm.set_source_switch('C5K125-48P2')
        self.cm.set_target_switch('SummitX460-48p+2sf')
        self.maxDiff = None
        translatedList, result = self.cm.translate(translateList)
        self.assertIn(expected, result)

    def test_translate_fails_because_two_untagged_vlans_v2(self):
        translateList = ['set vlan create 2',
                         'set vlan egress 2 ge.1.1 untagged',
                         ]
        expected = ('ERROR: Port "1" has multiple untagged egress VLANs: '
                    "('Default', 1) ('SYS_NLD_0002', 2)")
        self.cm.set_source_switch('C5K125-48P2')
        self.cm.set_target_switch('SummitX460-48p+2sf')
        self.maxDiff = None
        translatedList, result = self.cm.translate(translateList)
        self.assertIn(expected, result)

    def test_translate_fails_because_different_untagged_in_out(self):
        translateList = ['set vlan create 2',
                         'set vlan egress 2 ge.1.1 untagged',
                         'clear vlan egress 1 ge.1.1',
                         ]
        expected = ('ERROR: Untagged VLAN egress and ingress differs'
                    ' for port "1"')
        self.cm.set_source_switch('C5K125-48P2')
        self.cm.set_target_switch('SummitX460-48p+2sf')
        self.maxDiff = None
        translatedList, result = self.cm.translate(translateList)
        self.assertIn(expected, result)

    def test_translate_dynamic_lag_ok(self):
        translateList = ['set lacp aadminkey lag.0.1 100',
                         'set port lacp port ge.1.1-2 aadminkey 100',
                         'set port lacp port ge.1.1-2 enable']
        expected = ['enable sharing 1 grouping 1-2 algorithm address-based L3'
                    ' lacp']
        self.cm.set_source_switch('C5K125-48P2')
        self.cm.set_target_switch('SummitX460-48p+2sf')
        translatedList, err = self.cm.translate(translateList)
        for exp in expected:
            self.assertIn(exp, translatedList)

    def test_translate_static_lag_ok(self):
        translateList = ['set lacp static lag.0.1 key 100 ge.1.1-2']
        expected = ['enable sharing 1 grouping 1-2 algorithm address-based L3']
        self.cm.set_source_switch('C5K125-48P2')
        self.cm.set_target_switch('SummitX460-48p+2sf')
        translatedList, err = self.cm.translate(translateList)
        for exp in expected:
            self.assertIn(exp, translatedList)

    def test_translate_static_lag_manual_ok(self):
        translateList = ['set lacp static lag.0.1',
                         'set lacp aadminkey lag.0.1 100',
                         'set port lacp port ge.1.1-2 aadminkey 100']
        expected = ['enable sharing 1 grouping 1-2 algorithm address-based L3']
        self.cm.set_source_switch('C5K125-48P2')
        self.cm.set_target_switch('SummitX460-48p+2sf')
        translatedList, err = self.cm.translate(translateList)
        for exp in expected:
            self.assertIn(exp, translatedList)

    def test_translate_FMs_port_vlan_lag_ok(self):
        translateList = [
            '# example configuration exercising FMs port, VLAN, and LAG',
            '# for migration from C5G124-24 to Summit X460-24t',
            '# adjust jumbo port defaults to reduce generated output',
            'set port jumbo disable *.*.*',
            '# with LACP disabled on ports per default, single port LAG'
            ' should be enabled',
            'set lacp singleportlag enable',
            '# create some VLANs',
            'set vlan create 4,10,20,100-105,200,300,666,1000,3001-3010',
            'set vlan name 4 ADMIN',
            'set vlan name 10 DATA',
            'set vlan name 20 VOICE',
            'set vlan name 100 "VMK"',
            'set vlan name 101 "VIRTUAL SERVER 1"',
            'set vlan name 102 "VIRTUAL SERVER 2"',
            'set vlan name 103 "VIRTUAL SERVER 3"',
            'set vlan name 104 "VIRTUAL SERVER 4"',
            'set vlan name 105 "VIRTUAL SERVER 5"',
            'set vlan name 200 SERVER',
            'set vlan name 300 WIRELESS',
            'set vlan name 666 "UNUSED PORTS"',
            'set vlan name 1000 "NATIVE"',
            '# ports 1 to 10 for user PCs behind IP phones',
            'set port vlan ge.1.1-10 10 modify-egress',
            'set vlan egress 20 ge.1.1-16 tagged',
            'set port alias ge.1.1-10 "PC behind phone"',
            '# ports 11-12 LAG to physical server',
            'set lacp aadminkey lag.0.1 100',
            'set port lacp port ge.1.11-12 aadminkey 100',
            'set port lacp port ge.1.11-12 enable',
            'set port vlan ge.1.11-12;lag.0.1 200 modify-egress',
            'set port alias ge.1.11 "srv01 nic1"',
            'set port alias ge.1.12 "srv01 nic2"',
            '# ports 13-14 single attached virtualiziation servers',
            'set port vlan ge.1.13-14 100 modify-egress',
            'set vlan egress 101-105 ge.1.13-14 tagged',
            'set port alias ge.1.13 kvm01',
            'set port alias ge.1.14 kvm02',
            '# ports 15-16 dual attached virtualization server',
            'set lacp aadminkey lag.0.2 200',
            'set port lacp port ge.1.15-16 aadminkey 200',
            'set port lacp port ge.1.15-16 enable',
            'set port vlan ge.1.15-16;lag.0.2 100 modify-egress',
            'set vlan egress 101-105 ge.1.15-16;lag.0.2 tagged',
            'set port alias ge.1.15 "kvm03 eth0"',
            'set port alias ge.1.16 "kvm03 eth1"',
            '# ports 17-18 static LAG to 3rd party wireless controller',
            'set lacp static lag.0.3 key 300 ge.1.17-18',
            'set port vlan ge.1.17-18;lag.0.3 300 modify-egress',
            'set port speed ge.1.17-18 100',
            'set port duplex ge.1.17-18 full',
            'set port negotiation ge.1.17-18 disable',
            'set port alias ge.1.17 "WLC Port 1"',
            'set port alias ge.1.18 "WLC Port 2"',
            '# ports 19-20 not used',
            'set port vlan ge.1.19-20 666 modify-egress',
            'set port disable ge.1.19-20',
            'set port alias ge.1.19-20 Unused',
            '# ports 21-24 LAG uplinks to distribution',
            'set port lacp port ge.1.21-24 enable',
            'set lacp aadminkey lag.0.5 500',
            'set port lacp port ge.1.21-22 aadminkey 500',
            'set lacp aadminkey lag.0.6 600',
            'set port lacp port ge.1.23-24 aadminkey 600',
            'clear vlan egress 1 ge.1.21-24;lag.0.5-6',
            'set port alias ge.1.21 "kl_122_dis1-ge.1.1"',
            'set port alias ge.1.22 "kl_122_dis1-ge.1.2"',
            'set port alias ge.1.23 "kl_122_dis2-ge.1.1"',
            'set port alias ge.1.24 "kl_122_dis2-ge.1.2"',
            '# XOS cannot separate VLAN egress and ingress',
            'set port vlan ge.1.21-24;lag.0.5-6 1000 modify-egress',
            'set vlan egress 4,10,20,100-105,200,300,3001-3010 ge.1.21-24' +
            ';lag.0.5-6 tagged']
        expected = [
            'configure ports 1 display-string PC_behind_phone',
            'configure ports 1 description-string "PC_behind_phone"',
            'configure ports 2 display-string PC_behind_phone',
            'configure ports 2 description-string "PC_behind_phone"',
            'configure ports 3 display-string PC_behind_phone',
            'configure ports 3 description-string "PC_behind_phone"',
            'configure ports 4 display-string PC_behind_phone',
            'configure ports 4 description-string "PC_behind_phone"',
            'configure ports 5 display-string PC_behind_phone',
            'configure ports 5 description-string "PC_behind_phone"',
            'configure ports 6 display-string PC_behind_phone',
            'configure ports 6 description-string "PC_behind_phone"',
            'configure ports 7 display-string PC_behind_phone',
            'configure ports 7 description-string "PC_behind_phone"',
            'configure ports 8 display-string PC_behind_phone',
            'configure ports 8 description-string "PC_behind_phone"',
            'configure ports 9 display-string PC_behind_phone',
            'configure ports 9 description-string "PC_behind_phone"',
            'configure ports 10 display-string PC_behind_phone',
            'configure ports 10 description-string "PC_behind_phone"',
            'configure ports 11 display-string srv01_nic1',
            'configure ports 11 description-string "srv01_nic1"',
            'configure ports 12 display-string srv01_nic2',
            'configure ports 12 description-string "srv01_nic2"',
            'configure ports 13 display-string kvm01',
            'configure ports 13 description-string "kvm01"',
            'configure ports 14 display-string kvm02',
            'configure ports 14 description-string "kvm02"',
            'configure ports 15 display-string kvm03_eth0',
            'configure ports 15 description-string "kvm03_eth0"',
            'configure ports 16 display-string kvm03_eth1',
            'configure ports 16 description-string "kvm03_eth1"',
            'configure ports 17 auto off speed 100 duplex full',
            'configure ports 17 display-string WLC_Port_1',
            'configure ports 17 description-string "WLC_Port_1"',
            'configure ports 18 auto off speed 100 duplex full',
            'configure ports 18 display-string WLC_Port_2',
            'configure ports 18 description-string "WLC_Port_2"',
            'disable ports 19',
            'configure ports 19 display-string Unused',
            'configure ports 19 description-string "Unused"',
            'disable ports 20',
            'configure ports 20 display-string Unused',
            'configure ports 20 description-string "Unused"',
            'configure ports 21 display-string kl_122_dis1-ge.',
            'configure ports 21 description-string "kl_122_dis1-ge.1.1"',
            'configure ports 22 display-string kl_122_dis1-ge.',
            'configure ports 22 description-string "kl_122_dis1-ge.1.2"',
            'configure ports 23 display-string kl_122_dis2-ge.',
            'configure ports 23 description-string "kl_122_dis2-ge.1.1"',
            'configure ports 24 display-string kl_122_dis2-ge.',
            'configure ports 24 description-string "kl_122_dis2-ge.1.2"',
            'enable sharing 11 grouping 11-12 algorithm address-based L3 lacp',
            'enable sharing 15 grouping 15-16 algorithm address-based L3 lacp',
            'enable sharing 17 grouping 17-18 algorithm address-based L3',
            'enable sharing 21 grouping 21-22 algorithm address-based L3 lacp',
            'enable sharing 23 grouping 23-24 algorithm address-based L3 lacp',
            'configure vlan Default delete ports 1-24',
            'create vlan ADMIN tag 4',
            'configure vlan ADMIN add ports 21,23 tagged',
            'create vlan DATA tag 10',
            'configure vlan DATA add ports 1-10 untagged',
            'configure vlan DATA add ports 21,23 tagged',
            'create vlan VOICE tag 20',
            'configure vlan VOICE add ports 1-10,21,23 tagged',
            'create vlan VMK tag 100',
            'configure vlan VMK add ports 13-15 untagged',
            'configure vlan VMK add ports 21,23 tagged',
            'create vlan VIRTUAL_SERVER_1 tag 101',
            'configure vlan VIRTUAL_SERVER_1 add ports 13-15,21,23 tagged',
            'create vlan VIRTUAL_SERVER_2 tag 102',
            'configure vlan VIRTUAL_SERVER_2 add ports 13-15,21,23 tagged',
            'create vlan VIRTUAL_SERVER_3 tag 103',
            'configure vlan VIRTUAL_SERVER_3 add ports 13-15,21,23 tagged',
            'create vlan VIRTUAL_SERVER_4 tag 104',
            'configure vlan VIRTUAL_SERVER_4 add ports 13-15,21,23 tagged',
            'create vlan VIRTUAL_SERVER_5 tag 105',
            'configure vlan VIRTUAL_SERVER_5 add ports 13-15,21,23 tagged',
            'create vlan SERVER tag 200',
            'configure vlan SERVER add ports 11 untagged',
            'configure vlan SERVER add ports 21,23 tagged',
            'create vlan WIRELESS tag 300',
            'configure vlan WIRELESS add ports 17 untagged',
            'configure vlan WIRELESS add ports 21,23 tagged',
            'create vlan UNUSED_PORTS tag 666',
            'configure vlan UNUSED_PORTS add ports 19-20 untagged',
            'create vlan NATIVE tag 1000',
            'configure vlan NATIVE add ports 21,23 untagged',
            'create vlan SYS_NLD_3001 tag 3001',
            'configure vlan SYS_NLD_3001 add ports 21,23 tagged',
            'create vlan SYS_NLD_3002 tag 3002',
            'configure vlan SYS_NLD_3002 add ports 21,23 tagged',
            'create vlan SYS_NLD_3003 tag 3003',
            'configure vlan SYS_NLD_3003 add ports 21,23 tagged',
            'create vlan SYS_NLD_3004 tag 3004',
            'configure vlan SYS_NLD_3004 add ports 21,23 tagged',
            'create vlan SYS_NLD_3005 tag 3005',
            'configure vlan SYS_NLD_3005 add ports 21,23 tagged',
            'create vlan SYS_NLD_3006 tag 3006',
            'configure vlan SYS_NLD_3006 add ports 21,23 tagged',
            'create vlan SYS_NLD_3007 tag 3007',
            'configure vlan SYS_NLD_3007 add ports 21,23 tagged',
            'create vlan SYS_NLD_3008 tag 3008',
            'configure vlan SYS_NLD_3008 add ports 21,23 tagged',
            'create vlan SYS_NLD_3009 tag 3009',
            'configure vlan SYS_NLD_3009 add ports 21,23 tagged',
            'create vlan SYS_NLD_3010 tag 3010',
            'configure vlan SYS_NLD_3010 add ports 21,23 tagged']
        self.cm.set_source_switch('C5K125-48P2')
        self.cm.set_target_switch('SummitX460-48p+2sf')
        translatedList, err = self.cm.translate(translateList)
        for exp in expected:
            self.assertIn(exp, translatedList)

if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
