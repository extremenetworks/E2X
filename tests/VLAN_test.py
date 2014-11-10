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

import VLAN
import Switch
import Port

from unittest.mock import MagicMock


class VLAN_test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.mockPort = MagicMock(spec=Port.Port)
        cls.mockPort.is_hardware.return_value = True
        cls.mockSwitch = MagicMock(spec=Switch.Switch)
        cls.mockSwitch.get_ports_by_name.return_value = [cls.mockPort]

        cls.ErrorStart = 'ERROR: '
        cls.WarnStart = 'WARN: '
        cls.NoticeStart = 'NOTICE: '

    def setUp(self):
        self.vl = VLAN.VLAN(switch=self.mockSwitch)

    def test_set_get_name(self):
        name = 'Default'

        self.assertEqual(None, self.vl._name)

        self.vl.set_name(name)

        self.assertEqual(name, self.vl.get_name())

    def test_set_get_tag_ok(self):
        tag = '100'

        self.assertEqual(None, self.vl._tag)

        result = self.vl.set_tag(tag)

        self.assertTrue(result)
        self.assertEqual(int(tag), self.vl.get_tag())

    def test_set_tag_fail(self):
        tag = 'tag1'

        self.assertFalse(self.vl.set_tag(tag))

        tag = '4096'

        self.assertFalse(self.vl.set_tag(tag))

    def test_str(self):
        vlan = VLAN.VLAN('bar', '10')
        expectedName = 'Name: ' + vlan.get_name()
        expectedTag = 'Tag: ' + str(vlan.get_tag())

        result = str(vlan)

        self.assertIn(expectedName, result)
        self.assertIn(expectedTag, result)

    def test_get_list(self):
        direction = 'in'
        expectedList = self.vl._ingress_ports

        result = self.vl._get_list(direction)

        self.assertIs(expectedList, result)

        direction = 'e'
        expectedList = self.vl._egress_ports

        result = self.vl._get_list(direction)

        self.assertIs(expectedList, result)

        direction = 'nn'

        self.assertIsNone(self.vl._get_list(direction))

    def test_get_ports_ok(self):
        egressPort1Name = 'e1'
        ingressPort1name = 'i1'
        direction = 'e'
        tagged = 'all'
        self.vl._egress_ports.append((egressPort1Name, tagged))
        self.vl._ingress_ports.append((ingressPort1name, tagged))
        expectedEgressList = [egressPort1Name]
        expectedIngressList = [ingressPort1name]

        result = self.vl._get_ports(direction, tagged)

        self.assertEqual(expectedEgressList, result)

        direction = 'in'

        result = self.vl._get_ports(direction, tagged)

        self.assertEqual(expectedIngressList, result)

        tagged = 'untagged'
        self.vl._ingress_ports[0] = (ingressPort1name, tagged)
        expected = [ingressPort1name]

        result = self.vl._get_ports(direction, tagged)

        self.assertEqual(expected, result)

        expected = []

        result = self.vl._get_ports(direction, 'tagged')

        self.assertEqual(expected, result)

    def test_get_ports_fail_wrong_direction(self):
        direction = 'nn'
        tagged = 'all'

        self.assertIsNone(self.vl._get_ports(direction, tagged))

    def test_get_egress_ports(self):
        egressPort1Name = 'e1'
        tagged = 'untagged'
        self.vl._egress_ports.append((egressPort1Name, tagged))
        expectedEgressList = [egressPort1Name]

        result = self.vl.get_egress_ports(tagged)

        self.assertEqual(expectedEgressList, result)

    def test_get_ingress_ports(self):
        ingressPort1Name = 'i1'
        tagged = 'untagged'
        self.vl._ingress_ports.append((ingressPort1Name, tagged))
        expectedIngressList = [ingressPort1Name]

        result = self.vl.get_ingress_ports(tagged)

        self.assertEqual(expectedIngressList, result)

    def test_add_port_ok(self):
        portName = 'i1'
        direction = 'in'
        tagged = 'tagged'
        expectedEntry = (portName, tagged)

        result = self.vl._add_port(portName, direction, tagged)

        self.assertTrue(result)
        self.assertEqual(expectedEntry, self.vl._ingress_ports[0])

    def test_add_port_fail_wrong_direction(self):
        portName = 'i1'
        direction = 'nn'
        tagged = 'tagged'

        result = self.vl._add_port(portName, direction, tagged)

        self.assertFalse(result)

    def test_add_port_fail_wrong_tag(self):
        portName = 'i1'
        direction = 'in'
        tagged = 'dontknow'

        result = self.vl._add_port(portName, direction, tagged)

        self.assertFalse(result)

    def test_add_port_ok_but_entry_exists(self):
        portName = 'i1'
        direction = 'in'
        tagged = 'tagged'
        self.vl._ingress_ports.append((portName, tagged))

        result = self.vl._add_port(portName, direction, tagged)

        self.assertTrue(result)
        self.assertEqual(1, len(self.vl._ingress_ports))

    def test_add_egress_port(self):
        portName = 'e1'
        tagged = 'tagged'
        expectedLen = len(self.vl._egress_ports) + 1

        result = self.vl.add_egress_port(portName, tagged)

        self.assertTrue(result)
        self.assertEqual(expectedLen, len(self.vl._egress_ports))

    def test_add_ingress_port(self):
        portName = 'i1'
        tagged = 'tagged'
        expectedLen = len(self.vl._ingress_ports) + 1

        result = self.vl.add_ingress_port(portName, tagged)

        self.assertTrue(result)
        self.assertEqual(expectedLen, len(self.vl._ingress_ports))

    def test_del_port_ok_tagged(self):
        portName = 'i1'
        tagged = 'tagged'
        direction = 'in'
        self.vl._ingress_ports.append((portName, tagged))
        expectedLen = 0

        result = self.vl._del_port(portName, direction, tagged)

        self.assertTrue(result)
        self.assertEqual(expectedLen, len(self.vl._ingress_ports))

    def test_del_port_ok_all(self):
        portName = 'i1'
        tagged = 'all'
        direction = 'in'
        self.vl._ingress_ports.append((portName, 'untagged'))
        expectedLen = 0

        result = self.vl._del_port(portName, direction, tagged)

        self.assertTrue(result)
        self.assertEqual(expectedLen, len(self.vl._ingress_ports))

    def test_del_port_fail_wrong_direction(self):
        portName = 'i1'
        tagged = 'tagged'
        direction = 'nn'
        self.vl._ingress_ports.append((portName, tagged))
        expectedLen = 1

        result = self.vl._del_port(portName, direction, tagged)

        self.assertFalse(result)
        self.assertEqual(expectedLen, len(self.vl._ingress_ports))

    def test_del_port_fail_wrong_tag(self):
        portName = 'i1'
        tagged = 'dontknow'
        direction = 'in'
        self.vl._ingress_ports.append((portName, tagged))
        expectedLen = 1

        result = self.vl._del_port(portName, direction, tagged)

        self.assertFalse(result)
        self.assertEqual(expectedLen, len(self.vl._ingress_ports))

    def test_del_egress_port(self):
        portName = 'e1'
        tagged = 'tagged'
        self.vl._egress_ports.append((portName, tagged))
        expectedLen = 0

        result = self.vl.del_egress_port(portName)

        self.assertTrue(result)
        self.assertEqual(expectedLen, len(self.vl._egress_ports))

    def test_del_ingress_port(self):
        portName = 'i1'
        tagged = 'untagged'
        self.vl._ingress_ports.append((portName, tagged))
        expectedLen = 0

        result = self.vl.del_ingress_port(portName, 'untagged')

        self.assertTrue(result)
        self.assertEqual(expectedLen, len(self.vl._ingress_ports))

    def test_del_port(self):
        portName = 'p1'
        tagged = 'untagged'
        self.vl._ingress_ports.append((portName, tagged))
        self.vl._egress_ports.append((portName, tagged))
        expectedLen = 0

        result = self.vl.del_port(portName)

        self.assertTrue(result)
        self.assertEqual(expectedLen, len(self.vl._ingress_ports))
        self.assertEqual(expectedLen, len(self.vl._egress_ports))

    def test_del_all_ports(self):
        self.vl._egress_ports.append(('i1', 'untagged'))
        self.vl._ingress_ports.append(('e1', 'tagged'))

        self.vl.del_all_ports()

        self.assertEqual([], self.vl._egress_ports)
        self.assertEqual([], self.vl._ingress_ports)

    def test_transfer_config_ok_port_in_port_mapping(self):
        srcVlan = VLAN.VLAN(name='foo', tag=1)
        eg_tagged_name = 'et1'
        eg_untagged_name = 'eut1'
        srcVlan._egress_ports.append((eg_tagged_name, 'tagged'))
        srcVlan._egress_ports.append((eg_untagged_name, 'untagged'))
        ing_tagged_name = 'int1'
        ing_untagged_name = 'inut1'
        srcVlan._ingress_ports.append((ing_tagged_name, 'tagged'))
        srcVlan._ingress_ports.append((ing_untagged_name, 'untagged'))
        portMapping = {eg_tagged_name: '1', eg_untagged_name: '2',
                       ing_tagged_name: '3', ing_untagged_name: '4'}
        unmapped = ['5', '6']
        expected = []

        result = self.vl.transfer_config(srcVlan, portMapping, {}, unmapped)
        result = [el for el in result if not el.startswith('DEBUG: ')]

        self.assertEqual(expected, result)
        self.assertEqual(4, len(self.vl._egress_ports))
        self.assertEqual(('1', 'tagged'), self.vl._egress_ports[0])
        self.assertEqual(('2', 'untagged'), self.vl._egress_ports[1])
        self.assertEqual(4, len(self.vl._ingress_ports))
        self.assertEqual(('3', 'tagged'), self.vl._ingress_ports[0])
        self.assertEqual(('4', 'untagged'), self.vl._ingress_ports[1])

    def test_transfer_config_ok_port_in_lag_mapping(self):
        srcVlan = VLAN.VLAN(name='foo', tag=1)
        eg_tagged_name = 'lag.0.1'
        srcVlan._egress_ports.append((eg_tagged_name, 'tagged'))
        lag_mapping = {'lag.0.1': '1'}
        unmapped = []
        expected = []

        result = self.vl.transfer_config(srcVlan, {}, lag_mapping, unmapped)
        result = [el for el in result if not el.startswith('DEBUG: ')]

        self.assertEqual(expected, result)
        self.assertEqual(1, len(self.vl._egress_ports))
        self.assertEqual(('1', 'tagged'), self.vl._egress_ports[0])

    def test_transfer_config_warn_unmapped_ports(self):
        srcVlan = VLAN.VLAN(name='foo', tag=100)
        eg_tagged_name = 'et1'
        eg_untagged_name = 'eut1'
        eg_untagged_name2 = 'eut2'
        srcVlan._egress_ports.append((eg_tagged_name, 'tagged'))
        srcVlan._egress_ports.append((eg_untagged_name, 'untagged'))
        srcVlan._egress_ports.append((eg_untagged_name2, 'untagged'))
        ing_tagged_name = 'int1'
        ing_tagged_name2 = 'int2'
        ing_untagged_name = 'inut1'
        srcVlan._ingress_ports.append((ing_tagged_name, 'tagged'))
        srcVlan._ingress_ports.append((ing_tagged_name2, 'tagged'))
        srcVlan._ingress_ports.append((ing_untagged_name, 'untagged'))
        portMapping = {eg_untagged_name: '2',
                       ing_tagged_name: '3'}
        unmapped = ['5', '6']
        warnStr = self.WarnStart + 'Port "{}" in VLAN "' + \
            str(srcVlan.get_tag()) + '" ({}) not mapped to target switch'
        expected = [warnStr.format(eg_tagged_name, 'tagged'),
                    warnStr.format(eg_untagged_name2, 'untagged'),
                    warnStr.format(ing_tagged_name2, 'tagged'),
                    warnStr.format(ing_untagged_name, 'untagged')]

        result = self.vl.transfer_config(srcVlan, portMapping, {}, unmapped)
        result = [el for el in result if not el.startswith('DEBUG: ')]

        self.assertEqual(expected, result)
        self.assertEqual(1, len(self.vl._egress_ports))
        self.assertEqual(('2', 'untagged'), self.vl._egress_ports[0])
        self.assertEqual(1, len(self.vl._ingress_ports))
        self.assertEqual(('3', 'tagged'), self.vl._ingress_ports[0])

    def test_transfer_config_warn_shadowed_ports(self):
        srcVlan = VLAN.VLAN(name='foo', tag=100)
        eg_tagged_name = 'et1'
        eg_untagged_name = 'eut1'
        srcVlan._egress_ports.append((eg_tagged_name, 'tagged'))
        srcVlan._egress_ports.append((eg_untagged_name, 'untagged'))
        ing_tagged_name = 'int1'
        ing_untagged_name = 'inut1'
        srcVlan._ingress_ports.append((ing_tagged_name, 'tagged'))
        srcVlan._ingress_ports.append((ing_untagged_name, 'untagged'))
        portMapping = {eg_tagged_name: '1', eg_untagged_name: '2',
                       ing_tagged_name: '3', ing_untagged_name: '4'}
        unmapped = ['5', '6']
        lag_mapping = {'lag.0.1': '1'}
        noticeStr = self.NoticeStart + 'VLAN configuration of port ' + \
            '{} shadowed by LAG configuration'
        warnStr = self.WarnStart + 'Port "{}" in VLAN "' + \
            str(srcVlan.get_tag()) + '" ({}) omitted because of LAG with ' + \
            'same target port name'
        expected = [noticeStr.format(eg_tagged_name),
                    warnStr.format(eg_tagged_name, 'tagged, egress')]

        result = self.vl.transfer_config(srcVlan, portMapping, lag_mapping,
                                         unmapped)
        result = [el for el in result if not el.startswith('DEBUG: ')]

        self.assertEqual(expected, result)
        self.assertEqual(1, len(self.vl._egress_ports))
        self.assertEqual(('2', 'untagged'), self.vl._egress_ports[0])
        self.assertEqual(2, len(self.vl._ingress_ports))
        self.assertEqual(('3', 'tagged'), self.vl._ingress_ports[0])

    def test_transfer_config_fail_switch_undefined(self):
        targetVlan = VLAN.VLAN(name='bah', tag=101)
        srcVlan = VLAN.VLAN(name='foo', tag=100)
        eg_tagged_name = 'et1'
        srcVlan._egress_ports.append((eg_tagged_name, 'tagged'))
        portMapping = {}
        unmapped = []
        lag_mapping = {}
        errStr = self.ErrorStart + \
            'VLAN with tag ' + str(srcVlan.get_tag()) + ' and name "' + \
            srcVlan.get_name() + '" not associated with a switch'

        expected = [errStr]

        result = targetVlan.transfer_config(srcVlan, portMapping, lag_mapping,
                                            unmapped)
        result = [el for el in result if not el.startswith('DEBUG: ')]

        self.assertEqual(expected, result)

if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
