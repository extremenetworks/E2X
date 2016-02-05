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

"""Model a link aggregation group (LAG)."""

import Port


class LAG(Port.Port):

    """Model a link aggregation group (LAG).

    A LAG is a kind of logical port, thus this is a specialization of the
    Port class.

    Properties that pertain to physical ports only (e.g. speed and duplex)
    are removed/ignored.

    Properties specific to an LAG (e.g. member ports) have been added.
    """

    def __init__(self, number, name=None, use_lacp=None, aadminkey=None):
        self._data = {"type": "LAG", "speedrange": [], "PoE": "no"}
        super().__init__(number, name, self._data, False)
        self._lacp_enabled = (use_lacp, None)
        self._lacp_aadminkey = (aadminkey, None)
        self._members = []

    def __str__(self):
        description = 'Number: ' + str(self._label)
        description += ', Name: ' + str(self._name)
        description += ', LACP: ' + str(self._lacp_enabled[0])
        description += ', Actor Admin Key: ' + str(self._lacp_aadminkey[0])
        description += ', Alias: ' + str(self._description[0])
        description += ', Admin State: ' + str(self._admin_state[0])
        return description

    def is_disabled_only(self):
        reason = 'config'
        return (not self._admin_state[0] and
                self._admin_state[1] == reason and
                self._description[1] != reason and
                self._short_description[1] != reason and
                self._lacp_enabled[1] != reason and
                self._lacp_aadminkey[1] != reason)

    def accidental_config_only(self):
        """Some commands affect all ports of the switch, including LAGs.

        Having such a configuration affecting a LAG does not imply the LAG
        is actually used.
        """
        reason = 'config'
        if (self._speed[1] == reason or
                # ignore admin state (set port disable *.*.*)
                self._duplex[1] == reason or
                self._auto_neg[1] == reason or
                self._description[1] == reason or
                self._short_description[1] == reason or
                self._jumbo[1] == reason or
                self._lacp_enabled[1] == reason or
                self._lacp_aadminkey[1] == reason or
                self._stp_enabled[1] == reason or
                # ignore switch-wide, on-by-default auto-edge feature
                self._stp_edge[1] == reason or
                # ignore SpanGuard (en/disabled per switch)
                self._ipv4_acl_in[1] == reason):
            return False
        return True

    def set_speed(self, speed, reason):
        return True

    def set_duplex(self, mode, reason):
        return None

    def set_auto_neg(self, state, reason):
        return None

    def set_jumbo(self, state, reason):
        return None

    def get_members(self):
        return self._members

    def add_member_port(self, portname):
        if not portname:
            return False
        if portname not in self._members:
            self._members.append(portname)
        return True

    def get_master_port(self):
        if self._members:
            return self._members[0]

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
