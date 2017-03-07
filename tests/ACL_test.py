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

from ACL import ACL
from ACL import ACE


class ACL_test(unittest.TestCase):

    def setUp(self):
        self.acl = ACL()

    def test_constructorWithOutArguments(self):

        self.assertEqual(None, self.acl._number)
        self.assertEqual(None, self.acl._name)

    def test_constructorWithArguments(self):
        self.acl = ACL(number=1, name='test')

        self.assertEqual(1, self.acl._number)
        self.assertEqual('test', self.acl._name)

    def test_constructorWithIllegalNumber_illegalNumberIsIgnored(self):
        acl = ACL(number=-1)

        self.assertEqual(None, acl._number)

    def test_set_number_ValidStringsAreAccepted(self):

        self.assertEqual(1, self.acl.set_number("1"))

    def test_set_number_NaNStringsAreRejected(self):

        self.assertEqual(None, self.acl.set_number("xxx"))

    def test_set_number_illegalNumberDoesntChangeAssignedNumber(self):
        acl = ACL(number=1)

        self.assertEqual(1, acl.set_number("-1"))

    def test_add_ace_invalidTypesAreRejected(self):
        nrOfAces = len(self.acl._entries)

        self.acl.add_ace(ACL())

        self.assertEqual(nrOfAces, len(self.acl._entries))

    def test_add_ace_validAce(self):
        ace = ACE()

        nrOfAces = len(self.acl._entries)

        self.acl.add_ace(ace)

        self.assertEqual(nrOfAces + 1, len(self.acl._entries))

    class MockAce(ACE):
        def __init__(self, result):
            super().__init__()
            self.result = result

        def is_standard(self):
            return self.result

    def test_is_standard_shouldFail(self):
        self.acl.add_ace(self.MockAce(True))
        self.acl.add_ace(self.MockAce(False))
        self.acl.add_ace(self.MockAce(True))

        self.assertFalse(self.acl.is_standard())

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
        acl1 = ACL(number=1, name='test')
        acl2 = ACL(number=1, name='test')
        acl1.add_ace(ace1)
        acl2.add_ace(ace2)

        self.assertEqual(acl1, acl1)
        self.assertEqual(acl1, acl2)
        self.assertEqual(acl2, acl1)

    def test_equality_shouldNotBeEqual(self):
        acl1 = ACL(number=1, name='Test')
        acl2 = ACL(number=1, name='test')
        acl3 = ACL(number=1, name='test')
        ace1 = ACE(action='permit')
        ace2 = ACE(action='deny')
        acl1.add_ace(ace1)
        acl2.add_ace(ace1)
        acl3.add_ace(ace2)

        self.assertNotEqual(acl1, acl2)
        self.assertNotEqual(acl2, acl1)
        self.assertNotEqual(acl2, acl3)

    def test_add_ace_nonExistingAceShouldBeAdded(self):
        ace = ACE(action='deny')
        nr_of_aces = len(self.acl.get_entries())

        self.acl.add_ace(ace)

        self.assertEqual(nr_of_aces + 1, len(self.acl.get_entries()))

    def test_add_ace_alreadyExistingAceShouldBeSilentlyDropped(self):
        ace = ACE(action='deny')
        self.acl.add_ace(ace)

        nr_of_aces = len(self.acl.get_entries())

        self.acl.add_ace(ace)

        self.assertEqual(nr_of_aces, len(self.acl.get_entries()))

    def test_is_supported_type_shouldFail(self):

        self.assertFalse(self.acl.is_supported_type('mac'))

if __name__ == '__main__':
    unittest.main()


# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
