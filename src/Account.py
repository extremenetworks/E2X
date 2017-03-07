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

# Copyright 2014-2017 Extreme Networks, Inc.  All rights reserved.
# Use is subject to license terms.

# This file is part of e2x (translate EOS switch configuration to ExtremeXOS)

"""Representation of a user account.

Classes:
    SnmpTargetAddr - Represents a user account
"""


class UserAccount:

    """Representation of a user account.

    Available attributes are based on the basics needed to describe a user.
    Switches may have default users. The user type is based on EOS.
    Default accounts are assumed to be enabled.
    """

    def __init__(self):
        self._is_default = None
        self._name = None
        self._type = None
        self._state = None
        self._password = None
        self._is_written = False

    def __str__(self):
        d = 'Default, ' if self._is_default else 'Non-Default, '
        d += str(self._name) + ', ' + str(self._type) + ', '
        d += str(self._state) + ', ' + str(self._password)
        return d

    def set_is_default(self, boolean):
        self._is_default = boolean

    def get_is_default(self):
        return self._is_default

    def set_name(self, name):
        self._name = name

    def get_name(self):
        return self._name

    def set_type(self, _type):
        self._type = _type

    def get_type(self):
        return self._type

    def set_state(self, state):
        self._state = state

    def get_state(self):
        return self._state

    def set_password(self, password):
        self._password = password

    def get_password(self):
        return self._password

    def is_configured(self):
        return ((self._is_default is False) or (self._state == 'disabled') or
                (self._password is not None))

    def set_is_written(self, boolean):
        self._is_written = boolean

    def get_is_written(self):
        return self._is_written

    def transfer_config(self, from_account):
        self._is_default = from_account.get_is_default()
        self._name = from_account.get_name()
        self._type = from_account.get_type()
        self._state = from_account.get_state()
        self._password = from_account.get_password()
        self._is_written = from_account.get_is_written()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
