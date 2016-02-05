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

"""Model the Spanning Tree Protocol (STP)."""


class STP():

    """Model the Spanning Tree Protocol (STP).

    Methods:
    is_basic_stp_config() returns if the configuration is a basic STP
    often enabled by default on managed switches (with possible tweaks).
    transfer_config(from_stp) transfers the configuration of from_stp to
    this STP.
    """

    def __init__(self, name=None, version=None, enabled=None):
        self._name = (name, None)
        self._enabled = (enabled, None)
        self._version = (version, None)
        self._priority = (None, None)
        self._mst_cfgname = (None, None)    # only used with MST instance 0
        self._mst_rev = (None, None)        # only used with MST instance 0
        self._mst_instance = (None, None)
        self._vlans = ([], None)

    def __str__(self):
        description = 'Name: ' + str(self._name[0]) + ', '
        description += 'Status: '
        description += ('enabled' if self._enabled else 'disabled') + ', '
        description += 'Version: ' + str(self._version[0]) + ', '
        description += 'Priority: ' + str(self._priority[0]) + ', '
        description += 'VLANs: ' + str(self._vlans[0]) + ', '
        if (self._version is not None and
                isinstance(self._version[0], str) and
                self._version[0].lower() == 'mstp'):
            description += 'MST configuration name: '
            description += str(self._mst_cfgname[0]) + ', '
            description += 'MST configuration revision: '
            description += str(self._mst_rev[0]) + ', '
            description += 'MST instance id: '
            description += str(self._mst_instance[0]) + ', '
        return description

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def is_basic_stp_config(self):
        """Return True if this config is just a basic STP.

        This means a single STP instance with no MSTP region configuration.
        Extend this if more complex STP variants are added to possible
        input configurations (e.g. Extreme XOS STP configs).
        """
        _vlans = list(range(1, 4095))
        is_vlans_equal = len(set(_vlans).difference(self._vlans[0])) == 0
        is_cfg_none = self._mst_cfgname[0] is None
        is_mst_rev_0 = self._mst_rev[0] == 0
        is_mst_instance_0 = self._mst_instance[0] == 0
        if not is_cfg_none or not is_mst_rev_0 or not is_mst_instance_0 or \
                not is_vlans_equal:
            return False
        return True

    def is_enabled(self):
        return bool(self._enabled[0])

    def is_disabled(self):
        return not bool(self._enabled[0])

    def get_enabled_reason(self):
        return self._enabled[1]

    def set_enabled(self, state, reason):
        self._enabled = (bool(state), reason)
        return self._enabled[0]

    def enable(self, reason):
        self._enabled = (True, reason)

    def disable(self, reason):
        self._enabled = (False, reason)

    def get_name(self):
        return self._name[0]

    def get_name_reason(self):
        return self._name[1]

    def set_name(self, name, reason):
        self._name = (name, reason)
        return self._name[0]

    def get_version(self):
        return self._version[0]

    def get_version_reason(self):
        return self._version[1]

    def set_version(self, version, reason):
        self._version = (version, reason)
        return self._version[0]

    def get_priority(self):
        return self._priority[0]

    def get_priority_reason(self):
        return self._priority[1]

    def set_priority(self, priority, reason):
        try:
            prio = int(priority)
        except:
            return None
        if prio < 0 or prio > 65535:
            return self._priority[0]
        self._priority = (prio, reason)
        return self._priority[0]

    def get_mst_cfgname(self):
        return self._mst_cfgname[0]

    def get_mst_cfgname_reason(self):
        return self._mst_cfgname[1]

    def set_mst_cfgname(self, mst_cfgname, reason):
        self._mst_cfgname = (mst_cfgname, reason)
        return self._mst_cfgname[0]

    def get_mst_rev(self):
        return self._mst_rev[0]

    def get_mst_rev_reason(self):
        return self._mst_rev[1]

    def set_mst_rev(self, mst_rev, reason):
        try:
            rev = int(mst_rev)
        except:
            return self._mst_rev[0]
        self._mst_rev = (rev, reason)
        return self._mst_rev[0]

    def get_mst_instance(self):
        return self._mst_instance[0]

    def get_mst_instance_reason(self):
        return self._mst_instance[1]

    def set_mst_instance(self, mst_instance, reason):
        try:
            instance = int(mst_instance)
        except:
            return self._mst_instance[0]
        self._mst_instance = (instance, reason)
        return self._mst_instance[0]

    def get_vlans(self):
        return self._vlans[0]

    def get_vlans_reason(self):
        return self._vlans[1]

    def set_vlans_reason(self, reason):
        self._vlans = (self._vlans[0], reason)
        return self._vlans[1]

    def add_vlan(self, vlan_tag, reason):
        vlan_list = self._vlans[0][:]
        if vlan_tag not in vlan_list:
            vlan_list.append(vlan_tag)
        self._vlans = (vlan_list, reason)

    def add_vlans(self, vlan_tag_list, reason):
        for vlan_tag in vlan_tag_list:
            self.add_vlan(vlan_tag, reason)

    def del_vlan(self, vlan_tag, reason):
        vlan_list = self._vlans[0][:]
        if vlan_tag in vlan_list:
            vlan_list.remove(vlan_tag)
            self._vlans = (vlan_list, reason)

    def del_vlans(self, vlan_tag_list, reason):
        for vlan_tag in vlan_tag_list:
            self.del_vlan(vlan_tag, reason)

    def transfer_config(self, from_stp):

        def trans_reason(r):
            return 'transfer_conf' if r == 'config' else 'transfer_def'

        from_name = from_stp.get_name()
        if from_name is not None and from_name != self._name[0]:
            self._name = (from_name, trans_reason(from_stp.get_name_reason()))

        from_enabled = from_stp.is_enabled()
        if from_enabled != self.is_enabled():
            from_reason = from_stp.get_enabled_reason()
            self._enabled = (from_enabled, trans_reason(from_reason))

        from_version = from_stp.get_version()
        if from_version is not None and from_version != self._version[0]:
            from_reason = from_stp.get_version_reason()
            self._version = (from_version, trans_reason(from_reason))

        from_priority = from_stp.get_priority()
        if from_priority is not None and from_priority != self._priority[0]:
            from_reason = from_stp.get_priority_reason()
            self._priority = (from_priority, trans_reason(from_reason))

        from_mst_cfgname = from_stp.get_mst_cfgname()
        if (from_mst_cfgname is not None and
                from_mst_cfgname != self._mst_cfgname[0]):
            from_reason = from_stp.get_mst_cfgname_reason()
            self._mst_cfgname = (from_mst_cfgname, trans_reason(from_reason))

        from_mst_rev = from_stp.get_mst_rev()
        if from_mst_rev is not None and from_mst_rev != self._mst_rev[0]:
            from_reason = from_stp.get_mst_rev_reason()
            self._mst_rev = (from_mst_rev, trans_reason(from_reason))

        from_mst_instance = from_stp.get_mst_instance()
        if (from_mst_instance is not None and
                self._mst_instance[0] != from_mst_instance):
            from_reason = from_stp.get_mst_instance_reason()
            self._mst_instance = (from_mst_instance, trans_reason(from_reason))

        from_vlans = from_stp.get_vlans()
        if from_vlans and from_vlans != self._vlans:
            from_reason = from_stp.get_vlans_reason()
            self._vlans = (from_vlans, trans_reason(from_reason))

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
