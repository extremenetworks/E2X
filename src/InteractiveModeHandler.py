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

from E2XConsole import E2XConsole
from HowToHandler import HowToHandler
from Action import Action
from Translator import Translator


class InteractiveModeHandler:

    def __init__(self, cmdLineArgs, progname='generic', progver='unknown'):
        self._cmdlineArgs = cmdLineArgs
        self.hth = HowToHandler()
        self.prompt = progname + '> '
        self.console = \
            E2XConsole(use_curses=False, prompt=self.prompt,
                       howto_descr=self.hth.get_howto_descriptions())
        self.translator = Translator()

        intro = \
            progname + ' v' + progver + '\n' + \
            'Copyright 2014-2015 Extreme Networks, Inc.  All rights ' \
            'reserved.\n' \
            'Use is subject to license terms.\n' \
            'This is free software, licensed under CDDL 1.0\n' \
            '\n' \
            '% Command translation assumes VLAN 1 for management'

        self.console.display_intro(intro)

    def get_prompt(self):
        return self.prompt

    def _remove_unabbreviated_arguments(self, unabbreviated_args_set,
                                        args_list):
        cleared_list = \
            [p for p in args_list if p not in unabbreviated_args_set]
        return cleared_list

    def _determine_abbreviated_arguments(self, unabbreviated_args_list,
                                         args_list):
        abbreviated_args_list = []
        for unabbreviated_arg in unabbreviated_args_list:
            abbreviated_args_list += \
                [a for a in args_list if unabbreviated_arg.startswith(a)]
        return abbreviated_args_list

    def extractSurPlusCmdlineParameters(self):
        acceptedParams = set(['-D', '--interactive', '--debug'])
        cleared_from_accepted = \
            self._remove_unabbreviated_arguments(acceptedParams,
                                                 self._cmdlineArgs.split())
        abbreviated_accepted = \
            self._determine_abbreviated_arguments(acceptedParams,
                                                  cleared_from_accepted)
        difference = \
            [a for a in cleared_from_accepted if a not in abbreviated_accepted]
        return ' '.join(difference)

    def make_howto(self, description):
        return(self.hth.get_howto(description))

    def run(self):
        surplus = self.extractSurPlusCmdlineParameters()
        if surplus:
            hint = 'Hint: The argument(s) "{}" in the commandline "{}" ' \
                   'has(have) no effect in interactive ' \
                   'mode'.format(surplus, self._cmdlineArgs)
            self.console.display_hint(hint)
        try:
            while True:
                action = self.console.get_user_action()
                if action.command == Action.exit:
                    break
                if action.command == Action.display_howto_descriptions:
                    self.console.display_howto_descriptions()
                    continue
                if action.command == Action.display_howto:
                    howto = self.make_howto(action.parameter)
                    self.console.display_howto(howto)
                if action.command == Action.translate:
                    translated_configuration = \
                        self.translator.translate(action.parameter)
                    self.console.display_translation(translated_configuration)
                if action.command == Action.display_command_list:
                    self.console.display_command_list()
                    continue
        except (KeyboardInterrupt, EOFError):
            pass
        self.console.close()
        return 0

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
