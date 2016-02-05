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

"""Model layer 3 ACLs.

This module models layer 3 or router access control lists as known from
EOS (in router mode) or Cisco's IOS.

Classes:
ACL models a single access control list (ACL) consisting of access control
entries (ACEs).
ACE models a single access control entry (ACE)
Standard_ACE is a convenience class for modelling standard ACEs for standard
ACLs.
"""

import ipaddress


class ACL:

    """Model a layer 3 access control list (ACL).

    Access control lists are identified by either a number or a name.
    """

    _UNSUPPORTED_TYPE = ['mac', 'ipv6', 'ipv6mode']

    def __init__(self, number=None, name=None):
        self._number = self._convert_and_validate(number)
        self._name = name
        self._entries = []
        self._surplus_params = ''

    def __eq__(self, other):
        if self is other:
            return True
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False

    def _convert_and_validate(self, number):
        try:
            n = int(number)
        except:
            return None
        if n >= 0:
            return n
        return None

    def __str__(self):
        desc = '('
        desc += 'name="' + str(self._name) + '"'
        desc += ', number=' + str(self._number)
        desc += ', entries=['
        for ace in self._entries:
            desc += ' ' + str(ace)
        desc += ']'
        desc += ', surplus_params="' + str(self._surplus_params) + '"'
        desc += ')'
        return desc

    def is_standard(self):
        """Whether this is a standard ACL (filtering on source IP only)."""
        return all([ace.is_standard() for ace in self._entries])

    def get_number(self):
        """Get the identifying number of the ACL."""
        return self._number

    def set_number(self, number):
        """Set the identifying number of the ACL."""
        n = self._convert_and_validate(number)
        if n is not None:
            self._number = n
        return self._number

    def get_name(self):
        """Get the identifying name of the ACL."""
        return self._name

    def set_name(self, name):
        """Set the identifying name of the ACL."""
        self._name = str(name)
        return self._name

    def get_surplus_params(self):
        return self._surplus_params

    def set_surplus_params(self, to):
        self._surplus_params = to

    def get_entries(self):
        """Get the list of ACEs comprising the ACL."""
        return self._entries

    def add_entry(self, number=None, action=None, protocol=None, source=None,
                  source_op=None, source_port=None, dest=None, dest_op=None,
                  dest_port=None):
        """Add an ACE to the ACL using the individual ACE components."""
        new_ace = ACE(number, action, protocol, source, source_op, source_port,
                      dest, dest_op, dest_port)
        self._entries.append(new_ace)

    def add_ace(self, ace):
        """Add an existing ACE object to the ACL."""
        if isinstance(ace, ACE) and ace not in self._entries:
            self._entries.append(ace)

    @staticmethod
    def is_supported_type(type):
        return type.lower() not in ACL._UNSUPPORTED_TYPE


class ACE:

    """Model an access control entry (ACE)."""

    _ALLOWED_ACTIONS = ['permit', 'deny']
    _ALLOWED_PROTOCOLS = ['ip', 'udp', 'tcp', 'icmp', 'igmp']
    _ALLOWED_OPS = ['eq']

    def __init__(self, number=None, action=None, protocol=None, source=None,
                 source_mask=None, source_op=None, source_port=None, dest=None,
                 dest_mask=None, dest_op=None, dest_port=None):

        self._number = self._convert_and_validate_ace_number(number)
        self._action = action
        self._protocol = protocol
        self._source = source
        self._source_mask = source_mask
        self._source_op = source_op
        self._source_port = source_port
        self._dest = dest
        self._dest_mask = dest_mask
        self._dest_op = dest_op
        self._dest_port = dest_port

    def __eq__(self, other):
        if self is other:
            return True
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return NotImplemented

    def _convert_and_validate_ace_number(self, number):
        try:
            n = int(number)
        except:
            return None
        if n >= 0:
            return n
        return None

    @staticmethod
    def is_valid_ip_address(ip):
        try:
            ip = ipaddress.IPv4Address(ip)
        except:
            return False
        return True

    @staticmethod
    def _is_port_number(n):
        try:
            n = int(n)
        except:
            return False
        return n >= 0 and n <= 65535

    @staticmethod
    def _convertPositiveValue2int(value):
        try:
            nr = int(value)
        except:
            try:
                nr = int(value, 16)
            except:
                return -1
        return nr

    @staticmethod
    def validate_protocol_desc(desc):
        if desc in ACE._ALLOWED_PROTOCOLS:
            return desc
        number = ACE._convertPositiveValue2int(desc)
        if number != -1 and number in range(0, 256):
            return number
        return -1

    def __str__(self):
        desc = '{'
        desc += 'number=' + str(self._number)
        desc += ', action=' + str(self._action)
        desc += ', proto=' + str(self._protocol)
        desc += ', source=' + str(self._source) + '/' + str(self._source_mask)
        desc += ', s_op=' + str(self._source_op)
        desc += ', s_port=' + str(self._source_port)
        desc += ', dest=' + str(self._dest) + '/' + str(self._dest_mask)
        desc += ', d_op=' + str(self._dest_op)
        desc += ', d_port=' + str(self._dest_port)
        desc += '}'
        return desc

    def get_number(self):
        """Get the ACE's sequence number."""
        return self._number

    def set_number(self, number):
        """Set the ACE's sequence number."""
        n = self._convert_and_validate_ace_number(number)
        if n is not None:
            self._number = n
        return self._number

    def get_action(self):
        """Get the ACE's action."""
        return self._action

    def set_action(self, action):
        """Set the ACE's action."""
        if action in self._ALLOWED_ACTIONS:
            self._action = action
        return self._action

    def get_protocol(self):
        """Get the protocol this ACE is acting upon."""
        return self._protocol

    def set_protocol(self, protocol):
        """Set the protocol this ACE is acting upon."""
        prot = ACE.validate_protocol_desc(protocol)
        if prot != -1:
            self._protocol = str(prot)
        return self._protocol

    def _is_ip_address(self, ip):
        try:
            ip = ipaddress.IPv4Address(ip)
        except:
            return False
        return True

    def get_source(self):
        """Get the ACE's source address."""
        return self._source

    def set_source(self, source):
        """Set the ACE's source address."""
        if self._is_ip_address(source):
            self._source = ipaddress.IPv4Address(source)
        return self._source

    def get_source_mask(self):
        """Get the ACE's source wildcard."""
        return self._source_mask

    def _invert_ipv4_address(self, address):
        inv_address = bytes([b ^ 0xff for b in address.packed])
        return ipaddress.IPv4Address(inv_address)

    def get_source_mask_inverted(self):
        """Get the ACE's source standard mask."""
        if self._source_mask:
            return self._invert_ipv4_address(self._source_mask)
        return None

    def set_source_mask(self, source_mask):
        """Set the ACE's source wildcard."""
        if self._is_ip_address(source_mask):
            self._source_mask = ipaddress.IPv4Address(source_mask)
        return self._source_mask

    def get_source_op(self):
        """Get the ACE's source address operator."""
        return self._source_op

    def set_source_op(self, op):
        """Set the ACE's source address operator."""
        if op in self._ALLOWED_OPS:
            self._source_op = op
        return self._source_op

    def get_source_port(self):
        """Get the ACE's source port."""
        return self._source_port

    def set_source_port(self, port):
        """Set the ACE's source port."""
        if self._is_port_number(port):
            self._source_port = port
        return self._source_port

    def get_dest(self):
        """Get the ACE's destination address."""
        return self._dest

    def set_dest(self, dest):
        """Set the ACE's destination address."""
        if self._is_ip_address(dest):
            self._dest = ipaddress.IPv4Address(dest)
        return self._dest

    def get_dest_mask(self):
        """Get the ACE's dest wildcard."""
        return self._dest_mask

    def get_dest_mask_inverted(self):
        """Get the ACE's destination standard mask."""
        if self._dest_mask:
            return self._invert_ipv4_address(self._dest_mask)
        return None

    def set_dest_mask(self, dest_mask):
        """Set the ACE's destination address wildcard mask."""
        if self._is_ip_address(dest_mask):
            self._dest_mask = ipaddress.IPv4Address(dest_mask)
        return self._dest_mask

    def get_dest_op(self):
        """Get the ACE's destination address operator."""
        return self._dest_op

    def set_dest_op(self, op):
        """Set the ACE's destination address operator."""
        if op in self._ALLOWED_OPS:
            self._dest_op = op
        return self._dest_op

    def get_dest_port(self):
        """Get the ACE's destination port."""
        return self._dest_port

    def set_dest_port(self, port):
        """Set the ACE's destination port."""
        if self._is_port_number(port):
            self._dest_port = port
        return self._dest_port

    def is_standard(self):
        """Whether this ACE could be part of a standard ACL."""
        return (self._protocol == 'ip' and self._source_op is None and
                self._source_port is None and self._dest is None and
                self._dest_op is None and self._dest_port is None)


class Standard_ACE(ACE):

    """Convenience class for standard ACEs."""

    def __init__(self, number=None, action=None, source=None,
                 source_mask=None):
        super().__init__(number=number, action=action, protocol='ip',
                         source=source, source_mask=source_mask)

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
