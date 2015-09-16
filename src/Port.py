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

"""Model the attributes of a switch port."""


class Port:

    """Model the attributes of a switch port.

    This represents a physical port. Some attributes are not applicable
    to logical ports (e.g. a LAG). Use subclassing to represent special
    ports (e.g. stacking ports or logical ports).

    Methods:
    init_conf_values() initializes configurable attributes.
    is_configured() returns if the port has been configured.
    is_equivalent(port) returns if this port can be used in the same role as
    the given port.
    transfer_config(port) transfers the configuration from the given port to
    this port.
    """

    def __init__(self, label, name, data, is_hardware=True):
        self._label = label
        self._name = name
        self._connector = data['type']
        if self._connector.lower() == 'combo':
            self._connector_used = 'rj45'
        else:
            self._connector_used = self._connector
        self._allowed_speeds = data['speedrange']
        self._poe = data['PoE']
        self._is_hardware = is_hardware
        self.init_conf_values()

    def __str__(self):
        description = 'label: ' + self._label + ', '
        description += 'name: ' + self._name + ', '
        description += 'type: ' + self._connector
        if self._connector_used != self._connector:
            description += '(' + self._connector_used + ')'
        description += ', '
        description += 'speeds: ' + str(self._allowed_speeds) + ', '
        description += 'PoE: ' + self._poe + ', '
        description += 'Alias: ' + str(self._description[0]) + ', '
        description += 'Admin State: ' + str(self._admin_state[0]) + ', '
        description += 'Speed: ' + str(self._speed[0]) + ', '
        description += 'Duplex: ' + str(self._duplex[0]) + ', '
        description += 'Auto-Negotiation: ' + str(self._auto_neg[0]) + ', '
        description += 'Jumbo: ' + str(self._jumbo[0]) + ', '
        description += 'LACP: ' + str(self._lacp_enabled[0]) + ', '
        description += 'LACP Admin Actor Key: ' + str(self._lacp_aadminkey[0])
        description += ', STP State: ' + str(self._stp_enabled[0]) + ', '
        description += 'STP Auto Edge: ' + str(self._stp_auto_edge[0]) + ', '
        description += 'STP Admin Edge: ' + str(self._stp_edge[0]) + ', '
        description += 'STP BPDU Guard: ' + str(self._stp_bpdu_guard[0]) + ', '
        description += 'STP BPDU Guard Recovery Time: '
        description += str(self._stp_bpdu_guard_recovery_time[0]) + ', '
        description += 'Inbound ACL: ' + str(self._ipv4_acl_in[0])
        return description

    def init_conf_values(self):
        self._speed = (None, None)
        self._admin_state = (None, None)
        self._duplex = (None, None)
        self._auto_neg = (None, None)
        self._description = (None, None)
        self._short_description = (None, None)
        self._jumbo = (None, None)
        self._lacp_enabled = (None, None)
        self._lacp_aadminkey = (None, None)
        self._stp_enabled = (None, None)
        self._stp_auto_edge = (None, None)
        self._stp_edge = (None, None)
        self._stp_bpdu_guard = (None, None)
        self._stp_bpdu_guard_recovery_time = (None, None)
        self._ipv4_acl_in = ([], None)

    def is_configured(self):
        configured = False
        reason = 'config'
        if (self._speed[1] == reason or
                self._admin_state[1] == reason or
                self._duplex[1] == reason or
                self._auto_neg[1] == reason or
                self._description[1] == reason or
                self._short_description[1] == reason or
                self._jumbo[1] == reason or
                self._lacp_enabled[1] == reason or
                self._lacp_aadminkey[1] == reason or
                self._stp_enabled[1] == reason or
                # ignore auto-edge feature
                self._stp_edge[1] == reason or
                self._stp_bpdu_guard[1] == reason or
                self._stp_bpdu_guard_recovery_time[1] == reason or
                self._ipv4_acl_in[1] == reason):
            configured = True
        return configured

    def is_hardware(self):
        return self._is_hardware

    def get_label(self):
        return self._label

    def get_name(self):
        return self._name

    def get_connector(self):
        return self._connector

    def get_connector_used(self):
        return self._connector_used

    def set_connector_used(self, connector):
        self._connector_used = connector
        return self._connector_used

    def get_possible_speeds(self):
        return self._allowed_speeds

    def get_speed(self):
        return self._speed[0]

    def get_speed_reason(self):
        return self._speed[1]

    def set_speed(self, speed, reason):
        if speed not in self._allowed_speeds:
            return False
        self._speed = (speed, reason)
        return True

    def get_duplex(self):
        return self._duplex[0]

    def get_duplex_reason(self):
        return self._duplex[1]

    def set_duplex(self, mode, reason):
        self._duplex = (mode, reason)
        return self._duplex[0]

    def get_auto_neg(self):
        return self._auto_neg[0]

    def get_auto_neg_reason(self):
        return self._auto_neg[1]

    def set_auto_neg(self, state, reason):
        self._auto_neg = (bool(state), reason)
        return self._auto_neg[0]

    def get_admin_state(self):
        return self._admin_state[0]

    def get_admin_state_reason(self):
        return self._admin_state[1]

    def set_admin_state(self, state, reason):
        self._admin_state = (bool(state), reason)
        return self._admin_state[0]

    def get_description(self):
        return self._description[0]

    def get_description_reason(self):
        return self._description[1]

    def set_description(self, desc, reason):
        self._description = (desc, reason)
        return self._description[0]

    def get_short_description(self):
        return self._short_description[0]

    def get_short_description_reason(self):
        return self._short_description[1]

    def set_short_description(self, desc, reason):
        self._short_description = (desc, reason)
        return self._short_description[0]

    def get_jumbo(self):
        return self._jumbo[0]

    def get_jumbo_reason(self):
        return self._jumbo[1]

    def set_jumbo(self, state, reason):
        self._jumbo = (bool(state), reason)
        return self._jumbo[0]

    def get_lacp_enabled(self):
        return self._lacp_enabled[0]

    def get_lacp_enabled_reason(self):
        return self._lacp_enabled[1]

    def set_lacp_enabled(self, state, reason):
        self._lacp_enabled = (bool(state), reason)
        return self._lacp_enabled[0]

    def get_lacp_aadminkey(self):
        return self._lacp_aadminkey[0]

    def get_lacp_aadminkey_reason(self):
        return self._lacp_aadminkey[1]

    def set_lacp_aadminkey(self, key, reason):
        try:
            key = int(key)
        except:
            return None
        if key < 0 or key > 65535:
            return None
        self._lacp_aadminkey = (key, reason)
        return self._lacp_aadminkey[0]

    def get_stp_enabled(self):
        return self._stp_enabled[0]

    def get_stp_enabled_reason(self):
        return self._stp_enabled[1]

    def set_stp_enabled(self, state, reason):
        self._stp_enabled = (bool(state), reason)
        return self._stp_enabled[0]

    def enable_stp(self, reason):
        return self._set_stp_enabled(True, reason)

    def disable_stp(self, reason):
        return self._set_stp_enabled(False, reason)

    def get_stp_auto_edge(self):
        return self._stp_auto_edge[0]

    def get_stp_auto_edge_reason(self):
        return self._stp_auto_edge[1]

    def set_stp_auto_edge(self, state, reason):
        self._stp_auto_edge = (bool(state), reason)
        return self._stp_auto_edge[0]

    def get_stp_edge(self):
        return self._stp_edge[0]

    def get_stp_edge_reason(self):
        return self._stp_edge[1]

    def set_stp_edge(self, state, reason):
        self._stp_edge = (bool(state), reason)
        return self._stp_edge[0]

    def get_stp_bpdu_guard(self):
        return self._stp_bpdu_guard[0]

    def get_stp_bpdu_guard_reason(self):
        return self._stp_bpdu_guard[1]

    def set_stp_bpdu_guard(self, state, reason):
        self._stp_bpdu_guard = (bool(state), reason)
        return self._stp_bpdu_guard[0]

    def get_stp_bpdu_guard_recovery_time(self):
        return self._stp_bpdu_guard_recovery_time[0]

    def get_stp_bpdu_guard_recovery_time_reason(self):
        return self._stp_bpdu_guard_recovery_time[1]

    def set_stp_bpdu_guard_recovery_time(self, time, reason):
        try:
            rec_time = int(time)
        except:
            return self._stp_bpdu_guard_recovery_time[0]
        self._stp_bpdu_guard_recovery_time = (rec_time, reason)
        return self._stp_bpdu_guard_recovery_time[0]

    def get_ipv4_acl_in(self):
        return self._ipv4_acl_in[0]

    def get_ipv4_acl_in_reason(self):
        return self._ipv4_acl_in[1]

    def set_ipv4_acl_in(self, acl_id, reason):
        tmp_acl_lst = [acl_id]
        self._ipv4_acl_in = (tmp_acl_lst, reason)
        return self._ipv4_acl_in[0]

    def add_ipv4_acl_in(self, acl_id, reason):
        if acl_id not in self._ipv4_acl_in[0]:
            tmp_acl_lst = self._ipv4_acl_in[0]
            tmp_acl_lst.append(acl_id)
            self._ipv4_acl_in = (tmp_acl_lst, reason)
        return self._ipv4_acl_in[0]

    def del_ipv4_acl_in(self, acl_id, reason):
        tmp_acl_lst = self._ipv4_acl_in[0]
        if acl_id in tmp_acl_lst:
            tmp_acl_lst.remove(acl_id)
        self._ipv4_acl_in = (tmp_acl_lst, reason)
        return self._ipv4_acl_in[0]

    def is_equivalent(self, port):
        """Returns True if given port can be used in the same role as this."""
        # prefer identical ports
        if (self._connector == port.get_connector() and
                self._allowed_speeds == port.get_possible_speeds()):
            return True
        # prefer ports with same connector in use and same speeds
        elif (self._connector_used == port.get_connector_used() and
              self._allowed_speeds == port.get_possible_speeds()):
            return True
        # accept ports with same connector in use and same maximum speeds
        elif (self._connector_used == port.get_connector_used() and
              max(self._allowed_speeds) == max(port.get_possible_speeds())):
            return True
        # accept use of combo port for SFP port if same maximum speed
        elif (self._connector == 'combo' and port.get_connector() == 'sfp' and
              max(self._allowed_speeds) == max(port.get_possible_speeds())):
            return True
        else:
            return False

    def transfer_config(self, from_port):

        """Transfer configuration of from_port to this port."""

        reason_def = 'transfer_def'
        reason_conf = 'transfer_conf'

        t_speed = from_port.get_speed()
        if t_speed is not None and self._speed[0] != t_speed:
            if from_port.get_speed_reason() == 'default':
                self._speed = (t_speed, reason_def)
            else:
                self._speed = (t_speed, reason_conf)

        t_duplex = from_port.get_duplex()
        if t_duplex is not None and self._duplex[0] != t_duplex:
            if from_port.get_duplex_reason() == 'default':
                self._duplex = (t_duplex, reason_def)
            else:
                self._duplex = (t_duplex, reason_conf)

        t_auto_neg = from_port.get_auto_neg()
        if t_auto_neg is not None and self._auto_neg[0] != t_auto_neg:
            if from_port.get_auto_neg_reason() == 'default':
                self._auto_neg = (t_auto_neg, reason_def)
            else:
                self._auto_neg = (t_auto_neg, reason_conf)

        t_admin_state = from_port.get_admin_state()
        if self._admin_state[0] != t_admin_state:
            if from_port.get_admin_state_reason() == 'default':
                self._admin_state = (t_admin_state, reason_def)
            else:
                self._admin_state = (t_admin_state, reason_conf)

        t_description = from_port.get_description()
        if self._description[0] != t_description:
            if from_port.get_description_reason() == 'default':
                self._description = (t_description, reason_def)
            else:
                self._description = (t_description, reason_conf)

        t_short_description = from_port.get_short_description()
        if self._short_description[0] != t_short_description:
            if from_port.get_short_description_reason() == 'default':
                self._short_description = (t_short_description, reason_def)
            else:
                self._short_description = (t_short_description, reason_conf)

        t_jumbo = from_port.get_jumbo()
        if t_jumbo is not None and self._jumbo[0] != t_jumbo:
            if from_port.get_jumbo_reason() == 'default':
                self._jumbo = (t_jumbo, reason_def)
            else:
                self._jumbo = (t_jumbo, reason_conf)

        t_lacp_enabled = from_port.get_lacp_enabled()
        if self._lacp_enabled[0] != t_lacp_enabled:
            t_reason = (reason_def
                        if from_port.get_lacp_enabled_reason() == 'default'
                        else reason_conf)
            self._lacp_enabled = (t_lacp_enabled, t_reason)

        t_lacp_aadminkey = from_port.get_lacp_aadminkey()
        if self._lacp_aadminkey[0] != t_lacp_aadminkey:
            t_reason = (reason_def
                        if from_port.get_lacp_aadminkey_reason() == 'default'
                        else reason_conf)
            self._lacp_aadminkey = (t_lacp_aadminkey, t_reason)

        t_stp_enabled = from_port.get_stp_enabled()
        if self._stp_enabled[0] != t_stp_enabled:
            t_reason = (reason_def
                        if from_port.get_stp_enabled_reason() == 'default'
                        else reason_conf)
            self._stp_enabled = (t_stp_enabled, t_reason)

        t_stp_auto_edge = from_port.get_stp_auto_edge()
        if self._stp_auto_edge[0] != t_stp_auto_edge:
            t_reason = (reason_def
                        if from_port.get_stp_auto_edge_reason() == 'default'
                        else reason_conf)
            self._stp_auto_edge = (t_stp_auto_edge, t_reason)

        t_stp_edge = from_port.get_stp_edge()
        if self._stp_edge[0] != t_stp_edge:
            t_reason = (reason_def
                        if from_port.get_stp_edge_reason() == 'default'
                        else reason_conf)
            self._stp_edge = (t_stp_edge, t_reason)

        t_stp_bpdu_guard = from_port.get_stp_bpdu_guard()
        if self._stp_bpdu_guard[0] != t_stp_bpdu_guard:
            t_reason = (reason_def
                        if from_port.get_stp_bpdu_guard_reason() == 'default'
                        else reason_conf)
            self._stp_bpdu_guard = (t_stp_bpdu_guard, t_reason)

        t_stp_bpdu_guard_recovery_time = \
            from_port.get_stp_bpdu_guard_recovery_time()
        if (self._stp_bpdu_guard_recovery_time[0] !=
                t_stp_bpdu_guard_recovery_time):
            t_reason = \
                (reason_def
                 if (from_port.get_stp_bpdu_guard_recovery_time_reason() ==
                     'default')
                 else reason_conf)
            self._stp_bpdu_guard_recovery_time = \
                (t_stp_bpdu_guard_recovery_time, t_reason)

        t_ipv4_acl_in = from_port.get_ipv4_acl_in()
        if t_ipv4_acl_in is not None and self._ipv4_acl_in[0] != t_ipv4_acl_in:
            if from_port.get_ipv4_acl_in_reason() == 'default':
                self._ipv4_acl_in = (t_ipv4_acl_in, reason_def)
            else:
                self._ipv4_acl_in = (t_ipv4_acl_in, reason_conf)

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
