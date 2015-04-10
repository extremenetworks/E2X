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

"""Utility functions for E2X.

This is used for generic utility functions that are not obviously part
of a class.

Functions:
expand_sequence(sequence) expands a sequence given as a string into a list.
expand_sequence_to_int_list(sequence) expands a sequence of integers given as
a string into a list.
create_compact_sequence(lst) creates a sequence string from a list of integers.
create_sequence(lst) creates a sequence string from a list.
words_to_lower(lines, words) converts every instance of words found in lines
to lower case.
"""

import re


def expand_sequence(sequence):
    """Expand a string describing a sequence of elements.

    The sequence can contain commata to separate individual elements
    and hyphens to delineate ranges. Ranges must be integer ranges.
    The sequence can contain non-integers as simple, that is non-range,
    elements.

    The expanded sequence is returned as a list.

    >>> expand_sequence('1-2,5,7,10,12-15')
    ['1', '2', '5', '7', '10', '12', '13', '14', '15']
    >>> expand_sequence('10')
    ['10']
    >>> expand_sequence('ge,tg')
    ['ge', 'tg']
    >>> expand_sequence('*')
    ['*']
    """
    ret = []
    lst_of_ranges = sequence.split(',')
    for r in lst_of_ranges:
        if '-' in r:
            tmp = r.split('-')
            tmp = range(int(tmp[0]), int(tmp[1]) + 1)
            ret.extend([str(x) for x in tmp])
        else:
            ret.append(r)
    return ret


def expand_sequence_to_int_list(sequence):
    """Expand a string describing a sequence of elements.

    The sequence can contain commata to separate individual elements
    and hyphens to delineate ranges. All elements must be integers.

    The expanded sequence is returned as a list of integers.

    >>> expand_sequence_to_int_list('1-2,5,7,10,12-15')
    [1, 2, 5, 7, 10, 12, 13, 14, 15]
    >>> expand_sequence_to_int_list('10')
    [10]
    >>> expand_sequence_to_int_list('ge,tg')
    []
    >>> expand_sequence_to_int_list('*')
    []
    """
    ret = []
    lst = expand_sequence(sequence)
    try:
        lst = [int(s) for s in lst]
        return lst
    except:
        return ret


def create_compact_sequence(lst):
    """Create a sequence string from a list of EXOS port names.

    The list needs to be sortable. If possible, EXOS port names
    will be aggregated in ranges. Note that integers are syntactically
    valid EXOS port names.

    The sequence is returned as a string.

    >>> create_compact_sequence([1])
    '1'
    >>> create_compact_sequence(['1'])
    '1'
    >>> create_compact_sequence([1, '1', 1])
    '1'
    >>> create_compact_sequence([3, 4, 6, 7])
    '3-4,6-7'
    >>> create_compact_sequence([3, 1, 2, '5', 4])
    '1-5'
    >>> create_compact_sequence([3, 7, 1, 2, 10, 11, '5', 4, 9, 15])
    '1-5,7,9-11,15'
    >>> create_compact_sequence(['1:1'])
    '1:1'
    >>> create_compact_sequence(['1:1', '1:1', '1:1'])
    '1:1'
    >>> create_compact_sequence(['1:3', '1:1', '1:2', '1:5', '1:4'])
    '1:1-5'
    >>> lst=['1:3','1:7','1:1','1:2','1:10','1:11','1:5','1:4','1:9','1:15']
    >>> create_compact_sequence(lst)
    '1:1-5,1:7,1:9-11,1:15'
    >>> lst=['2:3','2:7','2:1','2:2','2:10','2:11','2:5','2:4','2:9','2:15']
    >>> create_compact_sequence(lst)
    '2:1-5,2:7,2:9-11,2:15'
    >>> lst=['1:3','1:7','1:1','1:2','1:10','1:11','1:5','1:4','1:9','1:15']
    >>> lst+=['2:3','2:7','2:1','2:2','2:10','2:11','2:5','2:4','2:9','2:15']
    >>> create_compact_sequence(lst)
    '1:1-5,1:7,1:9-11,1:15,2:1-5,2:7,2:9-11,2:15'
    >>> create_compact_sequence(['1:3', '1:4', '2:5', '2:6'])
    '1:3-4,2:5-6'
    >>> create_compact_sequence(['no', 'good'])
    ''
    >>> create_compact_sequence(['ge.1.1', 'ge.1.2'])
    ''
    >>> create_compact_sequence([1.1])
    ''
    >>> create_compact_sequence([1.1, 1.2])
    ''
    >>> create_compact_sequence([])
    ''
    >>> create_compact_sequence(['1:1', '1'])
    ''
    >>> create_compact_sequence(['1:1', '2'])
    ''
    >>> create_compact_sequence(['1:1', '100000'])
    ''
    >>> create_compact_sequence(['1:1', 'ge.1.2'])
    ''
    >>> create_compact_sequence(['1', 'ge.1.2'])
    ''
    """

    try:
        lst = list({str(x) for x in lst})
        lst.sort(key=port_sort_key)
    except:
        return ''
    ret = ''
    last_port = None
    in_range = False
    name_format = None
    for i in lst:
        try:
            slot, port = i.split(':')
            if name_format is not None and name_format != 'EXOS_STACK':
                return ''
            elif name_format is None:
                name_format = 'EXOS_STACK'
        except:
            slot, port = 0, i
            if name_format is not None and name_format != 'EXOS':
                return ''
            elif name_format is None:
                name_format = 'EXOS'
        try:
            slot, port = int(slot), int(port)
        except:
            return ''
        if not last_port:
            ret += (str(slot) + ':' + str(port)) if slot else str(port)
        elif port == last_port:
            continue
        elif last_slot == slot and port - last_port == 1:
            in_range = True
        elif in_range:
            ret += '-' + str(last_port)
            ret += ',' + ((str(slot) + ':' + str(port)) if slot else str(port))
            in_range = False
        else:
            ret += ',' + ((str(slot) + ':' + str(port)) if slot else str(port))
        last_slot, last_port = slot, port
    if in_range:
        ret += '-' + str(last_port)
    return ret


def port_sort_key(pname):
    """Build a sort key from a port name to sort a list of ports.

    >>> port_sort_key(1)
    1
    >>> port_sort_key('1')
    1
    >>> port_sort_key('1:1')
    1001
    >>> port_sort_key('16:17')
    16017
    >>> port_sort_key('ge.1.1')
    301001
    >>> port_sort_key('fe.1.1')
    201001
    >>> port_sort_key('tg.2.3')
    402003
    >>> port_sort_key('fg.4.10')
    504010
    >>> port_sort_key('lag.0.6')
    1000006
    >>> port_sort_key('some string')
    'some string'
    >>> port_sort_key('1:2:3')
    '1:2:3'
    >>> port_sort_key('a:2')
    'a:2'
    >>> port_sort_key('')
    ''
    """
    try:
        k = int(pname)
        return k
    except:
        pass
    key_val = {'fe': 200000, 'ge': 300000, 'tg': 400000, 'fg': 500000,
               'lag': 1000000, }
    if ':' in pname:
        lst = pname.split(':')
        if len(lst) == 2:
            try:
                return int(lst[0]) * 1000 + int(lst[1])
            except:
                pass
    elif '.' in pname:
        lst = pname.split('.')
        if len(lst) == 3:
            try:
                return key_val[lst[0]] + int(lst[1]) * 1000 + int(lst[2])
            except:
                pass
    return pname


def create_sequence(lst):
    """Create a sequence string from a list of elements.

    Each list element is converted to a string, then the list is sorted.

    The sequence is returned as a string.

    >>> create_sequence([])
    ''
    >>> create_sequence([1])
    '1'
    >>> create_sequence(['1'])
    '1'
    >>> create_sequence([1, '1', 1])
    '1'
    >>> create_sequence([3, 1, 2, '5', 4])
    '1,2,3,4,5'
    >>> create_sequence([3, 7, 1, 2, 10, 11, '5', 4, 9, 15])
    '1,2,3,4,5,7,9,10,11,15'
    >>> create_sequence(['1:2','1:1'])
    '1:1,1:2'
    >>> create_sequence(['1:2','1:1','1:11'])
    '1:1,1:2,1:11'
    """
    try:
        lst = [str(x) for x in lst]
        lst.sort(key=port_sort_key)
        ret = lst.pop(0)
    except:
        return ''
    last = ret
    for i in lst:
        if i != last:
            ret += ',' + i
            last = i
    return ret


def words_to_lower(lines, words, comments):
    """Convert all words found in lines to lower case.

    Quoted (using double quotes) or comment strings are kept unchanged.

    >>> words_to_lower(['FOO BAR BAZ'], {'foo', 'baz'}, '')
    ['foo BAR baz']
    >>> words_to_lower(['FOO BAR BAZ'], {'foo', 'bar'}, '')
    ['foo bar BAZ']
    >>> words_to_lower('FOO BAR BAZ', {'foo', 'baz'}, '')
    ['foo BAR baz']
    >>> words_to_lower(['FOO.BAR-BAZ'], {'foo', 'baz'}, '')
    ['FOO.BAR-BAZ']
    >>> words_to_lower('FOO.BAR-BAZ', {'foo', 'baz'}, '')
    ['FOO.BAR-BAZ']
    >>> words_to_lower(['SET VLAN NAME MYVLANNAME'], {'set', 'vlan', 'name'},\
                        '')
    ['set vlan name MYVLANNAME']
    >>> words_to_lower('set', {'set'}, '')
    ['set']
    >>> words_to_lower('SET SEt sET SeT Set sEt seT', {'set'}, '')
    ['set set set set set set set']
    >>> words_to_lower(['SET SEt sET SeT Set sEt seT'], {'clear'}, '')
    ['SET SEt sET SeT Set sEt seT']
    >>> words_to_lower('set port alias ge.1.17 "WLC Port 1"', \
                       {'set', 'port', 'alias'}, '#!')
    ['set port alias ge.1.17 "WLC Port 1"']
    >>> words_to_lower('! FOO', {'foo'}, '#!')
    ['! FOO']
    >>> words_to_lower('# FOO', {'foo'}, ['#', '!'])
    ['# FOO']
    >>> words_to_lower('// FOO', {'foo'}, ['#', '!'])
    ['// foo']
    >>> words_to_lower('" FOO "', {'foo'}, ['!'])
    ['" FOO "']
    >>> words_to_lower(' FOO ""', {'foo'}, ['!'])
    ['foo ""']
    >>> words_to_lower(' FOO "', {'foo'}, ['!'])
    ['foo "']
    >>> words_to_lower(' FOO"', {'foo'}, ['!'])
    ['FOO"']
    >>> words_to_lower('Foo " FOO " FoO', {'foo'}, ['!'])
    ['foo " FOO " foo']
    >>> words_to_lower('Foo " FOO  FoO', {'foo'}, ['!'])
    ['foo " FOO  FoO']
    >>> words_to_lower('Foo "FOO" FoO', {'foo'}, ['!'])
    ['foo "FOO" foo']
    >>> words_to_lower('Foo "FOO !Foo fOO" FoO', {'foo'}, ['!'])
    ['foo "FOO !Foo fOO" foo']
    >>> words_to_lower('Foo FOO !Foo fOO FoO', {'foo'}, ['!'])
    ['foo foo !Foo fOO FoO']
    >>> words_to_lower('set system contact "Switch 1', set(), [])
    ['set system contact "Switch 1']
    >>> words_to_lower('set system contact "Switch 1', set(), ['!', '#'])
    ['set system contact "Switch 1']
    >>> words_to_lower('set system contact "Switch 1', {'switch'}, [])
    ['set system contact "Switch 1']
    """

    result = []
    token_start = r'(?:^|\s+)'
    comment_chars = ''.join(list(comments))
    comment_regex = "|".join([c + '.*' for c in list(comments)])
    token_content = (r'([^\s"' + comment_chars + ']+"?|"[^"]*"?|' +
                     comment_regex + ')')
    token_end = r'(?=$|\s+)'
    scanner_regex = token_start + token_content + token_end
    scanner = re.compile(scanner_regex, flags=re.IGNORECASE)
    if type(lines) is not list:
        lines = [lines]
    for l in lines:
        normalized_lst = []
        token_lst = scanner.sub(lambda m: m.group(1) + '‖', l).split('‖')[:-1]
        for t in token_lst:
            if t.lower() in words:
                normalized_lst.append(t.lower())
            else:
                normalized_lst.append(t)
        result.append(' '.join(normalized_lst))
    return result

# hook for the doctest Python module
if __name__ == "__main__":
    import doctest
    doctest.testmod()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
