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

import CM


class Mapping_test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ErrorStart = 'ERROR:'
        cls.WarningStart = 'WARN:'
        cls.NoticeStart = 'NOTICE:'
        cls.MappingInfoStart = 'INFO: Mapping port'
        cls.MappingNoticeStart = 'NOTICE: Mapping port'
        cls.MappingWarningStart = 'WARN: Could not map port'
        cls.UnusedPortStart = 'NOTICE: Port'
        cls.UnusedPortEnd = 'of target switch is not used'
        cls.UnmappedPortStart = 'WARN: Could not map port'
        cls.default48PortMappingDict = {
            "ge.1.1": "1", "ge.1.2": "2", "ge.1.3": "3", "ge.1.4": "4",
            "ge.1.5": "5", "ge.1.6": "6", "ge.1.7": "7", "ge.1.8": "8",
            "ge.1.9": "9", "ge.1.10": "10", "ge.1.11": "11", "ge.1.12": "12",
            "ge.1.13": "13", "ge.1.14": "14", "ge.1.15": "15", "ge.1.16": "16",
            "ge.1.17": "17", "ge.1.18": "18", "ge.1.19": "19", "ge.1.20": "20",
            "ge.1.21": "21", "ge.1.22": "22", "ge.1.23": "23", "ge.1.24": "24",
            "ge.1.25": "25", "ge.1.26": "26", "ge.1.27": "27", "ge.1.28": "28",
            "ge.1.29": "29", "ge.1.30": "30", "ge.1.31": "31", "ge.1.32": "32",
            "ge.1.33": "33", "ge.1.34": "34", "ge.1.35": "35", "ge.1.36": "36",
            "ge.1.37": "37", "ge.1.38": "38", "ge.1.39": "39", "ge.1.40": "40",
            "ge.1.41": "41", "ge.1.42": "42", "ge.1.43": "43", "ge.1.44": "44",
            "ge.1.45": "45", "ge.1.46": "46", "ge.1.47": "47", "ge.1.48": "48",
        }
        cls.module1TenGMappingDict = {"tg.1.49": "53", "tg.1.50": "54"}
        cls.module2TenGMappingDict = {"tg.1.49": "55", "tg.1.50": "56"}
        cls.defaultStackMappingDict = {
            "ge.1.1": "1:1", "ge.1.2": "1:2", "ge.1.3": "1:3", "ge.1.4": "1:4",
            "ge.1.5": "1:5", "ge.1.6": "1:6", "ge.1.7": "1:7", "ge.1.8": "1:8",
            "ge.1.9": "1:9", "ge.1.10": "1:10", "ge.1.11": "1:11",
            "ge.1.12": "1:12", "ge.1.13": "1:13", "ge.1.14": "1:14",
            "ge.1.15": "1:15", "ge.1.16": "1:16", "ge.1.17": "1:17",
            "ge.1.18": "1:18", "ge.1.19": "1:19", "ge.1.20": "1:20",
            "ge.1.21": "1:21", "ge.1.22": "1:22", "ge.1.23": "1:23",
            "ge.1.24": "1:24", "ge.2.1": "2:1", "ge.2.2": "2:2",
            "ge.2.3": "2:3", "ge.2.4": "2:4", "ge.2.5": "2:5", "ge.2.6": "2:6",
            "ge.2.7": "2:7", "ge.2.8": "2:8", "ge.2.9": "2:9",
            "ge.2.10": "2:10", "ge.2.11": "2:11", "ge.2.12": "2:12",
            "ge.2.13": "2:13", "ge.2.14": "2:14", "ge.2.15": "2:15",
            "ge.2.16": "2:16", "ge.2.17": "2:17", "ge.2.18": "2:18",
            "ge.2.19": "2:19", "ge.2.20": "2:20", "ge.2.21": "2:21",
            "ge.2.22": "2:22", "ge.2.23": "2:23", "ge.2.24": "2:24",
        }

    def setUp(self):
        self.cm = CM.CoreModule()

    def __listContainsLinesStartingWith(self, startStr, strList):
        for line in strList:
            if line.startswith(startStr):
                return True
        return False

    def __mappingInfoNoticesEqualMappingDict(self, strList, mappingDict):
        noticeDict = {}
        for line in strList:
            # Example: NOTICE: Mapping port "tg.1.25" to port "51"
            if (line.startswith(self.MappingNoticeStart) or
                    line.startswith(self.MappingInfoStart)):
                lineList = line.split()
                from_port = lineList[3].strip('"')
                to_port = lineList[6].strip('"')
                noticeDict[from_port] = to_port
        return noticeDict == mappingDict

    def __unusedPortNoticesEqualList(self, strList, unusedPortsList):
        noticeList = []
        for line in strList:
            # Example: NOTICE: Port "49" of target switch is not used
            if (line.startswith(self.UnusedPortStart) and
                    line.endswith(self.UnusedPortEnd)):
                noticeList.append(line.split()[2].strip('"'))
        return sorted(noticeList) == sorted(unusedPortsList)

    def __unmappedPortWarningsEqualList(self, strList, unmappedPorts):
        warnList = []
        for line in strList:
            # Example: WARN: Could not map port tg.1.49
            if line.startswith(self.UnmappedPortStart):
                warnList.append(line.split()[-1])
        return sorted(warnList) == sorted(unmappedPorts)

    def test_mapping_to_compatible_switch(self):
        self.cm.set_source_switch('C5K125-48P2')
        self.cm.set_target_switch('SummitX460-48p+2sf')
        mappingDict = dict(self.default48PortMappingDict)
        mappingDict.update(self.module1TenGMappingDict)
        unusedPortsList = ['49', '50', '51', '52']

        result, errList = self.cm._create_port_mapping()

        self.assertFalse(
            self.__listContainsLinesStartingWith(self.ErrorStart, errList))
        self.assertTrue(
            self.__listContainsLinesStartingWith(self.NoticeStart, errList))
        self.assertTrue(
            self.__mappingInfoNoticesEqualMappingDict(errList, mappingDict))
        self.assertTrue(
            self.__unusedPortNoticesEqualList(errList, unusedPortsList))
        self.assertTrue(result)

    def test_mapping_to_switch_with_more_features(self):
        self.cm.set_source_switch('C5K125-48P2')
        self.cm.set_target_switch('SummitX460-48p+4sf')
        mappingDict = dict(self.default48PortMappingDict)
        mappingDict.update(self.module2TenGMappingDict)
        unusedPortsList = ['49', '50', '51', '52', '57', '58']

        result, errList = self.cm._create_port_mapping()

        self.assertFalse(
            self.__listContainsLinesStartingWith(self.ErrorStart, errList))
        self.assertTrue(
            self.__listContainsLinesStartingWith(self.NoticeStart, errList))
        self.assertTrue(
            self.__mappingInfoNoticesEqualMappingDict(errList, mappingDict))
        self.assertTrue(
            self.__unusedPortNoticesEqualList(errList, unusedPortsList))
        self.assertTrue(result)

    def test_mapping_to_full_featured_switch(self):
        self.cm.set_source_switch('C5K125-48P2')
        self.cm.set_target_switch('SummitX460-48p+2sf+4sf')
        mappingDict = dict(self.default48PortMappingDict)
        mappingDict.update(self.module1TenGMappingDict)
        unusedPortsList = ['49', '50', '51', '52', '55', '56', '57', '58']

        result, errList = self.cm._create_port_mapping()

        self.assertFalse(
            self.__listContainsLinesStartingWith(self.ErrorStart, errList))
        self.assertTrue(
            self.__listContainsLinesStartingWith(self.NoticeStart, errList))
        self.assertTrue(
            self.__mappingInfoNoticesEqualMappingDict(errList, mappingDict))
        self.assertTrue(
            self.__unusedPortNoticesEqualList(errList, unusedPortsList))
        self.assertTrue(result)

    def test_mapping_to_switch_with_lesser_features(self):
        self.cm.set_source_switch('C5K125-48P2')
        self.cm.set_target_switch('SummitX460-48p')
        mappingDict = self.default48PortMappingDict
        unusedPortsList = ['49', '50', '51', '52']
        unmappedPortsList = ['tg.1.49', 'tg.1.50']

        result, errList = self.cm._create_port_mapping()

        self.assertFalse(
            self.__listContainsLinesStartingWith(self.ErrorStart, errList))
        self.assertTrue(
            self.__listContainsLinesStartingWith(self.WarningStart, errList))
        self.assertTrue(
            self.__listContainsLinesStartingWith(self.NoticeStart, errList))
        self.assertTrue(
            self.__mappingInfoNoticesEqualMappingDict(errList, mappingDict))
        self.assertTrue(
            self.__unusedPortNoticesEqualList(errList, unusedPortsList))
        self.assertTrue(
            self.__unmappedPortWarningsEqualList(errList, unmappedPortsList))
        self.assertTrue(result)

    def test_mapping_stacks_OK(self):
        self.cm.set_source_switch('C5G124-24,C5G124-24')
        self.cm.set_target_switch('SummitX460-24t,SummitX460-24t')
        mappingDict = self.defaultStackMappingDict
        unusedPortsList = ["1:25", "1:26", "1:27", "1:28",
                           "2:25", "2:26", "2:27", "2:28"]

        result, errList = self.cm._create_port_mapping()

        self.assertFalse(
            self.__listContainsLinesStartingWith(self.ErrorStart, errList))
        self.assertFalse(
            self.__listContainsLinesStartingWith(self.WarningStart, errList))
        self.assertTrue(
            self.__listContainsLinesStartingWith(self.NoticeStart, errList))
        self.assertFalse(
            self.__listContainsLinesStartingWith(self.MappingNoticeStart,
                                                 errList))
        self.assertTrue(
            self.__mappingInfoNoticesEqualMappingDict(errList, mappingDict))
        self.assertTrue(
            self.__unusedPortNoticesEqualList(errList, unusedPortsList))
        self.assertTrue(result)

    def test_mapping_stacks_not_enough_ports(self):
        self.cm.set_source_switch('C5G124-24,C5G124-24,C5G124-24')
        self.cm.set_target_switch('SummitX460-24t,SummitX460-24t')
        mappingDict = self.defaultStackMappingDict
        unmappedPortsList = ['ge.3.1', 'ge.3.2', 'ge.3.3', 'ge.3.4', 'ge.3.5',
                             'ge.3.6', 'ge.3.7', 'ge.3.8', 'ge.3.9', 'ge.3.10',
                             'ge.3.11', 'ge.3.12', 'ge.3.13', 'ge.3.14',
                             'ge.3.15', 'ge.3.16', 'ge.3.17', 'ge.3.18',
                             'ge.3.19', 'ge.3.20', 'ge.3.21', 'ge.3.22',
                             'ge.3.23', 'ge.3.24']
        unusedPortsList = ["1:25", "1:26", "1:27", "1:28",
                           "2:25", "2:26", "2:27", "2:28"]

        result, errList = self.cm._create_port_mapping()

        self.assertFalse(
            self.__listContainsLinesStartingWith(self.ErrorStart, errList))
        self.assertTrue(
            self.__listContainsLinesStartingWith(self.MappingWarningStart,
                                                 errList))
        self.assertTrue(
            self.__listContainsLinesStartingWith(self.NoticeStart, errList))
        self.assertTrue(
            self.__mappingInfoNoticesEqualMappingDict(errList, mappingDict))
        self.assertTrue(
            self.__unmappedPortWarningsEqualList(errList, unmappedPortsList))
        self.assertTrue(
            self.__unusedPortNoticesEqualList(errList, unusedPortsList))
        self.assertTrue(result)

    def test_mapping_stack_to_standalone(self):
        self.cm.set_source_switch('C5G124-24,C5G124-24')
        self.cm.set_target_switch('SummitX460-48p')
        mappingDict = {
            "ge.1.1": "1", "ge.1.2": "2", "ge.1.3": "3", "ge.1.4": "4",
            "ge.1.5": "5", "ge.1.6": "6", "ge.1.7": "7", "ge.1.8": "8",
            "ge.1.9": "9", "ge.1.10": "10", "ge.1.11": "11", "ge.1.12": "12",
            "ge.1.13": "13", "ge.1.14": "14", "ge.1.15": "15", "ge.1.16": "16",
            "ge.1.17": "17", "ge.1.18": "18", "ge.1.19": "19", "ge.1.20": "20",
            "ge.1.21": "21", "ge.1.22": "22", "ge.1.23": "23", "ge.1.24": "24",
            "ge.2.1": "25", "ge.2.2": "26", "ge.2.3": "27", "ge.2.4": "28",
            "ge.2.5": "29", "ge.2.6": "30", "ge.2.7": "31", "ge.2.8": "32",
            "ge.2.9": "33", "ge.2.10": "34", "ge.2.11": "35", "ge.2.12": "36",
            "ge.2.13": "37", "ge.2.14": "38", "ge.2.15": "39", "ge.2.16": "40",
            "ge.2.17": "41", "ge.2.18": "42", "ge.2.19": "43", "ge.2.20": "44",
            "ge.2.21": "45", "ge.2.22": "46", "ge.2.23": "47", "ge.2.24": "48"
        }
        unusedPortsList = ['49', '50', '51', '52']

        result, errList = self.cm._create_port_mapping()

        self.assertFalse(
            self.__listContainsLinesStartingWith(self.ErrorStart, errList))
        self.assertFalse(
            self.__listContainsLinesStartingWith(self.WarningStart, errList))
        self.assertTrue(
            self.__listContainsLinesStartingWith(self.MappingNoticeStart,
                                                 errList))
        self.assertTrue(
            self.__mappingInfoNoticesEqualMappingDict(errList, mappingDict))
        self.assertTrue(
            self.__unusedPortNoticesEqualList(errList, unusedPortsList))
        self.assertTrue(result)

    def test_mapping_two_member_stack_to_one_member_stack(self):
        self.cm.set_source_switch('C5G124-24,C5G124-24')
        self.cm.set_target_switch('SummitX460-48p,')
        mappingDict = {
            "ge.1.1": "1:1", "ge.1.2": "1:2", "ge.1.3": "1:3",
            "ge.1.4": "1:4", "ge.1.5": "1:5", "ge.1.6": "1:6",
            "ge.1.7": "1:7", "ge.1.8": "1:8", "ge.1.9": "1:9",
            "ge.1.10": "1:10", "ge.1.11": "1:11", "ge.1.12": "1:12",
            "ge.1.13": "1:13", "ge.1.14": "1:14", "ge.1.15": "1:15",
            "ge.1.16": "1:16", "ge.1.17": "1:17", "ge.1.18": "1:18",
            "ge.1.19": "1:19", "ge.1.20": "1:20", "ge.1.21": "1:21",
            "ge.1.22": "1:22", "ge.1.23": "1:23", "ge.1.24": "1:24",
            "ge.2.1": "1:25", "ge.2.2": "1:26", "ge.2.3": "1:27",
            "ge.2.4": "1:28", "ge.2.5": "1:29", "ge.2.6": "1:30",
            "ge.2.7": "1:31", "ge.2.8": "1:32", "ge.2.9": "1:33",
            "ge.2.10": "1:34", "ge.2.11": "1:35", "ge.2.12": "1:36",
            "ge.2.13": "1:37", "ge.2.14": "1:38", "ge.2.15": "1:39",
            "ge.2.16": "1:40", "ge.2.17": "1:41", "ge.2.18": "1:42",
            "ge.2.19": "1:43", "ge.2.20": "1:44", "ge.2.21": "1:45",
            "ge.2.22": "1:46", "ge.2.23": "1:47", "ge.2.24": "1:48"
        }
        unusedPortsList = ['1:49', '1:50', '1:51', '1:52']

        result, errList = self.cm._create_port_mapping()

        self.assertFalse(
            self.__listContainsLinesStartingWith(self.ErrorStart, errList))
        self.assertFalse(
            self.__listContainsLinesStartingWith(self.WarningStart, errList))
        self.assertTrue(
            self.__listContainsLinesStartingWith(self.MappingNoticeStart,
                                                 errList))
        self.assertTrue(
            self.__mappingInfoNoticesEqualMappingDict(errList, mappingDict))
        self.assertTrue(
            self.__unusedPortNoticesEqualList(errList, unusedPortsList))
        self.assertTrue(result)

    def test_mapping_two_sfp_stack_to_standalone(self):
        self.cm.set_source_switch('C5K175-24,C5K175-24')
        self.cm.set_target_switch('SummitX460-48x+4sf')
        mappingDict = {
            "ge.1.1": "1", "ge.1.2": "2", "ge.1.3": "3", "ge.1.4": "4",
            "ge.1.5": "5", "ge.1.6": "6", "ge.1.7": "7", "ge.1.8": "8",
            "ge.1.9": "9", "ge.1.10": "10", "ge.1.11": "11", "ge.1.12": "12",
            "ge.1.13": "13", "ge.1.14": "14", "ge.1.15": "15", "ge.1.16": "16",
            "ge.1.17": "17", "ge.1.18": "18", "ge.1.19": "19", "ge.1.20": "20",
            "ge.1.21": "21", "ge.1.22": "22", "ge.1.23": "23", "ge.1.24": "24",
            "tg.1.25": "51", "tg.1.26": "52", "ge.2.1": "25", "ge.2.2": "26",
            "ge.2.3": "27", "ge.2.4": "28", "ge.2.5": "29", "ge.2.6": "30",
            "ge.2.7": "31", "ge.2.8": "32", "ge.2.9": "33", "ge.2.10": "34",
            "ge.2.11": "35", "ge.2.12": "36", "ge.2.13": "37", "ge.2.14": "38",
            "ge.2.15": "39", "ge.2.16": "40", "ge.2.17": "41", "ge.2.18": "42",
            "ge.2.19": "43", "ge.2.20": "44", "ge.2.21": "45", "ge.2.22": "46",
            "ge.2.23": "47", "ge.2.24": "48", "tg.2.25": "53", "tg.2.26": "54",
        }
        unusedPortsList = []

        result, errList = self.cm._create_port_mapping()

        self.assertFalse(
            self.__listContainsLinesStartingWith(self.ErrorStart, errList))
        self.assertFalse(
            self.__listContainsLinesStartingWith(self.WarningStart, errList))
        self.assertTrue(
            self.__listContainsLinesStartingWith(self.MappingNoticeStart,
                                                 errList))
        self.assertTrue(
            self.__mappingInfoNoticesEqualMappingDict(errList, mappingDict))
        self.assertTrue(
            self.__unusedPortNoticesEqualList(errList, unusedPortsList))
        self.assertTrue(result)

    def test_mapping_48_port_switch_to_two_24_port_stacked_switches(self):
        self.cm.set_source_switch('C5K125-48')
        self.cm.set_target_switch('SummitX460-24t,SummitX460-24t+2sf')
        mappingDict = {
            "ge.1.1": "1:1", "ge.1.2": "1:2", "ge.1.3": "1:3", "ge.1.4": "1:4",
            "ge.1.5": "1:5", "ge.1.6": "1:6", "ge.1.7": "1:7", "ge.1.8": "1:8",
            "ge.1.9": "1:9", "ge.1.10": "1:10", "ge.1.11": "1:11",
            "ge.1.12": "1:12", "ge.1.13": "1:13", "ge.1.14": "1:14",
            "ge.1.15": "1:15", "ge.1.16": "1:16", "ge.1.17": "1:17",
            "ge.1.18": "1:18", "ge.1.19": "1:19", "ge.1.20": "1:20",
            "ge.1.21": "1:21", "ge.1.22": "1:22", "ge.1.23": "1:23",
            "ge.1.24": "1:24", "ge.1.25": "2:1", "ge.1.26": "2:2",
            "ge.1.27": "2:3", "ge.1.28": "2:4", "ge.1.29": "2:5",
            "ge.1.30": "2:6", "ge.1.31": "2:7", "ge.1.32": "2:8",
            "ge.1.33": "2:9", "ge.1.34": "2:10", "ge.1.35": "2:11",
            "ge.1.36": "2:12", "ge.1.37": "2:13", "ge.1.38": "2:14",
            "ge.1.39": "2:15", "ge.1.40": "2:16", "ge.1.41": "2:17",
            "ge.1.42": "2:18", "ge.1.43": "2:19", "ge.1.44": "2:20",
            "ge.1.45": "2:21", "ge.1.46": "2:22", "ge.1.47": "2:23",
            "ge.1.48": "2:24", "tg.1.49": "2:29", "tg.1.50": "2:30",
        }
        unusedPortsList = ["1:25", "1:26", "1:27", "1:28",
                           "2:25", "2:26", "2:27", "2:28"]

        result, errList = self.cm._create_port_mapping()

        self.assertFalse(
            self.__listContainsLinesStartingWith(self.ErrorStart, errList))
        self.assertFalse(
            self.__listContainsLinesStartingWith(self.WarningStart, errList))
        self.assertTrue(
            self.__listContainsLinesStartingWith(self.MappingNoticeStart,
                                                 errList))
        self.assertTrue(
            self.__mappingInfoNoticesEqualMappingDict(errList, mappingDict))
        self.assertTrue(
            self.__unusedPortNoticesEqualList(errList, unusedPortsList))
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
