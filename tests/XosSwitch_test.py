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

from unittest.mock import Mock, call

import XOS
from Port import Port
from VLAN import VLAN


class XosSwitch_test(unittest.TestCase):

    def setUp(self):
        self.sw = XOS.XosSwitch()

    def test_build_port_name_is_stack(self):
        self.sw.set_stack(True)
        sep = self.sw._sep
        label = 1
        slot = 1
        expected = str(slot) + sep + str(label)

        result = self.sw._build_port_name(1, {}, slot)

        self.assertEqual(expected, result)

    def test_build_port_name_is_not_a_stack(self):
        label = 1
        slot = 1
        expected = str(label)

        result = self.sw._build_port_name(1, {}, slot)

        self.assertEqual(expected, result)

    def test_apply_default_settings(self):
        mockPort = Mock(spec=Port)
        self.sw._ports.append(mockPort)
        mockVlan = Mock(spec=VLAN)
        mockVlan.get_tag.return_value = 1
        self.sw._vlans.append((mockVlan))

        self.sw.apply_default_settings()

        methodCalls = [call.set_auto_neg(True, 'default'),
                       call.set_admin_state(True, 'default'),
                       call.set_jumbo(False, 'default'),
                       call.set_lacp_enabled(False, 'default'),
                       call.set_stp_edge(False, 'default'),
                       call.set_stp_bpdu_guard(False, 'default'),
                       call.set_stp_bpdu_guard_recovery_time(300, 'default'),
                       ]

        self.assertEqual(methodCalls, mockPort.method_calls)
        mockVlan.set_name.assert_called_with('Default', True)


if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
