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

import STP


class STP_test(unittest.TestCase):

    def setUp(self):
        self.stp = STP.STP()

    def test_is_basic_stp_config_false(self):

        self.assertFalse(self.stp.is_basic_stp_config())

    def test_is_basic_stp_config_false_vlans_differ(self):
        self.stp.set_mst_cfgname('cfg', 'test')
        self.stp.set_mst_rev(0, 'test')
        self.stp.set_mst_instance(0, 'test')
        vlansTagLst = list(range(1, 4094))
        self.stp.add_vlans(vlansTagLst, 'test')

        self.assertFalse(self.stp.is_basic_stp_config())

    def test_is_basic_stp_config_true(self):
        self.stp.set_mst_cfgname(None, 'test')
        self.stp.set_mst_rev(0, 'test')
        self.stp.set_mst_instance(0, 'test')
        vlansTagLst = list(range(1, 4095))
        self.stp.add_vlans(vlansTagLst, 'test')

        self.assertTrue(self.stp.is_basic_stp_config())

    def test_is_enabled_default(self):

        self.assertFalse(self.stp.is_enabled())

    def test_set_is_enabled(self):
        state, reason = True, 'test_reason'

        result_set = self.stp.set_enabled(state, reason)
        result_get = self.stp.is_enabled()

        self.assertTrue(result_set)
        self.assertTrue(result_get)

    def test_get_enabled_reason(self):
        state, reason = False, 'test'

        result_set = self.stp.set_enabled(state, reason)
        result_get = self.stp.get_enabled_reason()

        self.assertFalse(result_set)
        self.assertEqual(reason, result_get)

    def test_set_get_name(self):
        name, reason = 'test', 'test_reason'

        result_set = self.stp.set_name(name, reason)
        result_get = self.stp.get_name()

        self.assertEqual(name, result_set)
        self.assertEqual(name, result_get)

    def test_get_name_reason(self):
        name, reason = 'test', 'test_reason'

        result_set = self.stp.set_name(name, reason)
        result_get = self.stp.get_name_reason()

        self.assertEqual(name, result_set)
        self.assertEqual(reason, result_get)

    def test_set_get_version(self):
        version, reason = '1.0', 'test_reason'

        result_set = self.stp.set_version(version, reason)
        result_get = self.stp.get_version()

        self.assertEqual(version, result_set)
        self.assertEqual(version, result_get)

    def test_get_version_reason(self):
        version, reason = '1.0', 'test_reason'

        result_set = self.stp.set_version(version, reason)
        result_get = self.stp.get_version_reason()

        self.assertEqual(version, result_set)
        self.assertEqual(reason, result_get)

    def test_set_get_priority(self):
        prio, reason = 1, 'test_reason'

        result_set = self.stp.set_priority(str(prio), reason)
        result_get = self.stp.get_priority()

        self.assertEqual(prio, result_set)
        self.assertEqual(prio, result_get)

    def test_get_priority_reason(self):
        prio, reason = 1, 'test_reason'

        result_set = self.stp.set_priority(prio, reason)
        result_get = self.stp.get_priority_reason()

        self.assertEqual(prio, result_set)
        self.assertEqual(reason, result_get)

    def test_set_priority_not_int(self):
        prio, reason = 'a', 'test_reason'

        result_set = self.stp.set_priority(prio, reason)
        result_get = self.stp.get_priority_reason()

        self.assertIsNone(result_set)
        self.assertIsNone(result_get)
        self.assertIsNone(self.stp.get_priority_reason())

    def test_set_priority_out_of_bounds(self):
        prio_lower_bound, reason = 0, 'test_reason'
        prio_upper_bound, reason = 65535, 'test_reason'

        result_set_too_high = self.stp.set_priority(prio_upper_bound + 1,
                                                    reason)
        result_set_too_low = self.stp.set_priority(prio_lower_bound - 1,
                                                   reason)
        self.assertIsNone(result_set_too_high)
        self.assertIsNone(result_set_too_low)
        self.assertIsNone(self.stp.get_priority_reason())

    def test_set_get_mst_cfgname(self):
        mst_name, reason = 'mst1', 'test_reason'

        result_set = self.stp.set_mst_cfgname(mst_name, reason)
        result_get = self.stp.get_mst_cfgname()

        self.assertEqual(mst_name, result_set)
        self.assertEqual(mst_name, result_get)

    def test_get_mst_cfgname_reason(self):
        mst_name, reason = 'mst1', 'test_reason'

        result_set = self.stp.set_mst_cfgname(mst_name, reason)
        result_get = self.stp.get_mst_cfgname_reason()

        self.assertEqual(mst_name, result_set)
        self.assertEqual(reason, result_get)

    def test_set_get_mst_rev(self):
        mst_rev, reason = '1', 'test_reason'

        result_set = self.stp.set_mst_rev(mst_rev, reason)
        result_get = self.stp.get_mst_rev()

        self.assertEqual(int(mst_rev), result_set)
        self.assertEqual(int(mst_rev), result_get)

    def test_set_get_mst_rev_int(self):
        mst_rev, reason = 1, 'test_reason'

        result_set = self.stp.set_mst_rev(mst_rev, reason)
        result_get = self.stp.get_mst_rev()

        self.assertEqual(mst_rev, result_set)
        self.assertEqual(mst_rev, result_get)

    def test_set_mst_rev_fail_no_int(self):
        mst_rev, reason = 'a', 'test_reason'
        expected = None

        result_set = self.stp.set_mst_rev(mst_rev, reason)
        result_get = self.stp.get_mst_rev()

        self.assertEqual(expected, result_set)
        self.assertEqual(expected, result_get)

    def test_get_mst_rev_reason(self):
        mst_rev, reason = '1', 'test_reason'

        result_set = self.stp.set_mst_rev(mst_rev, reason)
        result_get = self.stp.get_mst_rev_reason()

        self.assertEqual(int(mst_rev), result_set)
        self.assertEqual(reason, result_get)

    def test_set_get_mst_instance(self):
        mst_inst, reason = '1', 'test_reason'

        result_set = self.stp.set_mst_instance(mst_inst, reason)
        result_get = self.stp.get_mst_instance()

        self.assertEqual(int(mst_inst), result_set)
        self.assertEqual(int(mst_inst), result_get)

    def test_set_get_mst_instance_int(self):
        mst_inst, reason = 1, 'test_reason'

        result_set = self.stp.set_mst_instance(mst_inst, reason)
        result_get = self.stp.get_mst_instance()

        self.assertEqual(mst_inst, result_set)
        self.assertEqual(mst_inst, result_get)

    def test_set_mst_instance_fail_no_int(self):
        mst_inst, reason = 'a', 'test_reason'
        expected = None

        result_set = self.stp.set_mst_instance(mst_inst, reason)
        result_get = self.stp.get_mst_instance()

        self.assertEqual(expected, result_set)
        self.assertEqual(expected, result_get)

    def test_get_mst_instance_reason(self):
        mst_inst, reason = '1', 'test'

        result_set = self.stp.set_mst_instance(mst_inst, reason)
        result_get = self.stp.get_mst_instance_reason()

        self.assertEqual(int(mst_inst), result_set)
        self.assertEqual(reason, result_get)

    def test_get_vlans_default(self):
        expected = []

        result = self.stp.get_vlans()

        self.assertEqual(expected, result)

    def test_add_vlan(self):
        vlanTag, reason = 1, 'test_reason'
        expectedLen = 1

        self.stp.add_vlan(vlanTag, reason)
        result = self.stp.get_vlans()

        self.assertEqual(expectedLen, len(result))

    def test_add_vlan_already_present(self):
        vlanTag, reason = 1, 'test_reason'
        self.stp.add_vlan(vlanTag, reason)
        expectedLen = 1

        self.stp.add_vlan(vlanTag, reason)
        result = self.stp.get_vlans()

        self.assertEqual(expectedLen, len(result))

    def test_add_vlans(self):
        reason = 'test_reason'
        vlanTagLst = [1, 2, 3]
        expectedLen = 3

        self.stp.add_vlans(vlanTagLst, reason)
        result = self.stp.get_vlans()

        self.assertEqual(expectedLen, len(result))

    def test_add_vlans_vlan_already_present(self):
        reason = 'test_reason'
        vlanTagLst = [1, 2, 3, 1, 3]
        expectedLen = 3

        self.stp.add_vlans(vlanTagLst, reason)
        result = self.stp.get_vlans()

        self.assertEqual(expectedLen, len(result))

    def test_get_vlans_reason(self):
        reason = 'test'
        vlanTagLst = [1, 2, 3]
        self.stp.add_vlans(vlanTagLst, reason)

        result = self.stp.get_vlans_reason()

        self.assertEqual(reason, result)

    def test_del_vlan_not_present(self):
        reason = 'test'
        vlanTagList = [1, 2, 3]
        self.stp.add_vlans(vlanTagList, reason)
        expectedLen = len(self.stp.get_vlans())

        self.stp.del_vlan(4, reason)

        self.assertEqual(expectedLen, len(self.stp.get_vlans()))

    def test_del_vlan(self):
        reason = 'test'
        vlanTagList = [1, 2, 3]
        self.stp.add_vlans(vlanTagList, reason)
        expectedLen = len(self.stp.get_vlans()) - 1
        expectedVlans = [1, 2]

        self.stp.del_vlan(3, reason)

        vlans = self.stp.get_vlans()
        self.assertEqual(expectedLen, len(vlans))
        self.assertEqual(expectedVlans, vlans)

    def test_del_vlans(self):
        reason = 'test'
        vlanTagLst = [1, 2, 3]
        vlanTagLst2Del = [2, 3]
        self.stp.add_vlans(vlanTagLst, reason)
        expectedLen = len(vlanTagLst) - len(vlanTagLst2Del)
        expectedVlans = [1]

        self.stp.del_vlans(vlanTagLst2Del, reason)

        vlans = self.stp.get_vlans()
        self.assertEqual(expectedVlans, vlans)
        self.assertEqual(expectedLen, len(vlans))

    def _is_default_stp(self, stp):
        default_stp = STP.STP()

        return stp == default_stp

    def _set_stp_attributes_with_reason(self, stp, reason):
        stp.set_name('a', reason)
        stp.set_enabled(True, reason)
        stp.set_version(1, reason)
        stp.set_priority(1, reason)
        stp.set_mst_instance(1, reason)
        stp.set_mst_cfgname('mst1', reason)
        stp.set_mst_rev('1', reason)
        stp.set_mst_instance(1, reason)
        stp.add_vlans([1], reason)

    def _is_reason_of_attributes_in_list_set_to(self, obj, attrLst, reason):
        ret = True
        for attrName in attrLst:
            attr = getattr(obj, attrName)
            if attr[1] != reason:
                return False
        return ret

    def test_transfer_config_from_default_stp(self):
        fromStp = STP.STP()

        self.stp.transfer_config(fromStp)

        self.assertTrue(self._is_default_stp(self.stp))

    def test_transfer_config_from_stp_which_is_configured(self):
        fromStp = STP.STP()
        self._set_stp_attributes_with_reason(fromStp, 'config')
        attrLst = self.stp.__dict__.keys()

        self.stp.transfer_config(fromStp)

        self.assertTrue(
            self._is_reason_of_attributes_in_list_set_to(self.stp,
                                                         attrLst,
                                                         'transfer_conf'))

    def test_transfer_config_from_stp_which_is_default(self):
        fromStp = STP.STP()
        self._set_stp_attributes_with_reason(fromStp, 'default')
        attrLst = self.stp.__dict__.keys()

        self.stp.transfer_config(fromStp)

        self.assertTrue(
            self._is_reason_of_attributes_in_list_set_to(self.stp,
                                                         attrLst,
                                                         'transfer_def'))

if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
