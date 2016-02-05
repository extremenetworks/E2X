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

"""Representation of a set of SNMP target parameters as used by EOS.

Classes:
    SnmpTargetParams - Represents a set of SNMP target parameters
"""


class SnmpTargetParams:

    """Representation of a set of SNMP target parameters as used by EOS.

    Available attributes are based on the EOS 'set snmp targetparams' command.
    Usually there are no SNMP target parameters configured in the switch
    defaults, so every non-None attribute is considered as a configured
    value.
    """

    def __init__(self):
        self._user = None
        self._security_model = None
        self._message_processing = None
        self._is_written = False

    def __str__(self):
        s = (str(self._user) + ', ' + str(self._security_model) + ', ' +
             str(self._message_processing))
        return s

    def set_user(self, user):
        self._user = user

    def get_user(self):
        return self._user

    def set_security_model(self, security_model):
        self._security_model = security_model

    def get_security_model(self):
        return self._security_model

    def set_message_processing(self, message_processing):
        self._message_processing = message_processing

    def get_message_processing(self):
        return self._message_processing

    def is_configured(self):
        return (not (self._user is None and self._security_model is None and
                self._message_processing is None))

    def set_is_written(self, boolean):
        self._is_written = boolean

    def get_is_written(self):
        return self._is_written

    def transfer_config(self, from_params):
        self._user = from_params.get_user()
        self._security_model = from_params.get_security_model()
        self._message_processing = from_params.get_message_processing()
        self._is_written = from_params.get_is_written()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
