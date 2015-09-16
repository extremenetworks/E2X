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

import sys
sys.path.extend(['../src'])
import unittest
from unittest import mock
import cli


class args:
    quiet = False
    verbose = False
    debug = False
    ignore_defaults = True
    keep_unknown_lines = True
    comment_unknown_lines = True
    disable_unused_ports = True
    mgmt_port = False
    source = ""
    target = ""


def parse():
    return args


class cli_test(unittest.TestCase):

    @mock.patch('cli.CommandLineParser.parse', side_effect=parse)
    def test_shouldNotSwitchToInteractiveMode(self, mock_function):
        args.interactive = False

        with mock.patch('cli.InteractiveModeHandler.run') as int_int_run:

            cli.main('')

            self.assertFalse(int_int_run.called)

    @mock.patch('cli.CommandLineParser.parse', side_effect=parse)
    def test_shouldSwitchToInteractiveModeAndReturnZero(self, mock_function):
        args.interactive = True
        with mock.patch('cli.InteractiveModeHandler.run') as int_int_run:
            int_int_run.return_value = 0

            ret = cli.main('')

            self.assertTrue(int_int_run.called)
            self.assertEqual(0, ret)

    @mock.patch('cli.CommandLineParser.parse', side_effect=parse)
    def test_shouldPassOriginalCommandLineToInteractiveMode(self,
                                                            mock_function):
        args.interactive = True
        expected = "--interactive -D"
        with mock.patch('cli.InteractiveModeHandler') as int_int:

            cli.main(expected.split())

            int_int.assert_called_once_with(expected, progname=cli.progname,
                                            progver=cli.progver)


if __name__ == '__main__':
    unittest.main(buffer=True)

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
