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
from unittest.mock import patch, MagicMock

from E2XConsole import E2XConsole
from HowToHandler import HowTo
from Action import Action
from Translator import Translator

from InteractiveModeHandler import InteractiveModeHandler


class InteractiveModeHandler_test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.exit_action = Action()
        cls.exit_action.command = Action.exit

        cls.disp_howto_descr_action = Action()
        cls.disp_howto_descr_action.command = \
            Action.display_howto_descriptions

        cls.disp_howto_action = Action()
        cls.disp_howto_action.command = Action.display_howto
        cls.disp_howto_action.parameter = 'test'

        cls.translate_action = Action()
        cls.translate_action.command = Action.translate
        cls.translate_action.parameter = 'show'

    def setUp(self):
        self.imh = InteractiveModeHandler('')

    def extractSurplusParameters_test_with(self, surplus_params):
        cmdLine = '-D --interactive ' + surplus_params
        imh = InteractiveModeHandler(cmdLine)

        expected = surplus_params
        actual = imh.extractSurPlusCmdlineParameters()

        self.assertEqual(expected, actual)

    def test_extractSurplusCmdlineParameters_shouldGiveSource(self):
        surplusParams = '--source'

        self.extractSurplusParameters_test_with(surplusParams)

    def test_extractSurplusCmdlineParameters_shouldGiveAllSurplusParams(self):
        surplusParams = '--source C5G124-24 --abort-on-error'

        self.extractSurplusParameters_test_with(surplusParams)

    def test_extractSurplusCmdlineParameters_shouldGiveNoSurplusParams(self):
        surplusParams = ''

        self.extractSurplusParameters_test_with(surplusParams)

    def test_extractSurplusCmdlineParameters_UnambiguousShortenedParam(self):
        cmdline = '--int --debu -D'
        expected = ''
        imh = InteractiveModeHandler(cmdline)

        actual = imh.extractSurPlusCmdlineParameters()

        self.assertEqual(expected, actual)

    def test_extractSurplusCmdlineParameters_AmbiguousParam(self):
        cmdline = '--inten --inter'
        expected = "--inten"
        imh = InteractiveModeHandler(cmdline)

        actual = imh.extractSurPlusCmdlineParameters()

        self.assertEqual(expected, actual)

    def test_make_howto_shouldForwardTohowtoHandler(self):
        desc = 'show arp table'

        with patch('HowToHandler.HowToHandler.get_howto') as gr:
            self.imh.make_howto(desc)

            gr.assert_called_once_with(desc)

    def test_run_shouldReturnZeroWhenUserExits(self):

        with patch('E2XConsole.E2XConsole.get_user_action') as gua:
            gua.return_value = self.exit_action

            self.assertEqual(0, self.imh.run())

    def test_run_shouldCloseConsoleWhenUserExits(self):
        console_mock = MagicMock(spec=E2XConsole)
        self.imh.console = console_mock
        console_mock.get_user_action.return_value = self.exit_action

        self.imh.run()

        console_mock.close.assert_called_once_with()

    def test_run_shouldCloseConsoleWhenUserHitsCtrlC(self):
        console_mock = MagicMock(spec=E2XConsole)
        self.imh.console = console_mock
        console_mock.get_user_action.side_effect = KeyboardInterrupt

        self.imh.run()

        console_mock.close.assert_called_once_with()

    def test_run_shouldDisplayHintOnSurplusParameters(self):
        surplus = '--source'
        cmdLine = '-D --interactive' + ' ' + surplus
        imh = InteractiveModeHandler(cmdLine)
        console_mock = MagicMock(spec=E2XConsole)
        console_mock.get_user_action.return_value = self.exit_action
        imh.console = console_mock

        imh.run()
        # ToDo: This is a weak test!
        self.assertTrue(console_mock.display_hint.called)

    def test_run_shouldDisplayListOfhowtosWhenUserWantsToSeeThem(self):
        console_mock = MagicMock(spec=E2XConsole)
        console_mock.get_user_action.side_effect = \
            [self.disp_howto_descr_action, self.exit_action]

        with patch('HowToHandler.HowToHandler.get_howto_descriptions') as g:
            g.return_value = ['test']

            imh = InteractiveModeHandler('--int')
            imh.console = console_mock

            imh.run()

            console_mock.display_howto_descriptions.\
                assert_called_with()

    def test_run_shouldDisplayHowtoWhenUserSelectsOneFromTheList(self):
        console_mock = MagicMock(spec=E2XConsole)
        console_mock.get_user_action.side_effect = \
            [self.disp_howto_action, self.exit_action]
        self.imh.console = console_mock

        howto_mock = MagicMock(spec=HowTo)
        howto_mock.get_description.return_value = 'test'
        patched_method = \
            'InteractiveModeHandler.InteractiveModeHandler.make_howto'
        with patch(patched_method) as m:
            m.return_value = howto_mock

            self.imh.run()

            m.assert_called_once_with('test')
            console_mock.display_howto.assert_called_with(howto_mock)

    def test_run_shouldCallConfiglineInterpreter(self):
        console_mock = MagicMock(spec=E2XConsole)
        console_mock.get_user_action.side_effect = \
            [self.translate_action, self.exit_action]
        self.imh.console = console_mock

        translator_mock = MagicMock(spec=Translator)
        self.imh.translator = translator_mock

        self.imh.run()

        translator_mock.translate.\
            assert_called_once_with(self.translate_action.parameter)
        self.assertTrue(console_mock.display_translation.called)

if __name__ == '__main__':
    unittest.main(buffer=True)

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
