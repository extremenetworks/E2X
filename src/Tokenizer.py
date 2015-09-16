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

"""Tokenizer Module to help parsing configuration command lines.

Classes:
    Tokenizer - generic tokenizer

>>> tt = [('QUOTED_WORD', '["][^"]*["]'), ('WORD', r'\S+'), ('SPACE', r'\s+')]
>>> T = Tokenizer(tt)
>>> for tok in T.generate_tokens('one two three'): print(tok)
...
Token(t='WORD', v='one')
Token(t='SPACE', v=' ')
Token(t='WORD', v='two')
Token(t='SPACE', v=' ')
Token(t='WORD', v='three')
>>> for tok in T.generate_tokens('"one two" three'): print(tok)
...
Token(t='QUOTED_WORD', v='"one two"')
Token(t='SPACE', v=' ')
Token(t='WORD', v='three')
>>> for tok in T.generate_tokens('one "two" three'): print(tok)
...
Token(t='WORD', v='one')
Token(t='SPACE', v=' ')
Token(t='QUOTED_WORD', v='"two"')
Token(t='SPACE', v=' ')
Token(t='WORD', v='three')
>>> for tok in T.generate_tokens('one "two three"'): print(tok)
...
Token(t='WORD', v='one')
Token(t='SPACE', v=' ')
Token(t='QUOTED_WORD', v='"two three"')
"""

from collections import namedtuple
import re


class Tokenizer:

    """Generic Tokenizer.

    A list of tuples (TYPE, REGEX) describing the tokens needs to be provided.
    """

    _token = namedtuple('Token', ('t', 'v'))

    def __init__(self, token_types):
        token_regex = '|'.join('(?P<%s>%s)' % tt for tt in token_types)
        self._compiled_token_regex = re.compile(token_regex)

    def generate_tokens(self, line):
        for m in self._compiled_token_regex.finditer(line):
            yield self._token(m.lastgroup, m.group())

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
