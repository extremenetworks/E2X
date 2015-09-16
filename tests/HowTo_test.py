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
import xml.etree.ElementTree as ET
from HowToHandler import HowTo


class howto_test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        howto_xml = '<?xml version="1.0"?>' \
                    '<howto desc="test">' \
                    '  <hint></hint>' \
                    '  <eos>The eos config line(s)</eos>' \
                    '  <xos>The xos config\n' \
                    '       line(s)</xos>' \
                    '</howto>'
        cls.howto_element = ET.fromstring(howto_xml)

    def setUp(self):
        self.howto = HowTo(self.howto_element)

    def test_get_description_shouldReturntest(self):
        expected = 'test'

        result = self.howto.get_description()

        self.assertEqual(expected, result)

    def test_get_hint_shouldReturnNone(self):

        result = self.howto.get_hint()

        self.assertIsNone(result)

    def test_get_eos_shouldReturnOneLine(self):
        expected = 'The eos config line(s)'

        result = self.howto.get_eos()

        self.assertEqual(expected, result)

    def test_get_xos_shouldReturnTwoLines(self):
        expectedNrOfLines = 2

        result = self.howto.get_xos()

        self.assertEqual(expectedNrOfLines, len(result.splitlines()))

    def test_init_missinghowtoElementShouldGiveEmptyReply(self):

        howto = HowTo()

        self.assertEqual(None, howto.get_description())
        self.assertEqual(None, howto.get_hint())
        self.assertEqual(None, howto.get_eos())
        self.assertEqual(None, howto.get_xos())

    def test_get_xos_as_list_shouldCondenseLines(self):
        expected = ['The xos config', 'line(s)']

        result = self.howto.get_xos_as_list()

        self.assertEqual(expected, result)

    def test_get_eos_as_list_shouldDoNothing(self):
        expected = ['The eos config line(s)']

        result = self.howto.get_eos_as_list()

        self.assertEqual(expected, result)

    def test_get_hint_as_list_shouldReturnEmptyList(self):
        expected = []

        result = self.howto.get_hint_as_list()

        self.assertEqual(expected, result)

if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
