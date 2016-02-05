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

import EOS_read
import Switch

from unittest.mock import Mock


class EosClearPortCommand_test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.mockSwitch = Mock(spec=Switch.Switch)

    def setUp(self):
        self.cmd = EOS_read.EosClearPortCommand(self.mockSwitch)

    def test_do_lacp_fail(self):
        confFragment = 'foo'
        expected = 'NOTICE: Ignoring unknown command "clear port ' + \
            confFragment + '"'

        result = self.cmd.onecmd(confFragment)

        self.assertEqual(expected, result)

    def test_do_lacp(self):
        confFragment = 'lacp'
        self.cmd.do_lacp = Mock(return_value=None)

        self.cmd.onecmd(confFragment)

        self.assertEqual(1, self.cmd.do_lacp.call_count)

if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
