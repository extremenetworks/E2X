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

import sys
sys.path.extend(['../src'])

import unittest
import xml.etree.ElementTree as ET

from HowToHandler import HowToHandler


class howtoHandler_test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.howtos = '<?xml version="1.0"?>' \
                     '<howtos>' \
                     '  <howto desc="Upgrade firmware">' \
                     '  </howto>' \
                     '  <howto desc="Reboot switch">' \
                     '  </howto>' \
                     '  <howto desc="Show arp table">' \
                     '    <hint />' \
                     '    <eos />' \
                     '    <xos />'\
                     '  </howto>' \
                     '  <howto desc="Show routing table" />' \
                     '</howtos>'

    def setUp(self):
        self.rh = HowToHandler(self.howtos)

    def test_get_list_shouldReturnListOfhowtoDescriptions(self):

        result = self.rh.get_howto_descriptions()

        self.assertIn("Upgrade firmware", result)
        self.assertIn("Reboot switch", result)
        self.assertIn("Show arp table", result)

    def test_get_howto_element_shouldReturnShowRoutingTableElement(self):
        desc = 'Show routing table'
        expected_element = ET.Element('howto')
        expected_element.set('desc', desc)

        result = self.rh.get_howto_element(desc)

        self.assertEqual(expected_element.attrib['desc'],
                         result.attrib['desc'])

    def test_get_howto_shouldReturnhowto(self):
        desc = 'Show arp table'

        result = self.rh.get_howto(desc)

        self.assertEqual(desc, result.get_description())

    def test_init_ommittinghowtosParameterShouldResultInPredefinedList(self):
        rh = HowToHandler()

        result = rh.get_howto_descriptions()

        self.assertNotEqual([], result)

    def test_init_settingEmptyhowtosShouldResultInEmptyList(self):
        empty_howtos = '<howtos />'
        rh = HowToHandler(empty_howtos)

        result = rh.get_howto_descriptions()

        self.assertEqual([], result)

if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
