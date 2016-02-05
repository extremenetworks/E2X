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

# Copyright 2014-2016 Extreme Networks, Inc.  All rights reserved.
# Use is subject to license terms.

# This file is part of e2x (translate EOS switch configuration to ExtremeXOS)

import unittest
import sys
sys.path.extend(['../src'])

from EOS_read import EosNumberedAclLineParser, EosAclParseError
from ACL import ACL, Standard_ACE, ACE
from ipaddress import IPv4Address


class EosNumberedAclParser_test(unittest.TestCase):

    def setUp(self):
        self.parser = EosNumberedAclLineParser()

    def test_create_acl_aclNameShouldThrowException(self):
        token_list = 'inter'.split()

        self.assertRaisesRegex(EosAclParseError, "^ERROR:.* numbered.*$",
                               self.parser.create_acl, token_list)

    def test_create_acl_aclNumberOutOfRangeShouldThrowException(self):
        lower_boundary, upper_boundary = 1, 399

        self.assertRaisesRegex(EosAclParseError, "^ERROR: ACL number.*$",
                               self.parser.create_acl,
                               str(lower_boundary - 1).split())
        self.assertRaisesRegex(EosAclParseError, "^ERROR: ACL number.*$",
                               self.parser.create_acl,
                               str(upper_boundary + 1).split())

    def test_create_acl_emptyAceConfigShouldThrowException(self):
        token_list = '1'.split()

        self.assertRaisesRegex(EosAclParseError,
                               "^ERROR: Empty ACE configuration.*$",
                               self.parser.create_acl, token_list)

    def test_create_acl_invalidActionShouldThrowException(self):
        token_list = '1 invalid'.split()

        self.assertRaisesRegex(EosAclParseError,
                               "^ERROR: Invalid ACE action.*$",
                               self.parser.create_acl, token_list)

    def test_create_acl_stdAclWithNoSourceShouldThrowException(self):
        token_list = '1 permit'.split()

        self.assertRaisesRegex(EosAclParseError,
                               "^ERROR: Address definition missing in ACE "
                               "config.*$",
                               self.parser.create_acl, token_list)

    def test_create_acl_stdAclWithInvalidSourceAddressShouldThrow(self):
        token_list = '1 permit unknown'.split()

        self.assertRaisesRegex(EosAclParseError,
                               "^ERROR: Invalid address in ACE "
                               "config.*$",
                               self.parser.create_acl, token_list)

    def test_create_acl_aclWithMissingParameterShouldThrowException(self):
        token_list = '1 permit host'.split()

        self.assertRaisesRegex(EosAclParseError,
                               "^ERROR: Missing address parameter in ACE "
                               "config.*$",
                               self.parser.create_acl, token_list)

    def test_create_acl_stdAclsShouldSucceed(self):
        exp_ace1 = Standard_ACE(action='permit')
        exp_ace1.set_source('192.168.0.1')
        exp_ace1.set_source_mask('0.0.0.0')
        exp_ace2 = Standard_ACE(action='permit')
        exp_ace2.set_source('0.0.0.0')
        exp_ace2.set_source_mask('255.255.255.255')
        exp_acl1 = ACL(number=1)
        exp_acl1.add_ace(exp_ace1)
        exp_acl2 = ACL(number=99)
        exp_acl2.add_ace(exp_ace2)
        token_list1 = '1 permit host 192.168.0.1'.split()
        token_list2 = '1 permit 192.168.0.1 0.0.0.0'.split()
        token_list3 = '1 permit 192.168.0.1'.split()
        token_list4 = '99 permit any'.split()

        self.assertEqual(exp_acl1, self.parser.create_acl(token_list1))
        self.assertEqual(exp_acl1, self.parser.create_acl(token_list2))
        self.assertEqual(exp_acl1, self.parser.create_acl(token_list3))
        self.assertEqual(exp_acl2, self.parser.create_acl(token_list4))

    def test_create_acl_stdAclWithModifiers(self):
        token_list = '1 permit any assign-queue 0'.split()

        acl = self.parser.create_acl(token_list)

        self.assertEqual('assign-queue 0', acl.get_surplus_params())

    def test_create_acl_extAclWithTooFewParametersShouldThrowException(self):
        token_list = '100 permit ip any'.split()

        self.assertRaisesRegex(EosAclParseError,
                               "^ERROR: Extended ACEs need protocol, source "
                               "and destination.*$",
                               self.parser.create_acl, token_list)

    def test_create_acl_extAclWithWrongProtocolShouldThrowException(self):
        token_list = '100 permit unknown any any'.split()

        self.assertRaisesRegex(EosAclParseError,
                               "^ERROR: Unsupported ACE protocol.*$",
                               self.parser.create_acl, token_list)

    def test_create_acl_extAclWithInvalidSourceAddressShouldThrow(self):
        token_list = '100 deny ip unknown any'.split()

        self.assertRaisesRegex(EosAclParseError,
                               "^src: ERROR: Invalid address in ACE"
                               " config.*$",
                               self.parser.create_acl, token_list)

    def test_create_acl_extAclWithIncompleteSrcAddressShouldThrow(self):
        token_list = '100 deny ip host any'.split()

        self.assertRaisesRegex(EosAclParseError,
                               "^src: ERROR: Missing address parameter in ACE"
                               " config.*$",
                               self.parser.create_acl, token_list)

    def test_create_acl_extAclWithMissingSrcPortShouldThrowException(self):
        token_list = '100 deny ip host 10.0.0.1 eq any'.split()

        self.assertRaisesRegex(EosAclParseError,
                               "^src: ERROR: Invalid port definition in ACE"
                               " config.*$",
                               self.parser.create_acl, token_list)

    def test_create_acl_extAclWithInvalidDestinationAddressShouldThrow(self):
        token_list = '100 deny ip any unknown'.split()

        self.assertRaisesRegex(EosAclParseError,
                               "^dest: ERROR: Invalid address in ACE"
                               " config.*$",
                               self.parser.create_acl, token_list)

    def test_create_acl_extAclWithIncompleteDestAddressShouldThrow(self):
        token_list = '100 deny ip any host'.split()

        self.assertRaisesRegex(EosAclParseError,
                               "^dest: ERROR: Missing address parameter in ACE"
                               " config.*$",
                               self.parser.create_acl, token_list)

    def test_create_acl_extAclWithMissingDestPortShouldThrowException(self):
        token_list = '100 deny ip host 10.0.0.1 any eq'.split()

        self.assertRaisesRegex(EosAclParseError,
                               "^dest: ERROR: Missing port definition in ACE"
                               " config.*$",
                               self.parser.create_acl, token_list)

    def test_create_acl_extAclWithInvalidDestPortShouldThrowException(self):
        token_list = '100 deny ip host 10.0.0.1 any eq unknown'.split()

        self.assertRaisesRegex(EosAclParseError,
                               "^dest: ERROR: Invalid port definition in ACE"
                               " config.*$",
                               self.parser.create_acl, token_list)

    def test_create_acl_extAclsShouldSucceed(self):
        token_list1 = '100 deny ip host 192.0.2.1 any'.split()
        token_list2 = \
            '100 deny ip 192.0.2.1 0.0.0.0 0.0.0.0 255.255.255.255'.split()
        exp_ace1 = ACE(action='deny', protocol='ip',
                       source=IPv4Address('192.0.2.1'),
                       source_mask=IPv4Address('0.0.0.0'),
                       dest=IPv4Address('0.0.0.0'),
                       dest_mask=IPv4Address('255.255.255.255'))
        exp_acl1 = ACL(number=100)
        exp_acl1.add_ace(exp_ace1)
        token_list3 = '399 permit 7 any any'.split()
        token_list4 = '399 permit tcp any any'.split()
        token_list5 = '399 permit tcp any eq 80 any'.split()
        token_list6 = '399 permit tcp any eq 80 any eq 23'.split()
        exp_ace2 = ACE(action='permit', protocol='tcp',
                       source=IPv4Address('0.0.0.0'),
                       source_mask=IPv4Address('255.255.255.255'),
                       dest=IPv4Address('0.0.0.0'),
                       dest_mask=IPv4Address('255.255.255.255'))
        exp_acl2 = ACL(number=399)
        exp_acl2.add_ace(exp_ace2)

        self.assertEqual(exp_acl1, self.parser.create_acl(token_list1))
        self.assertEqual(exp_acl1, self.parser.create_acl(token_list2))
        exp_ace2.set_protocol('7')
        self.assertEqual(exp_acl2, self.parser.create_acl(token_list3))
        exp_ace2.set_protocol('tcp')
        self.assertEqual(exp_acl2, self.parser.create_acl(token_list4))
        exp_ace2.set_source_op('eq')
        exp_ace2.set_source_port('80')
        self.assertEqual(exp_acl2, self.parser.create_acl(token_list5))
        exp_ace2.set_dest_op('eq')
        exp_ace2.set_dest_port('23')
        self.assertEqual(exp_acl2, self.parser.create_acl(token_list6))

    def test_create_acl_extAclWithModifiers(self):
        token_list = \
            '100 permit ip host 192.0.2.1 eq 23 0.0.0.0 255.255.255.255 ' \
            'eq 80 precedence 1 assign-queue 0'.split()

        acl = self.parser.create_acl(token_list)

        self.assertEqual('precedence 1 assign-queue 0',
                         acl.get_surplus_params())

if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
