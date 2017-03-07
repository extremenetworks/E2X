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

"""Representation of a syslog server configuration.

Classes:
    SyslogServer - Represents configuration options for a syslog server
"""


class SyslogServer:

    """Representation of a remote syslog server as seen from a switch.

    Available attributes are based on the EOS 'set logging server' command.
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

    def set_description(self, descr):
        self._attributes['descr'] = descr

    def get_description(self):
        return self._attributes.get('descr')

    def set_facility(self, facility):
        self._attributes['facility'] = facility

    def get_facility(self):
        return self._attributes.get('facility')

    def get_default_facility(self):
        return self._attributes.get('def_facility')

    def set_ip(self, ip):
        self._attributes['ip'] = ip

    def get_ip(self):
        return self._attributes.get('ip')

    def set_port(self, port):
        self._attributes['port'] = port

    def get_port(self):
        return self._attributes.get('port')

    def get_default_port(self):
        return self._attributes.get('def_port')

    def set_severity(self, severity):
        self._attributes['severity'] = severity

    def get_severity(self):
        return self._attributes.get('severity')

    def get_default_severity(self):
        return self._attributes.get('def_severity')

    def set_state(self, state):
        self._attributes['state'] = state

    def get_state(self):
        return self._attributes.get('state')

    def get_default_state(self):
        return self._attributes.get('def_state')

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

    def transfer_config(self, from_syslog_conf):
        self._attributes.update(from_syslog_conf.get_attributes())
        self._is_configured = from_syslog_conf.get_is_configured()
        self._is_written = from_syslog_conf.get_is_written()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
