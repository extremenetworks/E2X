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

from Translator import Translator, PatternReplacement


class Translator_test(unittest.TestCase):

    def setUp(self):
        pattern_replacement = PatternReplacement('show switch (\d+)',
                                                 r'show slot \1')
        pattern_replacements = [pattern_replacement]
        self.tlr = Translator(pattern_replacements=pattern_replacements)

    def test_translate_shouldReturnNoHintOnEmptyConfigLine(self):
        configline = ''

        transl = self.tlr.translate(configline)

        self.assertEqual('', transl.get_hint())

    def test_translate_shouldReturnNoHintOnCommentedConfigLine(self):
        configline = '#'

        transl = self.tlr.translate(configline)

        self.assertEqual('', transl.get_hint())

    def test_translate_shouldReturnNoHintOnCommentedConfigLine2(self):
        configline = '!'

        transl = self.tlr.translate(configline)

        self.assertEqual('', transl.get_hint())

    def test_translate_shouldReturnXosConfigOnValidInput(self):
        configline = 'show switch 12'
        expected = 'show slot 12'

        transl = self.tlr.translate(configline)

        self.assertEqual(expected, transl.get_xos())

    def test_translate_shouldReturnEmptyHintOnValidInput(self):
        configline = 'show switch 1'
        expected = ''

        transl = self.tlr.translate(configline)

        self.assertEqual(expected, transl.get_hint())

    def test_translate_shouldIgnoreMultipleSpacesBetweenKeywords(self):
        configline = 'show    switch   1'
        expected = 'show slot 1'

        transl = self.tlr.translate(configline)

        self.assertEqual(expected, transl.get_xos())

    def test_translate_shouldAllowNewlineInReplacement(self):
        pattern_replacement = PatternReplacement('set timeout (\d+)',
                                                 r'configure timeout \1\n'
                                                 'enable timeout')
        tlr = Translator(pattern_replacements=[pattern_replacement])
        configline = 'set timeout 10'
        expected = 'configure timeout 10\nenable timeout'

        transl = tlr.translate(configline)

        self.assertEqual(expected, transl.get_xos())

    def test_translate_shouldAllowConstantsInPatternString(self):
        PATTERN_IPV4 = Translator.PATTERN_IPV4
        pattern = 'ip address (' + PATTERN_IPV4 + ') ' \
                                                  'mask (' + PATTERN_IPV4 + ')'
        pattern_replacement = PatternReplacement(pattern,
                                                 r'\1 \2')
        pattern_replacements = [pattern_replacement]
        tlr = Translator(pattern_replacements)
        configline = 'ip address 1.2.3.4 mask 255.255.255.0'
        expected = '1.2.3.4 255.255.255.0'

        transl = tlr.translate(configline)

        self.assertEqual(expected, transl.get_xos())

    def test_translate_shouldEmitEmptyStringIfNoHintInPatternReplacement(self):
        pattern = 'show (\d+)'
        configline = 'show 11'
        pattern_replacement = \
            PatternReplacement(pattern, r'show \1')
        tlr = Translator([pattern_replacement])

        transl = tlr.translate(configline)

        self.assertEqual(configline, transl.get_xos())
        self.assertEqual('', transl.get_hint())

    def test_translate_shouldEmitHintInPatternReplacement(self):
        pattern = 'show (\d+)'
        hint = 'silly hint'
        configline = 'show 11'
        pattern_replacement_and_hint = \
            PatternReplacement(pattern, r'show \1', 'silly hint')
        tlr = Translator([pattern_replacement_and_hint])

        transl = tlr.translate(configline)

        self.assertEqual(configline, transl.get_xos())
        self.assertEqual(hint, transl.get_hint())

if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
