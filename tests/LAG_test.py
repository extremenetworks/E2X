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

import LAG


class LAG_test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.lagLabel = '1'

    def setUp(self):
        self.lag = LAG.LAG(self.lagLabel)

    def test_str(self):
        expected = 'Number: ' + self.lagLabel
        expected += ', Name: None'
        expected += ', LACP: None'
        expected += ', Actor Admin Key: None'
        expected += ', Alias: None'
        expected += ', Admin State: None'

        self.assertEqual(expected, str(self.lag))

    def test_is_disabled_only(self):
        reason_config, other_reason = 'config', 'test'
        does_not_matter = 'dnm'
        self.lag.set_admin_state(False, reason_config)
        self.lag.set_description(does_not_matter, other_reason)
        self.lag.set_short_description(does_not_matter, other_reason)
        self.lag.set_lacp_enabled(does_not_matter, other_reason)
        self.lag.set_lacp_aadminkey(does_not_matter, other_reason)

        self.assertTrue(self.lag.is_disabled_only())

    def test_set_speed(self):

        self.assertTrue(self.lag.set_speed(100, 'test'))

    def test_set_duplex(self):

        self.assertIsNone(self.lag.set_duplex('half', 'test'))

    def test_set_auto_neg(self):

        self.assertIsNone(self.lag.set_auto_neg('on', 'test'))

    def test_set_jumbo(self):

        self.assertIsNone(self.lag.set_jumbo('on', 'test'))

    def test_get_members(self):

        self.assertEqual([], self.lag.get_members())

    def test_add_member_port_fail(self):

        self.assertFalse(self.lag.add_member_port(''))

    def test_add_member_port_ok(self):
        portName = 'p1'

        self.assertTrue(self.lag.add_member_port(portName))
        self.assertEqual(portName, self.lag.get_master_port())

    def test_get_master_port(self):
        ports = ['p1', 'p2', 'p3']
        for p in ports:
            self.lag.add_member_port(p)

        self.assertEqual(ports[0], self.lag.get_master_port())

if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
