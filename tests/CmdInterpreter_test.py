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

import Switch


class CmdInterpreter_test(unittest.TestCase):
    def setUp(self):
        self.cmd = Switch.CmdInterpreter()

    def test_is_comment(self):
        self.cmd._comments = ['!', '#']
        line1 = '!This is is comment'
        line2 = '#This also'
        line3 = 'But not this!'

        self.assertTrue(self.cmd._is_comment(line1))
        self.assertTrue(self.cmd._is_comment(line2))
        self.assertFalse(self.cmd._is_comment(line3))

    def test_emptyline(self):

        self.assertEqual("", self.cmd.emptyline())

    def test_get_comment_with_comments(self):
        expected = '!'
        self.cmd._comments = [expected, '#']

        self.assertEqual(expected, self.cmd.get_comment())

    def test_get_comment_default(self):

        self.assertIsNone(self.cmd.get_comment())

if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
