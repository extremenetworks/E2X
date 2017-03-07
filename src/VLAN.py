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

"""Model of a VLAN."""


def is_valid_tag(tag):
    try:
        itag = int(tag)
    except:
        return False
    return 0 < itag < 4096


class VLAN():

    """Model of a VLAN.

    This representation is modeled after the Enterasys OS VLAN configuration
    model with separated in- and egress configuration. It is actually more
    general, although most switch operating systems use a more restricted
    VLAN configuration.
    """

    def __init__(self, name=None, tag=None, switch=None):
        self._name = name
        self._name_is_default = False
        self._tag = tag
        self._egress_ports = []
        self._ingress_ports = []
        self._switch = switch
        self._ipv4_acl_in = []
        self._ipv4_addresses = []
        self._ipv4_helper_addresses = []
        self._svi_shutdown = None

    def __str__(self):
        description = 'Name: ' + str(self._name) + ', '
        description += 'Tag: ' + str(self._tag) + ', '
        description += 'Egress ports: ' + str(self._egress_ports) + ', '
        description += 'Ingress ports: ' + str(self._ingress_ports) + ', '
        description += 'IPv4 ACL in: ' + str(self._ipv4_acl_in) + ', '
        description += 'IPv4 addresses: ' + str(self._ipv4_addresses) + ', '
        description += ('IPv4 helper addresses: ' +
                        str(self._ipv4_helper_addresses) + ', ')
        description += 'SVI shutdown: ' + str(self._svi_shutdown)
        return description

    def get_name(self):
        return self._name

    def set_name(self, name, is_default=False):
        self._name = name
        self._name_is_default = is_default

    def has_default_name(self):
        return self._name_is_default

    def get_tag(self):
        return self._tag

    def set_tag(self, tag):
        if not is_valid_tag(tag):
            return False
        self._tag = int(tag)
        return True

    def _get_list(self, direction):
        if direction.startswith('in'):
            lst = self._ingress_ports
        elif direction.startswith('e'):
            lst = self._egress_ports
        else:
            lst = None
        return lst

    def _get_ports(self, direction, tagged):
        lst = self._get_list(direction)
        if lst is None:
            return None

        def pred(x, y):
            return y == 'all' or x == y

        ret = [pname[0] for pname in lst if pred(pname[1], tagged)]
        return ret

    def get_egress_ports(self, tagged='all'):
        return self._get_ports('egress', tagged)

    def get_ingress_ports(self, tagged='all'):
        return self._get_ports('ingress', tagged)

    def _add_port(self, name, direction, tagged):
        lst = self._get_list(direction)
        if lst is None:
            return False
        if tagged not in {'tagged', 'untagged'}:
            return False
        if (name, tagged) not in lst:
            lst.append((name, tagged))
        return True

    def add_egress_port(self, name, tagged='untagged'):
        return self._add_port(name, 'egress', tagged)

    def add_ingress_port(self, name, tagged='untagged'):
        return self._add_port(name, 'ingress', tagged)

    def _del_port(self, name, direction, tagged):
        lst = self._get_list(direction)
        if lst is None:
            return False

        if tagged not in {'all', 'tagged', 'untagged'}:
            return False
        if tagged in {'all', 'tagged'}:
            try:
                lst.remove((name, 'tagged'))
            except:
                pass
        if tagged in {'all', 'untagged'}:
            try:
                lst.remove((name, 'untagged'))
            except:
                pass
        return True

    def del_egress_port(self, name, tagged='all'):
        return self._del_port(name, 'egress', tagged)

    def del_ingress_port(self, name, tagged='all'):
        return self._del_port(name, 'ingress', tagged)

    def del_port(self, name, tagged='all'):
        re = self.del_egress_port(name, tagged='all')
        ri = self.del_ingress_port(name, tagged='all')
        return re and ri

    def del_all_ports(self):
        self._egress_ports = []
        self._ingress_ports = []

    def _add_mapped_ports(self, from_list, port_mapping, lag_mapping,
                          shadowed, tagging, direction):
        mapped_list, ret = [], []
        for name in from_list:
            if name in shadowed:
                err = 'INFO: Port "' + name + '" in VLAN "' + str(self._tag)
                err += '" (' + tagging + ', ' + direction + ') omitted because'
                err += ' of LAG with same target port name'
                ret.append(err)
            elif name in port_mapping:
                if (port_mapping[name], tagging) not in mapped_list:
                    mapped_list.append((port_mapping[name], tagging))
            elif name in lag_mapping:
                if (lag_mapping[name], tagging) not in mapped_list:
                    mapped_list.append((lag_mapping[name], tagging))
            else:
                if self._switch is None:
                    err = 'ERROR: VLAN with tag ' + str(self._tag) + ' and '
                    err += 'name "' + str(self._name)
                    err += '" not associated with a switch'
                    ret.append(err)
                else:
                    tmp_pl = self._switch.get_ports_by_name(name)
                    for p in tmp_pl:
                        if p.is_hardware():
                            err = 'WARN: Port "' + name + '" in VLAN "'
                            err += str(self._tag) + '" (' + tagging
                            err += ') not mapped to target switch'
                            ret.append(err)
        return mapped_list, ret

    def contains_port(self, portname):
        if portname in [pn for pn, _ in self._egress_ports]:
            return True
        if portname in [pn for pn, _ in self._ingress_ports]:
            return True
        return False

    def get_ipv4_acl_in(self):
        return self._ipv4_acl_in

    def set_ipv4_acl_in(self, identifier):
        """Replace existing ACL"""
        self._ipv4_acl_in.clear()
        self._ipv4_acl_in.append(identifier)

    def add_ipv4_acl_in(self, identifier):
        """Add identifier (number or name) of inbound ACL."""
        if identifier not in self._ipv4_acl_in:
            self._ipv4_acl_in.append(identifier)
        return self._ipv4_acl_in

    def del_ipv4_acl_in(self, identifier):
        """Delete identifier (number or name) of inbound ACL."""
        if identifier in self._ipv4_acl_in:
            self._ipv4_acl_in.remove(identifier)
        return self._ipv4_acl_in

    def get_ipv4_addresses(self):
        return self._ipv4_addresses

    def set_ipv4_addresses(self, address_list):
        self._ipv4_addresses = list(address_list)

    def get_ipv4_address(self, index):
        """Return the IPv4 address at a given list index."""
        if index < len(self._ipv4_addresses):
            return self._ipv4_addresses[index]

    def add_ipv4_address(self, ip, netmask):
        """Add an IPv4 address. First address in list is primary."""
        self._ipv4_addresses.append((ip, netmask))

    def change_ipv4_address(self, ip, netmask):
        if len(self._ipv4_addresses) > 1:
            return False
        elif len(self._ipv4_addresses) == 1:
            self._ipv4_addresses[0] = (ip, netmask)
        else:
            self._ipv4_addresses.append((ip, netmask))
        return True

    def get_ipv4_helper_addresses(self):
        return self._ipv4_helper_addresses

    def set_ipv4_helper_addresses(self, address_list):
        self._ipv4_helper_addresses = list(address_list)

    def get_ipv4_helper_address(self, index):
        """Return the IPv4 helper address at a given list index."""
        if index < len(self._ipv4_helper_addresses):
            return self._ipv4_helper_addresses[index]

    def add_ipv4_helper_address(self, ip):
        """Add an IPv4 helper address. First address in list is primary."""
        self._ipv4_helper_addresses.append(ip)

    def get_svi_shutdown(self):
        return self._svi_shutdown

    def set_svi_shutdown(self, shutdown):
        self._svi_shutdown = shutdown

    def transfer_config(self, from_vlan, port_mapping, lag_mapping,
                        unmapped_ports):
        ret = []
        self._name = from_vlan.get_name()
        self._name_is_default = from_vlan.has_default_name()
        self._tag = from_vlan.get_tag()
        self._ipv4_acl_in = from_vlan.get_ipv4_acl_in()
        self._ipv4_addresses = from_vlan.get_ipv4_addresses()
        self._ipv4_helper_addresses = from_vlan.get_ipv4_helper_addresses()
        self._svi_shutdown = from_vlan.get_svi_shutdown()
        # XOS reuses the names of physical ports for LAG names,
        # so remove source ports from the port_mapping, if the same
        # target port is mapped in lag_mapping as well
        lag_names = lag_mapping.values()
        shadowed = []
        for port_name in port_mapping.keys():
            if port_mapping[port_name] in lag_names:
                shadowed.append(port_name)
                err = ('NOTICE: VLAN configuration of port ' + port_name +
                       ' shadowed by LAG configuration')
                ret.append(err)
        ret.append('DEBUG: Ports shadowed by LAGs: ' + str(shadowed))
        egr_tag, err = self._add_mapped_ports(
            from_vlan.get_egress_ports('tagged'), port_mapping, lag_mapping,
            shadowed, 'tagged', 'egress'
        )
        ret.extend(err)
        egr_un, err = self._add_mapped_ports(
            from_vlan.get_egress_ports('untagged'), port_mapping, lag_mapping,
            shadowed, 'untagged', 'egress'
        )
        ret.extend(err)
        self._egress_ports = egr_tag + egr_un
        ret.append('DEBUG: Egress ports VLAN "' + str(self._tag) + '": ' +
                   str(self._egress_ports))
        ing_tag, err = self._add_mapped_ports(
            from_vlan.get_ingress_ports('tagged'), port_mapping, lag_mapping,
            shadowed, 'tagged', 'ingress'
        )
        ret.extend(err)
        ing_un, err = self._add_mapped_ports(
            from_vlan.get_ingress_ports('untagged'), port_mapping, lag_mapping,
            shadowed, 'untagged', 'ingress'
        )
        ret.extend(err)
        self._ingress_ports = ing_tag + ing_un
        ret.append('DEBUG: Ingress ports VLAN "' + str(self._tag) + '": ' +
                   str(self._ingress_ports))
        # re-add unmapped ports to default VLAN 1
        if self._tag == 1:
            for name in unmapped_ports:
                self.add_egress_port(name, 'untagged')
                self.add_ingress_port(name, 'untagged')
        return ret

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
