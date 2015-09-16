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
from unittest.mock import patch
from io import StringIO
import xml.etree.ElementTree as ET

from E2XConsole import SysInOutConsole
from HowToHandler import HowTo
from Translator import Translation
from Action import Action


class SysInOutConsole_test(unittest.TestCase):

    def setUp(self):
        self.prompt = 'any prompt is OK> '
        self.howto_descr_list = ('A', 'B')
        self.input_options = 'Enter "q" to quit'
        self.sioc = SysInOutConsole(self.prompt, self.howto_descr_list)

    def test_display_intro_shouldAddInfo(self):
        output = 'Copyright'

        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.sioc.display_intro(output)
            outlines = fake_out.getvalue().splitlines()

            self.assertIn(output, outlines)

    def test_build_howto_descriptions_dict(self):
        expected = {'1': 'A', '2': 'B'}

        self.assertDictEqual(
            expected,
            self.sioc._build_howto_descriptions_dict(self.howto_descr_list))

    def test_display_howto_descriptions_shouldShowInputOptions(self):
        expected = self.sioc.info

        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.sioc.display_howto_descriptions()

            self.assertIn(expected, fake_out.getvalue())

    def _generate_dummy_howto_element(self, desc):
        howto_element = ET.Element('howto')
        howto_element.set('desc', desc)
        hint_element = ET.SubElement(howto_element, 'hint')
        hint_element.text = 'No hint'
        eos_element = ET.SubElement(howto_element, 'eos')
        eos_element.text = 'I dont know this'
        xos_element = ET.SubElement(howto_element, 'xos')
        xos_element.text = 'I dont know this either'
        return howto_element

    def test_display_howto(self):
        desc = 'A'
        expected = 'HowTo ' + desc
        howto_element = self._generate_dummy_howto_element(desc)
        howto = HowTo(howto_element)

        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.sioc.display_howto(howto)

            self.assertIn(expected, fake_out.getvalue())

    def test_display_howto_shouldShowInputOptions(self):
        howto_element = self._generate_dummy_howto_element('A')
        howto = HowTo(howto_element)
        expected = self.sioc.info

        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.sioc.display_howto(howto)

            self.assertIn(expected, fake_out.getvalue())

    def test_display_translation_shouldShowXos(self):
        expected = 'show'
        translation = Translation(xos=expected)

        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.sioc.display_translation(translation)
            outlines = fake_out.getvalue().splitlines()

            self.assertIn(expected, outlines)

    def test_display_translation_shouldShowHintWithLeadingPercent(self):
        hint = 'hint'
        expected = '% ' + hint
        translation = Translation(hint=hint)

        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.sioc.display_translation(translation)
            outlines = fake_out.getvalue().splitlines()

            self.assertIn(expected, outlines)

    def test_display_translation_shouldShowXosFollowedByHint(self):
        hint = 'hint'
        xos = 'show 1'
        expected = xos + '\n' + '% ' + hint
        translation = Translation(xos=xos, hint=hint)

        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.sioc.display_translation(translation)
            out = fake_out.getvalue()

            self.assertIn(expected, out)

    def test_get_user_action_ExitAction(self):
        expected = Action.exit
        fake_input = 'q'

        with patch('sys.stdin', StringIO(fake_input)):
            result = self.sioc.get_user_action()

            self.assertEqual(expected, result.command)

    def test_get_user_action_DisplayhowtoDescriptionsAction(self):
        expected = Action.display_howto_descriptions
        fake_input = 'howtos'

        with patch('sys.stdin', StringIO(fake_input)):
            result = self.sioc.get_user_action()

            self.assertEqual(expected, result.command)

    def test_get_user_action_DisplayhowtoAction(self):
        expected_command = Action.display_howto
        expected_parameter = 'A'
        fake_input = '1'

        with patch('sys.stdin', StringIO(fake_input)):
            result = self.sioc.get_user_action()

            self.assertEqual(expected_command, result.command)
            self.assertEqual(expected_parameter, result.parameter)

    def test_get_user_action_DefaultAction(self):
        expected_command = Action.translate
        expected_parameter = 'show ip arp'
        fake_input = expected_parameter

        with patch('sys.stdin', StringIO(fake_input)):
            result = self.sioc.get_user_action()

            self.assertEqual(expected_command, result.command)
            self.assertEqual(expected_parameter, result.parameter)

if __name__ == '__main__':
    unittest.main(buffer=True)

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
