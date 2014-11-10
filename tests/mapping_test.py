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

import CM


class Mapping_test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ErrorStart = 'ERROR:'
        cls.WarningStart = 'WARN:'
        cls.NoticeStart = 'NOTICE:'

    def setUp(self):
        self.cm = CM.CoreModule()

    def __listContainsLinesStartingWith(self, startStr, strList):
        for line in strList:
            if line.startswith(startStr):
                return True
        return False

    def test_mapping_to_compatible_switch(self):
        self.cm.set_source_switch('C5K125-48P2')
        self.cm.set_target_switch('SummitX460-48p+2sf')

        result, errList = self.cm._create_port_mapping()

        self.assertFalse(
            self.__listContainsLinesStartingWith(self.ErrorStart, errList))
        self.assertTrue(
            self.__listContainsLinesStartingWith(self.NoticeStart, errList))
        self.assertTrue(result)

    def test_mapping_to_switch_with_more_features(self):
        self.cm.set_source_switch('C5K125-48P2')
        self.cm.set_target_switch('SummitX460-48p+4sf')

        result, errList = self.cm._create_port_mapping()

        self.assertFalse(
            self.__listContainsLinesStartingWith(self.ErrorStart, errList))
        self.assertTrue(
            self.__listContainsLinesStartingWith(self.NoticeStart, errList))
        self.assertTrue(result)

    def test_mapping_to_full_featured_switch(self):
        self.cm.set_source_switch('C5K125-48P2')
        self.cm.set_target_switch('SummitX460-48p+2sf+4sf')

        result, errList = self.cm._create_port_mapping()

        self.assertFalse(
            self.__listContainsLinesStartingWith(self.ErrorStart, errList))
        self.assertTrue(
            self.__listContainsLinesStartingWith(self.NoticeStart, errList))
        self.assertTrue(result)

    def test_mapping_to_switch_with_lesser_features(self):
        self.cm.set_source_switch('C5K125-48P2')
        self.cm.set_target_switch('SummitX460-48p')

        result, errList = self.cm._create_port_mapping()

        self.assertFalse(
            self.__listContainsLinesStartingWith(self.ErrorStart, errList))
        self.assertTrue(
            self.__listContainsLinesStartingWith(self.WarningStart, errList))
        self.assertTrue(
            self.__listContainsLinesStartingWith(self.NoticeStart, errList))
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4