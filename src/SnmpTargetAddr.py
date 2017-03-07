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

"""Representation of an SNMP target address as used by EOS.

Classes:
    SnmpTargetAddr - Represents an SNMP target address
"""


class SnmpTargetAddr:

    """Representation of an SNMP target address as used by EOS.

    Available attributes are based on the EOS 'set snmp targetaddr' command.
    Usually there are no SNMP target address configured in the switch
    defaults, so every non-None attribute is considered as a configured
    value.
    """

    def __init__(self):
        self._ip = None
        self._params = None
        self._is_written = False

    def __str__(self):
        return (str(self._ip) + ', ' + str(self._params))

    def set_ip(self, ip):
        self._ip = ip

    def get_ip(self):
        return self._ip

    def set_params(self, params):
        self._params = params

    def get_params(self):
        return self._params

    def is_configured(self):
        return (not (self._ip is None and self._params is None))

    def set_is_written(self, boolean):
        self._is_written = boolean

    def get_is_written(self):
        return self._is_written

    def transfer_config(self, from_addr):
        self._ip = from_addr.get_ip()
        self._params = from_addr.get_params()
        self._is_written = from_addr.get_is_written()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
