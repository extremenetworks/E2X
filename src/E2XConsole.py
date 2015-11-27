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

import importlib

from Action import Action
from InteractiveModeCommandList import INT_MODE_CMD_LST


class E2XConsole:

    def __init__(self, use_curses=False, prompt='> ', howto_descr=None):
        self.screen = SysInOutConsole(prompt, howto_descr)
        if use_curses:
            try:
                curses = importlib.import_module('curses')
                self.screen = CursesConsole(curses)
            except ImportError:
                try:
                    curses = importlib.import_module('unicurses')
                    self.screen = CursesConsole(curses)
                except ImportError:
                    pass
        try:
            import readline  # noqa (avoid false flake8 warning)
        except ImportError:
            pass

    def get_screen(self):
        return self.screen

    def display_intro(self, string):
        self.screen.display_intro(string)

    def get_user_action(self):
        return self.screen.get_user_action()

    def close(self):
        self.screen.close()

    def display_hint(self, text):
        self.screen.display_hint(text)

    def display_howto_descriptions(self):
        self.screen.display_howto_descriptions()

    def display_command_list(self):
        self.screen.display_command_list()

    def display_howto(self, howto):
        self.screen.display_howto(howto)

    def display_translation(self, translation):
        self.screen.display_translation(translation)


class SysInOutConsole:
    def __init__(self, prompt, howto_descr_list):
        self.howto_descriptions_dict = \
            self._build_howto_descriptions_dict(howto_descr_list)
        self.howtos_key_range = \
            self._build_key_range(self.howto_descriptions_dict.keys())
        self._breaking_seq = {'q': Action.exit,
                              'howtos': Action.display_howto_descriptions,
                              'commands': Action.display_command_list,
                              }
        self.info = 'Enter ' + self.howtos_key_range + ' to select HowTo\n' + \
                    'Enter "q" to quit'
        self.info_option = 'Enter "HowTos" or "commands" to show list'
        self.prompt = prompt

    def close(self):
        self._print_empty_lines(1)

    def display_intro(self, str):
        print(str)
        self._print_empty_lines(1)
        self._display_info(self.info_option)

    def _display_info(self, option=''):
        info = ''
        if option:
            info = option + '\n'
        info += self.info + '\n'
        print(info)

    def display_hint(self, hint):
        print(hint)
        self._print_empty_lines(1)

    def _build_key_range(self, list):
        size = len(list)
        if size == 0:
            return ""
        if size == 1:
            return '"1"'
        else:
            return 'number from "1" to "' + str(size) + '"'

    def _build_howto_descriptions_dict(self, howto_descriptions_list):
        descr_dict = {}
        if not howto_descriptions_list:
            return descr_dict
        for index, desc in enumerate(howto_descriptions_list):
            desc_nr = str(index + 1)
            descr_dict[desc_nr] = desc
        return descr_dict

    def display_howto_descriptions(self):
        self._print_empty_lines(1)
        print('List of HowTos:')
        for index in sorted(self.howto_descriptions_dict.keys(), key=int):
            desc = self.howto_descriptions_dict[index]
            print('  {:>2}: {}'.format(index, desc))
        self._print_empty_lines(1)
        self._display_info()

    def display_command_list(self):
        self._print_empty_lines(1)
        print('Supported EOS commands:')
        print(INT_MODE_CMD_LST)
        self._display_info()

    def _condensed_line(self, line):
        return ' '.join(line.split())

    def _print_text(self, line_prefix, text):
        for line in text.splitlines():
            line = line.strip()
            print(line_prefix + self._condensed_line(line))

    def _print_empty_lines(self, nr):
        for n in range(nr):
            print()

    def _display_translation_and_hint(self, translation):
        xos = translation.get_xos()
        hint = translation.get_hint()
        if xos:
            print(xos)
        if hint:
            print('% ' + hint)

    def _display_info_triple(self, info):
        self._print_empty_lines(1)
        print(' EOS')
        self._print_text(' '*3, info.get_eos())
        self._print_empty_lines(1)
        print(' XOS')
        self._print_text(' '*3, info.get_xos())
        self._print_empty_lines(1)
        print(' Hint')
        self._print_text(' '*3, info.get_hint())
        self._print_empty_lines(2)

    def display_howto(self, howto):
        self._print_empty_lines(2)
        print('HowTo ' + howto.get_description() + ':')
        self._display_info_triple(howto)
        self._display_info(self.info_option)

    def display_translation(self, translation):
        self._display_translation_and_hint(translation)

    def get_user_action(self):
        entry = input(self.prompt)
        action = Action()
        action.command = Action.translate   # Default action
        action.parameter = entry
        if entry.lower() in self._breaking_seq:
            action.command = self._breaking_seq[entry.lower()]
        if entry in sorted(self.howto_descriptions_dict.keys()):
            action.command = Action.display_howto
            action.parameter = self.howto_descriptions_dict[entry]
        return action


class CursesConsole:
    def __init__(self, curses):
        self.curses = curses
        self.stdscr = self.curses.initscr()
        self.stdscr.clear()

    def close(self):
        self.curses.endwin()

    def display_intro(self, intro):
        self.curses.curs_set(0)
        self.stdscr.addstr(intro, self.curses.A_REVERSE)
        self.stdscr.chgat(-1, self.curses.A_REVERSE)

    def display_hint(self, hint):
        pass

    def display_info(self, info):
        self.stdscr.addstr(self.curses.LINES - 1, 0, info)

    def display_howto_descriptions(self, description_list):
        pass

    def display_howto(self, howto):
        pass

    def get_user_action(self):
        action = Action()
        c = self.stdscr.getch()
        if c == ord('q') or c == ord('Q'):
            action.command = Action.exit
        return action

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
