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

"""Representation of an SNTP server configuration.

Classes:
    SntpServer - Represents configuration options for an SNTP server
"""


class SntpServer:

    """Representation of an SNTP server as seen from a switch.

    Available attributes are based on the EOS 'set sntp server' command.
    Usually there is no remote syslog server configured in the switch
    defaults, so every non-None attribute is considered as a configured
    value.
    """

    def __init__(self):
        self._attributes = {}
        self._is_configured = None
        self._is_written = False

    def __str__(self):
        s = ''
        for (k, v) in self._attributes.items():
            s += ' ' + str(k).capitalize() + ': ' + str(v) + ','
        return s[:-1]

    def set_precedence(self, precedence):
        self._attributes['precedence'] = precedence

    def get_precedence(self):
        return self._attributes.get('precedence')

    def get_default_precedence(self):
        return self._attributes.get('def_precedence')

    def set_ip(self, ip):
        self._attributes['ip'] = ip

    def get_ip(self):
        return self._attributes.get('ip')

    def get_attributes(self):
        return self._attributes

    def update_attributes(self, attrs):
        self._attributes.update(attrs)

    def set_is_configured(self, boolean):
        self._is_configured = boolean

    def get_is_configured(self):
        return self._is_configured

    def set_is_written(self, boolean):
        self._is_written = boolean

    def get_is_written(self):
        return self._is_written

    def transfer_config(self, from_sntp_conf):
        self._attributes.update(from_sntp_conf.get_attributes())
        self._is_configured = from_sntp_conf.get_is_configured()
        self._is_written = from_sntp_conf.get_is_written()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
