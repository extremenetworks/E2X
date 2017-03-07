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

"""Representation of a TACACS+ server configuration.

Classes:
    TacacsServer - Represents configuration options for a TACACS+ server
"""


class TacacsServer:

    """Representation of a TACACS+ server as seen from a switch.

    Available attributes are based on the EOS 'set tacacs' command.
    Usually there is no TACACS+ server configured in the switch
    defaults, so every non-None attribute is considered as a configured
    value.
    """

    def __init__(self):
        self._ip = None
        self._port = None
        self._secret = None
        self._is_configured = False
        self._is_written = False

    def __str__(self):
        s = (str(self._ip) + ':' + str(self._port) + ', ' + str(self._secret) +
             ', ' + str(self._realm))
        return s

    def set_ip(self, ip):
        self._ip = ip

    def get_ip(self):
        return self._ip

    def set_port(self, port):
        self._port = port

    def get_port(self):
        return self._port

    def set_secret(self, secret):
        self._secret = secret

    def get_secret(self):
        return self._secret

    def set_is_configured(self, boolean):
        self._is_configured = boolean

    def get_is_configured(self):
        return self._is_configured

    def set_is_written(self, boolean):
        self._is_written = boolean

    def get_is_written(self):
        return self._is_written

    def transfer_config(self, from_tacacs_conf):
        self._ip = from_tacacs_conf.get_ip()
        self._port = from_tacacs_conf.get_port()
        self._secret = from_tacacs_conf.get_secret()
        self._is_configured = from_tacacs_conf.get_is_configured()
        self._is_written = from_tacacs_conf.get_is_written()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
