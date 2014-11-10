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

import EOS


class Configuration_test(unittest.TestCase):
    def setUp(self):
        self.sw = EOS.C5K125_48P2()

    def test_setUp_ok(self):
        self.assertEqual('C5K125-48P2', self.sw._model)

    def test_configuration_fails_because_of_unknown_configs(self):
        configLine = 'set snmp group company security-model v1'
        expected = 'NOTICE: Ignoring unknown command "' + configLine + '"'

        result = self.sw.configure(configLine)

        self.assertEqual(expected, result)

    def test_configuration_fails_because_of_invalid_port(self):
        portName = 'ge.2.1'
        cmd = 'set port disable'
        configLine = cmd + ' ' + portName
        expected = 'ERROR: Port ' + portName + ' not found (' + cmd + ')'

        result = self.sw.configure(configLine)

        self.assertEqual(expected, result)

    def test_configuration_fails_because_of_incomplete_configline(self):
        configLine = 'set port disable'
        expected = 'ERROR: Port  not found (' + configLine + ')'

        result = self.sw.configure(configLine)

        self.assertEqual(expected, result)

    def test_configuration_succeeds_port_disable_command(self):
        portName = 'ge.1.1'
        configLine = 'set port disable ' + portName
        self.sw.get_ports_by_name(portName)[0].set_admin_state(True, None)

        expected = 'Success'

        result = self.sw.configure(configLine)
        portState = self.sw.get_ports_by_name(portName)[0].get_admin_state()

        self.assertEqual(False, portState)

if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
