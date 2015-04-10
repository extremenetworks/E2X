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

from unittest.mock import MagicMock

import Port
import Switch
import STP


class ConfigWriter_test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.mockPort = MagicMock(spec=Port.Port)
        cls.mockPort.get_name.return_value = 'ge.1.1'

        cls.mockSwitch = MagicMock(spec=Switch.Switch)
        cls.mockSwitch.get_ports_by_name.return_value = [cls.mockPort]
#        cls.mockSwitch.get_ports.return_value = [cls.mockPort]

        cls.omitStr = ', but omitted from configuration file'

        cls.ErrorStart = 'ERROR: '
        cls.NoticeStart = 'NOTICE: '
        cls.WarningStart = 'WARN: '

    def setUp(self):
        self.cw = Switch.ConfigWriter(self.mockSwitch)

    def test_check_unwritten(self):
        self.mockSwitch.get_ports.return_value = [self.mockPort]
        reason = 'transfer_conf'
        warnStr = self.WarningStart + '{}'

        # port speed
        self.mockPort.get_speed_reason.return_value = reason
        self.mockPort.get_speed.return_value = 100

        result = self.cw.check_unwritten()

        self.assertTrue(result[0].startswith(warnStr.format('Speed of')))

        # port duplex
        self.mockPort.get_duplex_reason.return_value = reason
        self.mockPort.get_duplex.return_value = 'full'

        result = self.cw.check_unwritten()

        self.assertTrue(result[1].startswith(warnStr.format('Duplex of')))

        # port auto_neg
        self.mockPort.get_auto_neg_reason.return_value = reason
        self.mockPort.get_auto_neg.return_value = True

        result = self.cw.check_unwritten()

        self.assertTrue(result[2].startswith(warnStr.format('Auto-negot')))

        # port admin_state
        self.mockPort.get_admin_state_reason.return_value = reason
        self.mockPort.get_admin_state.return_value = True

        result = self.cw.check_unwritten()

        self.assertTrue(result[3].startswith(warnStr.format('Admin state of')))

        # port lacp enabled
        self.mockPort.get_lacp_enabled_reason.return_value = reason
        self.mockPort.get_lacp_enabled.return_value = True

        result = self.cw.check_unwritten()

        self.assertTrue(result[4].startswith(warnStr.format('LACP state of')))

        # port lacp aadmin key
        self.mockPort.get_lacp_aadminkey_reason.return_value = reason
        self.mockPort.get_lacp_aadminkey.return_value = 1

        result = self.cw.check_unwritten()

        self.assertTrue(result[5].
                        startswith(warnStr.format('LACP aadminkey of')))

        # switch lacp support
        self.mockSwitch.get_lacp_support_reason.return_value = reason
        self.mockSwitch.get_lacp_support.return_value = False

        result = self.cw.check_unwritten()

        self.assertTrue(result[6].startswith(warnStr.format('Disabled')))

        # switch max lag
        self.mockSwitch.get_max_lag_reason.return_value = reason
        self.mockSwitch.get_max_lag.return_value = 1

        result = self.cw.check_unwritten()

        self.assertTrue(result[7].startswith(warnStr.format('Maximum')))

        # switch single port lag
        self.mockSwitch.get_single_port_lag_reason.return_value = reason
        self.mockSwitch.get_single_port_lag.return_value = False

        result = self.cw.check_unwritten()

        self.assertTrue(result[8].startswith(warnStr.format('Disabled')))

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

    def test_check_unwritten_stp_reason_is_config(self):
        reason = 'default'
        stp = STP.STP()
        self._set_stp_attributes_with_reason(stp, 'transfer_conf')
        self.mockSwitch.get_ports.return_value = []
        self.mockPort.get_lacp_enabled_reason.return_value = reason
        self.mockPort.get_lacp_aadminkey_reason.return_value = reason
        self.mockSwitch.get_lacp_support_reason.return_value = reason
        self.mockSwitch.get_max_lag_reason.return_value = reason
        self.mockSwitch.get_single_port_lag_reason.return_value = reason
        self.mockSwitch.get_stps.return_value = [stp]

        expResult = [
            self.WarningStart + 'STP process name "' + stp.get_name() +
            '" configured' + self.omitStr,
            self.ErrorStart + 'STP enabled' + self.omitStr,
            self.ErrorStart + 'STP version "' + str(stp.get_version()) +
            '" configured' + self.omitStr,
            self.ErrorStart + 'STP priority "' + str(stp.get_priority()) +
            '" configured' + self.omitStr,
            self.ErrorStart + 'MST configuration name "' +
            stp.get_mst_cfgname() + '" configured' + self.omitStr,
            self.ErrorStart + 'MST configuration revision "' +
            str(stp.get_mst_rev()) + '" configured' + self.omitStr,
            self.ErrorStart + 'MST instance "' + str(stp.get_mst_instance()) +
            '" configured' + self.omitStr,
            self.ErrorStart + 'MST instance "' + str(stp.get_mst_instance()) +
            '" with associated VLANs configured' + self.omitStr]

        result = self.cw.check_unwritten()

        self.assertEqual(expResult, result)

    def test_generate(self):
        expErrStr = self.ErrorStart + \
            'Generic switch cannot generate {} configuration'
        expected = \
            ([], [expErrStr.format('port'),
                  expErrStr.format('LAG'),
                  expErrStr.format('VLAN'),
                  expErrStr.format('STP'),
                  expErrStr.format('ACL'),
                  ])

        self.cw.check_unwritten = MagicMock(return_value=[])

        result = self.cw.generate()

        self.assertEqual(expected, result)

if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
