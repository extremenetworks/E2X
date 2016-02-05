# CDDL HEADER START
#
# The contents of this file are subject to the terms
# of the Common Development and Distribution License
# (the 'License').  You may not use this file except
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
# fields enclosed by brackets '[]' replaced with your
# own identifying information: Portions Copyright [yyyy]
# [name of copyright owner]
#
# CDDL HEADER END

# Copyright 2014-2016 Extreme Networks, Inc.  All rights reserved.
# Use is subject to license terms.

# This file is part of e2x (translate EOS switch configuration to ExtremeXOS)

import unittest

import sys
sys.path.extend(['../src'])

from ipaddress import IPv4Address

from ACL import ACE, Standard_ACE


class ACE_test(unittest.TestCase):

    def setUp(self):
        self.ace = ACE()

    def test_constructorWithNoArguments(self):
        ace = ACE()

        self.assertEqual(None, ace._number)

    def test_constructorWithNegativeNumber_negativeNumberIsIgnored(self):
        ace = ACE(number=-1)

        self.assertEqual(None, ace._number)

    def test_set_number_ValidStringsAreAccepted(self):

        self.assertEqual(1, self.ace.set_number('1'))

    def test_set_number_NaNStringsAreRejected(self):

        self.assertEqual(None, self.ace.set_number('xxx'))

    def test_set_number_negativeNumberDoesntChangeAssignedNumber(self):
        ace = ACE(number=1)

        self.assertEqual(1, ace.set_number('-1'))

    def test_set_action_validAction(self):
        self.assertEqual('permit', self.ace.set_action('permit'))
        self.assertEqual('deny', self.ace.set_action('deny'))

    def test_set_action_illegalActionDoesntChangeOldValue(self):

        self.assertEqual(None, self.ace.set_action('Unknown'))

    def test_set_protocol_validProtocol(self):

        self.assertEqual('ip', self.ace.set_protocol('ip'))
        self.assertEqual('udp', self.ace.set_protocol('udp'))
        self.assertEqual('tcp', self.ace.set_protocol('tcp'))
        self.assertEqual('icmp', self.ace.set_protocol('icmp'))
        self.assertEqual('igmp', self.ace.set_protocol('igmp'))
        self.assertEqual('0', self.ace.set_protocol('0'))
        self.assertEqual('127', self.ace.set_protocol('0x7F'))
        self.assertEqual('171', self.ace.set_protocol('0xAb'))
        self.assertEqual('255', self.ace.set_protocol('0xff'))

    def test_set_protocol_illegalProtocolDoesntChangeOldValue(self):

        self.assertEqual(None, self.ace.set_protocol('unknown'))

    def test_set_protocol_protocolNrOutOfRangeDoesntChangeOldValue(self):
        upper_limit = 255
        lower_limit = 0
        self.ace.set_protocol('icmp')

        self.assertEqual('icmp', self.ace.set_protocol(upper_limit + 1))
        self.assertEqual('icmp', self.ace.set_protocol(lower_limit - 1))

    def test_set_source_validAddress(self):

        self.assertEqual(IPv4Address('192.168.0.1'),
                         self.ace.set_source('192.168.0.1'))

    def test_set_source_invalidAddressDoesntChangeOldValue(self):
        ip = IPv4Address('192.168.0.1')
        ace = ACE(source=ip)

        self.assertEqual(ip, ace.set_source(':::1'))

    def test_set_source_mask_validAddress(self):

        self.assertEqual(IPv4Address('192.168.0.1'),
                         self.ace.set_source_mask('192.168.0.1'))

    def test_set_source_mask_invalidAddressDoesntChangeOldValue(self):
        ip = IPv4Address('192.168.0.1')
        ace = ACE(source_mask=ip)

        self.assertEqual(ip, ace.set_source_mask(':::1'))

    def test_set_source_op_validOp(self):

        self.assertEqual('eq', self.ace.set_source_op('eq'))

    def test_set_source_op_illegalOpDoesntChangeOldValue(self):

        self.assertEqual(None, self.ace.set_source_op('unknown'))

    def test_set_source_port_validPortNumber(self):

        self.assertEqual('1234', self.ace.set_source_port('1234'))

    def test_set_source_port_valueOutOfRange(self):
        upper_limit = 65535
        lower_limit = 0

        self.assertEqual(None, self.ace.set_source_port(str(upper_limit + 1)))
        self.assertEqual(None, self.ace.set_source_port(str(lower_limit - 1)))

    def test_set_dest_validAddress(self):

        self.assertEqual(IPv4Address('192.168.0.1'),
                         self.ace.set_dest('192.168.0.1'))

    def test_set_dest_invalidAddressDoesntChangeOldValue(self):
        ip = IPv4Address('192.168.0.1')
        ace = ACE(dest=ip)

        self.assertEqual(ip, ace.set_dest(':::1'))

    def test_set_dest_mask_validAddress(self):

        self.assertEqual(IPv4Address('192.168.0.1'),
                         self.ace.set_dest_mask('192.168.0.1'))

    def test_set_dest_mask_invalidAddressDoesntChangeOldValue(self):
        ip = IPv4Address('192.168.0.1')
        ace = ACE(dest_mask=ip)

        self.assertEqual(ip, ace.set_dest_mask(':::1'))

    def test_set_dest_op_validOp(self):

        self.assertEqual('eq', self.ace.set_dest_op('eq'))

    def test_set_dest_op_illegalOpDoesntChangeOldValue(self):

        self.assertEqual(None, self.ace.set_dest_op('unknown'))

    def test_set_dest_port_validPortNumber(self):

        self.assertEqual('1234', self.ace.set_dest_port('1234'))

    def test_set_dest_port_valueOutOfRange(self):
        upper_limit = 65535
        lower_limit = 0

        self.assertEqual(None, self.ace.set_dest_port(str(upper_limit + 1)))
        self.assertEqual(None, self.ace.set_dest_port(str(lower_limit - 1)))

    def test_is_standard_shouldReturnTrue(self):
        ace = ACE(protocol='ip')

        self.assertTrue(ace.is_standard())

    def test_is_standard_shouldReturnFalse(self):
        self.ace.set_source_op('eq')   # ||
        self.ace.set_dest_op(('eq'))   # ||
        self.ace.set_dest_port('0')    # ||
        self.ace.set_source_port('0')  # ||
        self.ace.set_dest('192.168.0.1')

        self.assertFalse(self.ace.is_standard())

    def test_get_source_mask_inverted_ok(self):
        masks = ('0.0.0.0', '255.255.255.255', '170.85.170.85')
        expected = (IPv4Address('255.255.255.255'),
                    IPv4Address('0.0.0.0'),
                    IPv4Address('85.170.85.170'))

        for mask in masks:
            index = masks.index(mask)
            self.ace.set_source_mask(mask)

            result = self.ace.get_source_mask_inverted()

            self.assertEqual(expected[index], result)

    def test_get_source_mask_inverted_sourceMaskNotSet(self):

        self.assertIsNone(self.ace.get_source_mask())

    def test_get_dest_mask_inverted_ok(self):
        masks = ('0.0.0.0', '255.255.255.255', '170.85.170.85')
        expected = (IPv4Address('255.255.255.255'),
                    IPv4Address('0.0.0.0'),
                    IPv4Address('85.170.85.170'))

        for mask in masks:
            index = masks.index(mask)
            self.ace.set_dest_mask(mask)

            result = self.ace.get_dest_mask_inverted()

            self.assertEqual(expected[index], result)

    def test_get_dest_mask_inverted_destMaskNotSet(self):

        self.assertIsNone(self.ace.get_dest_mask_inverted())

    def test_is_valid_ip_shouldFail(self):

        self.assertFalse(ACE.is_valid_ip_address('::1'))

    def test_equality_shouldBeEqual(self):
        ace1 = ACE(action='deny')
        ace1.set_source('0.0.0.0')
        ace1.set_source_mask('255.255.255.255')
        ace1.set_dest('192.168.1.2')
        ace1.set_dest_mask('255.255.255.255')
        ace2 = ACE(action='deny')
        ace2.set_source('0.0.0.0')
        ace2.set_source_mask('255.255.255.255')
        ace2.set_dest('192.168.1.2')
        ace2.set_dest_mask('255.255.255.255')

        self.assertEqual(ace1, ace2)
        self.assertEqual(ace2, ace1)

    def test_equality_shouldNotBeEqual(self):
        ace1 = ACE(action='deny')
        ace2 = ACE(action='permit')

        self.assertNotEqual(ace1, ace2)
        self.assertNotEqual(ace2, ace1)

    def test_equality_stdAcesShouldBeEqual(self):
        ace1 = Standard_ACE()
        ace2 = ACE(protocol='ip')

        self.assertEqual(ace1, ace2)

if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
