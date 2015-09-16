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

import xml.etree.ElementTree as ET


class HowTo:
    def __init__(self, howto_as_element_tree=None):
        self._description = None
        self._hint = None
        self._eos = None
        self._xos = None
        if howto_as_element_tree is not None:
            self._description = howto_as_element_tree.get('desc')
            self._hint = howto_as_element_tree.find('hint').text
            self._eos = howto_as_element_tree.find('eos').text
            self._xos = howto_as_element_tree.find('xos').text

    def _condense_line(self, line):
        return ' '.join(line.split())

    def _build_list(self, node_text):
        ret_list = []
        if node_text:
            ret_list = \
                [self._condense_line(line) for line in node_text.splitlines()]
        return ret_list

    def get_description(self):
        return self._description

    def get_hint(self):
        return self._hint

    def get_hint_as_list(self):
        return self._build_list(self._hint)

    def get_eos(self):
        return self._eos

    def get_eos_as_list(self):
        return self._build_list(self._eos)

    def get_xos(self):
        return self._xos

    def get_xos_as_list(self):
        return self._build_list(self._xos)


class HowToHandler:

    def __init__(self, howtos=None):
        if not howtos:
            howtos = '<?xml version="1.0"?>' \
                     '<howtos>' \
                     '  <howto desc="Upgrade firmware">' \
                     '    <eos>copy &lt;SOURCE&gt; system:image\n' \
                     '         set boot system &lt;IMAGENAME&gt;\n' \
                     '         reset' \
                     '    </eos>' \
                     '    <xos>download image &lt;SOURCEHOST&gt; ' \
                     '      &lt;[DIR/]SOURCEFILE&gt;' \
                     '      vr VR-Default &lt;PARTITION&gt;\n' \
                     '      install image &lt;SOURCEFILE&gt; ' \
                     '&lt;PARTITION&gt;\n' \
                     '      use image partition &lt;PARTITION&gt;\n' \
                     '      reboot' \
                     '    </xos>' \
                     '    <hint>You may need to install additional XMODs, ' \
                     ' e.g. for SSH.</hint>' \
                     '  </howto>' \
                     '  <howto desc="Reset switch to factory defaults">' \
                     '    <eos>clear ip address\n' \
                     '         set ip protocol dhcp\n' \
                     '         clear config all' \
                     '    </eos>' \
                     '    <xos>rm *\n' \
                     '         unconfigure switch all' \
                     '    </xos>' \
                     '    <hint>EOS commands do not delete saved ' \
                     'files.</hint>' \
                     '  </howto>' \
                     '  <howto desc="Configure Management IP Address">' \
                     '    <eos>' \
                     '      set host vlan &lt;VLANID&gt;\n'\
                     '      set ip address &lt;IP&gt; mask &lt;NETMASK&gt;'\
                     '        gateway &lt;GATEWAYIP&gt;' \
                     '    </eos>' \
                     '    <xos>' \
                     '      configure vlan &lt;VLANNAME&gt; ipaddress' \
                     '        &lt;IP&gt;/&lt;PREFIXLEN&gt;\n' \
                     '      configure iproute add default &lt;GATEWAYIP&gt; ' \
                     '        [vr &lt;VRNAME&gt;]' \
                     '    </xos>' \
                     '    <hint>' \
                     '      Use "vlan Mgmt" and "vr VR-Mgmt" for XOS ' \
                     '        management port.' \
                     '    </hint>' \
                     '  </howto>' \
                     '  <howto desc="Configure Router IP Address">' \
                     '    <eos>' \
                     '      router\n'\
                     '      enable\n'\
                     '      configure\n'\
                     '      interface &lt;INTERFACE&gt;\n'\
                     '      ip address &lt;IP&gt; &lt;NETMASK&gt;\n'\
                     '      exit\n'\
                     '      ip route 0.0.0.0 0.0.0.0 &lt;GATEWAYIP&gt;\n'\
                     '      exit'\
                     '    </eos>' \
                     '    <xos>' \
                     '      configure vlan &lt;VLANNAME&gt; ipaddress' \
                     '        &lt;IP&gt;/&lt;PREFIXLEN&gt;\n' \
                     '      enable ipforwarding vlan &lt;VLANNAME&gt;\n' \
                     '      configure iproute add default &lt;GATEWAYIP&gt; ' \
                     '        [vr &lt;VRNAME&gt;]' \
                     '    </xos>' \
                     '    <hint>' \
                     '      This configures an SVI for layer 3 forwarding.' \
                     '    </hint>' \
                     '  </howto>' \
                     '  <howto desc="Create a VLAN">' \
                     '    <eos>' \
                     '      set vlan create &lt;VLANID&gt;\n' \
                     '      set vlan name &lt;VLANID&gt; &lt;VLANNAME&gt;\n' \
                     '      set port vlan &lt;PORTSTRING&gt; &lt;VLANLIST&gt;'\
                     '        modify-egress\n' \
                     '      set vlan egress &lt;VLANID&gt; &lt;PORTSTRING&gt;'\
                     '        tagged' \
                     '    </eos>' \
                     '    <xos>' \
                     '      create vlan &lt;VLANNAME&gt; tag &lt;VLANID&gt;\n'\
                     '      configure vlan Default delete ports' \
                     '        &lt;PORTSTRING&gt;\n' \
                     '      configure vlan &lt;VLANNAME&gt; add ports' \
                     '        &lt;PORTSTRING&gt;\n' \
                     '      configure vlan &lt;VLANNAME&gt; add ports' \
                     '        &lt;PORTSTRING&gt; tagged' \
                     '    </xos>' \
                     '    <hint>' \
                     '      Untagged ports must be deleted from current VLAN' \
                     '        before they can be added to new VLAN.' \
                     '    </hint>' \
                     '  </howto>' \
                     '  <howto desc="Configure a Quiet Switch">' \
                     '    <eos>' \
                     '      set spantree disable\n' \
                     '      set gvrp disable\n' \
                     '      set lacp disable\n' \
                     '      set cdp state disable\n' \
                     '      set ciscodp status disable\n' \
                     '      set lldp port status disabled *.*.*\n' \
                     '      set flowcontrol disable\n' \
                     '      clear port advertise *.*.* pause\n' \
                     '      set mac agetime &lt;SECONDS&gt;' \
                     '    </eos>' \
                     '    <xos>' \
                     '      disable edp ports all\n' \
                     '      disable lldp ports all\n' \
                     '      disable stpd\n' \
                     '      disable flow-control rx-pause ports all\n' \
                     '      disable flow-control tx-pause ports all\n' \
                     '      configure fdb agingtime &lt;SECONDS&gt;' \
                     '    </xos>' \
                     '    <hint>' \
                     '      XOS does not support GVRP.' \
                     '      LACP is off by default and enabled per port on' \
                     '        XOS.' \
                     '    </hint>' \
                     '  </howto>' \
                     '</howtos>'

        self._howtos = ET.fromstring(howtos)

    def get_howto_descriptions(self):
        result = []
        for howto in self._howtos:
            result.append(howto.attrib['desc'])
        return result

    def get_howto_element(self, description):
        for howto in self._howtos:
            if howto.attrib['desc'] == description:
                return howto
        return None

    def get_howto(self, description):
        howto_element = self.get_howto_element(description)

        return HowTo(howto_element)

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
