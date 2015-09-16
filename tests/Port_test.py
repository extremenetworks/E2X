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

from unittest.mock import Mock

from Port import Port


class Port_test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        port1data = {"type": "rj45", "speedrange": [10, 100, 1000],
                     "PoE": "yes"}
        port49data = {"type": "sfp", "speedrange": [1000, 10000], "PoE": "no"}
        cls.p1 = {'name': 'ge.1.1', 'label': '1', 'data': port1data}
        p2 = {'name': 'tg.1.49', 'label': '49', 'data': port49data}
        cls.ports = [cls.p1, p2]

    def setUp(self):
        entry = self.ports[0]
        self.p = Port(entry['label'], entry['name'], entry['data'])

    def test_init(self):
        for entry in self.ports:
            p = Port(entry['label'], entry['name'], entry['data'])

            self.assertEqual(entry['label'], p.get_label())
            self.assertEqual(entry['name'], p.get_name())
            self.assertEqual(entry['data']['type'], p.get_connector())
            self.assertEqual(entry['data']['speedrange'], p._allowed_speeds)

    def test_is_hardware(self):

        self.assertTrue(self.p.is_hardware())

    def test_set_speed_OK(self):
        speed = 100
        reason = 'config'

        result = self.p.set_speed(speed, reason)

        self.assertTrue(result)
        self.assertEqual(reason, self.p.get_speed_reason())

    def test_set_speed_Fail(self):
        speed = 10000

        result = self.p.set_speed(speed, 'Config')

        self.assertFalse(result)

    def test_get_speed_initial(self):

        result = self.p.get_speed()

        self.assertEqual(None, result)

    def test_get_speed_100(self):
        self.p.set_speed(100, 'Config')

        result = self.p.get_speed()

        self.assertEqual(100, result)

    def test_get_possible_speeds(self):
        possibleSpeeds = self.p1['data']['speedrange']

        result = self.p.get_possible_speeds()

        self.assertEqual(possibleSpeeds, result)

    def test_set_admin_state_enable(self):

        result = self.p.set_admin_state(True, 'config')

        self.assertTrue(result)

    def test_set_admin_state_disable(self):

        result = self.p.set_admin_state(False, None)

        self.assertFalse(result)

    def test_get_admin_state_unset(self):

        result = self.p.get_admin_state()

        self.assertIsNone(result)

    def test_get_admin_state_enabled(self):
        adminState = True
        reason = None
        self.p.set_admin_state(adminState, reason)

        result = self.p.get_admin_state()

        self.assertEqual(adminState, result)
        self.assertEqual(reason, self.p.get_admin_state_reason())

    def test_get_admin_state_disabled(self):
        adminState = False
        reason = 'Default'
        self.p.set_admin_state(adminState, reason)

        result = self.p.get_admin_state()

        self.assertEqual(adminState, result)
        self.assertEqual(reason, self.p.get_admin_state_reason())

    def test_set_auto_neg(self):
        self.assertTrue(self.p.set_auto_neg(1, 'Config'))
        self.assertTrue(self.p.set_auto_neg(True, 'Default'))
        self.assertTrue(self.p.set_auto_neg('Foo', None))
        self.assertFalse(self.p.set_auto_neg('', 'Applied'))
        self.assertFalse(self.p.set_auto_neg(0, 'Default'))
        self.assertFalse(self.p.set_auto_neg(False, 'default'))

    def test_get_auto_neg(self):
        autoNeg = True
        reason = 'Config'
        self.p.set_auto_neg(autoNeg, reason)

        result = self.p.get_auto_neg()

        self.assertEqual(autoNeg, result)
        self.assertEqual(reason, self.p.get_auto_neg_reason())

    def test_str(self):
        self.p.set_admin_state(False, 'applied')
        self.p.set_connector_used('sfp')
        entry = self.ports[0]
        entryData = entry['data']
        expected = 'label: ' + entry['label'] + ', '
        expected += 'name: ' + entry['name'] + ', '
        expected += 'type: ' + entryData['type']
        expected += '(sfp), '
        expected += 'speeds: ' + str(entryData['speedrange']) + ', '
        expected += 'PoE: ' + entryData['PoE'] + ', '
        expected += 'Alias: None, '
        expected += 'Admin State: False, '
        expected += 'Speed: None, '
        expected += 'Duplex: None, '
        expected += 'Auto-Negotiation: None, '
        expected += 'Jumbo: None, '
        expected += 'LACP: None, '
        expected += 'LACP Admin Actor Key: None, '
        expected += 'STP State: None, '
        expected += 'STP Auto Edge: None, '
        expected += 'STP Admin Edge: None, '
        expected += 'STP BPDU Guard: None, '
        expected += 'STP BPDU Guard Recovery Time: None, '
        expected += 'Inbound ACL: []'

        result = str(self.p)

        self.assertEqual(expected, result)

    def test_isEquivalent_connector_and_allowedSpeeds(self):
        mockPort = Mock(spec=Port)
        mockPort.get_possible_speeds.return_value = \
            self.p1['data']['speedrange']
        mockPort.get_connector.return_value = \
            self.p1['data']['type']

        result = self.p.is_equivalent(mockPort)

        self.assertTrue(result)

    def test_isEquivalent_usedConnector_and_allowedSpeeds_equal(self):
        mockPort = Mock(spec=Port)
        mockPort.get_possible_speeds.return_value = \
            self.p1['data']['speedrange']
        mockPort.get_connector_used.return_value = \
            self.p1['data']['type']

        result = self.p.is_equivalent(mockPort)

        self.assertTrue(result)

    def test_isEquivalent_usedConnector_and_maxOfAllowedSpeeds_equal(self):
        mockPort = Mock(spec=Port)
        mockPort.get_possible_speeds.return_value = [10, 1000]
        mockPort.get_connector_used.return_value = \
            self.p1['data']['type']

        result = self.p.is_equivalent(mockPort)

        self.assertTrue(result)

    def test_isEquivalent_fail_usedConnector_differ(self):
        mockPort = Mock(spec=Port)
        mockPort.get_possible_speeds.return_value = \
            self.p1['data']['speedrange']
        mockPort.get_connector_used.return_value = 'sfp'

        result = self.p.is_equivalent(mockPort)

        self.assertFalse(result)

    def test_set_connector_used(self):
        connector = 'sfp'

        result = self.p.set_connector_used(connector)

        self.assertEqual(connector, result)
        self.assertEqual(connector, self.p.get_connector_used())

    def test_set_duplex(self):
        duplex = 'half'
        reason = 'test'

        result = self.p.set_duplex(duplex, reason)

        self.assertEqual(duplex, result)
        self.assertEqual(duplex, self.p.get_duplex())
        self.assertEqual(reason, self.p.get_duplex_reason())

    def __setPorts(self, sP, tP, sReason, tReason):
        srcSpeed = 100
        tSpeed = 1000
        srcDuplex = 'half'
        tDuplex = 'full'
        srcAutoNeg = False
        tAutoNeg = True
        srcAdminState = False
        tAdminState = True
        srcDescr = 'source'
        tDescr = 'target'
        srcShDesc = 'src'
        tShDesc = 'tgt'
        srcJumbo = False
        tJumbo = True
        srcLacpEnabled = False
        tLacpEnabled = True
        srcLacpAadminkey = 1000
        tLacpAadminkey = 2000
        sP.set_speed(srcSpeed, sReason)
        tP.set_speed(tSpeed, tReason)
        sP.set_duplex(srcDuplex, sReason)
        tP.set_duplex(tDuplex, tReason)
        sP.set_auto_neg(srcAutoNeg, sReason)
        tP.set_auto_neg(tAutoNeg, tReason)
        sP.set_admin_state(srcAdminState, sReason)
        tP.set_admin_state(tAdminState, tReason)
        sP.set_description(srcDescr, sReason)
        tP.set_description(tDescr, tReason)
        sP.set_short_description(srcShDesc, sReason)
        tP.set_short_description(tShDesc, tReason)
        sP.set_jumbo(srcJumbo, sReason)
        tP.set_jumbo(tJumbo, tReason)
        sP.set_lacp_enabled(srcLacpEnabled, sReason)
        tP.set_lacp_enabled(tLacpEnabled, tReason)
        sP.set_lacp_aadminkey(srcLacpAadminkey, sReason)
        tP.set_lacp_aadminkey(tLacpAadminkey, tReason)

    def test_transfer_config(self):
        srcReason = 'default'
        tReason = 'init'
        reason_def = 'transfer_def'
        reason_conf = 'transfer_conf'
        srcSpeed = 100
        srcDuplex = 'half'
        srcAutoNeg = False
        srcAdminState = False
        srcDescr = 'source'
        srcShDesc = 'src'
        srcJumbo = False
        srcLacpEnabled = False
        srcLacpAadminkey = 1000

        sourcePort = self.p

        p2Data = {"type": "rj45", "speedrange": [10, 100, 1000],
                  "PoE": "yes"}
        p2Label = 1
        p2Name = '1'
        targetPort = Port(p2Name, p2Label, p2Data)

        self.__setPorts(sourcePort, targetPort, srcReason, tReason)

        targetPort.transfer_config(sourcePort)

        # speed
        self.assertEqual(srcSpeed, targetPort.get_speed())
        self.assertEqual(reason_def, targetPort.get_speed_reason())
        # duplex
        self.assertEqual(srcDuplex, targetPort.get_duplex())
        self.assertEqual(reason_def, targetPort.get_duplex_reason())
        # auto neg
        self.assertEqual(srcAutoNeg, targetPort.get_auto_neg())
        self.assertEqual(reason_def, targetPort.get_auto_neg_reason())
        # admin state
        self.assertEqual(srcAdminState, targetPort.get_admin_state())
        self.assertEqual(reason_def, targetPort.get_admin_state_reason())
        # description
        self.assertEqual(srcDescr, targetPort.get_description())
        self.assertEqual(reason_def, targetPort.get_description_reason())
        # short description
        self.assertEqual(srcShDesc, targetPort.get_short_description())
        self.assertEqual(reason_def, targetPort.get_short_description_reason())
        # jumbo frame
        self.assertEqual(srcJumbo, targetPort.get_jumbo())
        self.assertEqual(reason_def, targetPort.get_jumbo_reason())
        # lacp
        self.assertEqual(srcLacpEnabled, targetPort.get_lacp_enabled())
        self.assertEqual(reason_def, targetPort.get_lacp_enabled_reason())
        # lacp aadminkey
        self.assertEqual(srcLacpAadminkey, targetPort.get_lacp_aadminkey())
        self.assertEqual(reason_def, targetPort.get_lacp_aadminkey_reason())

        srcReason = 'init'
        self.__setPorts(sourcePort, targetPort, srcReason, tReason)

        targetPort.transfer_config(sourcePort)

        # speed
        self.assertEqual(srcSpeed, targetPort.get_speed())
        self.assertEqual(reason_conf, targetPort.get_speed_reason())
        # duplex
        self.assertEqual(srcDuplex, targetPort.get_duplex())
        self.assertEqual(reason_conf, targetPort.get_duplex_reason())
        # auto neg
        self.assertEqual(srcAutoNeg, targetPort.get_auto_neg())
        self.assertEqual(reason_conf, targetPort.get_auto_neg_reason())
        # admin state
        self.assertEqual(srcAdminState, targetPort.get_admin_state())
        self.assertEqual(reason_conf, targetPort.get_admin_state_reason())
        # description
        self.assertEqual(srcDescr, targetPort.get_description())
        self.assertEqual(reason_conf, targetPort.get_description_reason())
        # short description
        self.assertEqual(srcShDesc, targetPort.get_short_description())
        self.assertEqual(reason_conf,
                         targetPort.get_short_description_reason())
        # jumbo frame
        self.assertEqual(srcJumbo, targetPort.get_jumbo())
        self.assertEqual(reason_conf, targetPort.get_jumbo_reason())
        # lacp
        self.assertEqual(srcLacpEnabled, targetPort.get_lacp_enabled())
        self.assertEqual(reason_conf, targetPort.get_lacp_enabled_reason())
        # lacp aadminkey
        self.assertEqual(srcLacpAadminkey, targetPort.get_lacp_aadminkey())
        self.assertEqual(reason_conf, targetPort.get_lacp_aadminkey_reason())

    def test_set_get_description(self):
        description = 'Desc'
        reason = 'Default'

        result = self.p.set_description(description, reason)

        self.assertEqual(description, result)
        self.assertEqual(description, self.p.get_description())
        self.assertEqual(reason, self.p.get_description_reason())

    def test_set_get_short_description(self):
        description = 'desc'
        reason = 'Config'

        result = self.p.set_short_description(description, reason)

        self.assertEqual(description, result)
        self.assertEqual(description, self.p.get_short_description())
        self.assertEqual(reason, self.p.get_short_description_reason())

    def test_set_get_jumbo(self):
        jumbo = True
        reason = 'Transfer'

        result = self.p.set_jumbo(jumbo, reason)

        self.assertTrue(result)
        self.assertEqual(jumbo, self.p.get_jumbo())
        self.assertEqual(reason, self.p.get_jumbo_reason())

    def test_set_get_lacp_enabled(self):
        lacpEnabled = True
        reason = 'Config'

        result = self.p.set_lacp_enabled(lacpEnabled, reason)

        self.assertTrue(result)
        self.assertEqual(lacpEnabled, self.p.get_lacp_enabled())
        self.assertEqual(reason, self.p.get_lacp_enabled_reason())

    def test_set_get_lacp_aadminkey_ok(self):
        lacpAadminkey = 1000
        reason = 'Config'

        result = self.p.set_lacp_aadminkey(lacpAadminkey, reason)

        self.assertEqual(lacpAadminkey, result)
        self.assertEqual(lacpAadminkey, self.p.get_lacp_aadminkey())
        self.assertEqual(reason, self.p.get_lacp_aadminkey_reason())

    def test_set_lacp_aadminkey_fail_no_int(self):
        lacpAadminkey = 'foo'
        reason = 'Config'

        result = self.p.set_lacp_aadminkey(lacpAadminkey, reason)

        self.assertIsNone(result)
        self.assertIsNone(self.p.get_lacp_aadminkey())
        self.assertIsNone(self.p.get_lacp_aadminkey_reason())

    def test_set_lacp_aadminkey_fail_out_of_range(self):
        lacpAadminkey = 65536
        reason = 'Config'

        result = self.p.set_lacp_aadminkey(lacpAadminkey, reason)

        self.assertIsNone(result)
        self.assertIsNone(self.p.get_lacp_aadminkey())
        self.assertIsNone(self.p.get_lacp_aadminkey_reason())

    def test_is_configured_one_attribute(self):
        reason_config = 'config'
        dont_matter = 'dnm'

        result_attribute_conf_states_default = self.p.is_configured()

        self.p.set_admin_state(dont_matter, reason_config)

        result_one_attribute_is_configured = self.p.is_configured()

        self.assertFalse(result_attribute_conf_states_default)
        self.assertTrue(result_one_attribute_is_configured)

    def test_is_configured_two_attributes(self):
        reason_config = 'config'
        dont_matter = 'dnm'

        result_attribute_conf_states_default = self.p.is_configured()

        self.p.set_admin_state(dont_matter, reason_config)
        self.p.set_auto_neg(dont_matter, reason_config)

        result_two_attributes_are_configured = self.p.is_configured()

        self.assertFalse(result_attribute_conf_states_default)
        self.assertTrue(result_two_attributes_are_configured)

if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
