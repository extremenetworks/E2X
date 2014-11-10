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

"""Utility functions for E2X.

This is used for generic utility functions that are not obviously part
of a class.

Functions:
expand_sequence(sequence) expands a sequence given as a string into a list.
expand_sequence_to_int_list(sequence) expands a sequence of integers given as
a string into a list.
create_compact_sequence(lst) creates a sequence string from a list of integers.
create_sequence(lst) creates a sequence string from a list.
"""


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
    """Create a sequence string from a list of integer elements.

    The list needs to be sortable. If possible, integer elements
    will be aggregated in ranges.

    The sequence is returned as a string.

    >>> create_compact_sequence([1])
    '1'
    >>> create_compact_sequence(['1'])
    '1'
    >>> create_compact_sequence([1, '1', 1])
    '1'
    >>> create_compact_sequence([3, 1, 2, '5', 4])
    '1-5'
    >>> create_compact_sequence([3, 7, 1, 2, 10, 11, '5', 4, 9, 15])
    '1-5,7,9-11,15'
    """

    try:
        lst = [int(x) for x in lst]
        lst.sort()
    except:
        return ''
    ret = ''
    last = None
    in_range = False
    for i in lst:
        if not last:
            ret += str(i)
        elif i == last:
            continue
        elif i - last == 1:
            in_range = True
        elif in_range:
            ret += '-' + str(last) + ',' + str(i)
            in_range = False
        else:
            ret += ',' + str(i)
        last = i
    if in_range:
        ret += '-' + str(last)
    return ret


def create_sequence(lst):
    """Create a sequence string from a list of elements.

    Each list element is converted to a string, then the list is sorted.

    The sequence is returned as a string.

    >>> create_sequence([1])
    '1'
    >>> create_sequence(['1'])
    '1'
    >>> create_sequence([1, '1', 1])
    '1'
    >>> create_sequence([3, 1, 2, '5', 4])
    '1,2,3,4,5'
    >>> create_sequence([3, 7, 1, 2, 10, 11, '5', 4, 9, 15])
    '1,10,11,15,2,3,4,5,7,9'
    >>> create_sequence(['1:2','1:1'])
    '1:1,1:2'
    >>> create_sequence(['1:2','1:1','1:11'])
    '1:1,1:11,1:2'
    """
    # TODO: Implement and use a sort function for port names

    try:
        lst = [str(x) for x in lst]
        lst.sort()
    except:
        return ''
    ret = lst.pop(0)
    last = ret
    for i in lst:
        if i != last:
            ret += ',' + i
            last = i
    return ret

# hook for the doctest Python module
if __name__ == "__main__":
    import doctest
    doctest.testmod()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
