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

"""Model of a Loopback Interface."""


class Loopback():

    """Model of a Loopback Interface.

    A Loopback interface is modeled like a VLAN without ports, tags, etc.
    This basically fits with XOS notion of "loopback" mode for a VLAN
    and the similarities of a Loopback interface and an SVI.
    """

    def __init__(self, number=None):
        self._number = number
        self._ipv4_addresses = []
        self._svi_shutdown = None

    def __str__(self):
        description = 'Number: ' + str(self._number) + ', '
        description += 'IPv4 addresses: ' + str(self._ipv4_addresses) + ', '
        description += 'Interface shutdown: ' + str(self._svi_shutdown)
        return description

    def get_number(self):
        return self._number

    def set_number(self, number):
        self._name = number

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

    def get_svi_shutdown(self):
        return self._svi_shutdown

    def set_svi_shutdown(self, shutdown):
        self._svi_shutdown = shutdown

    def transfer_config(self, from_loopback):
        self._number = from_loopback.get_number()
        self._ipv4_addresses = from_loopback.get_ipv4_addresses()
        self._svi_shutdown = from_loopback.get_svi_shutdown()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
