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
            howtos = """\
<?xml version="1.0"?>
<howtos>
  <howto desc="Upgrade firmware">
    <eos>copy &lt;SOURCE&gt; system:image
         set boot system &lt;IMAGENAME&gt;
         reset\
    </eos>
    <xos>download image &lt;SOURCEHOST&gt; &lt;[DIR/]SOURCEFILE&gt; vr \
VR-Default &lt;PARTITION&gt;
      install image &lt;SOURCEFILE&gt; &lt;PARTITION&gt;
      use image partition &lt;PARTITION&gt;
      reboot\
    </xos>
    <hint>You may need to install additional XMODs, e.g. for SSH.</hint>
  </howto>
  <howto desc="Reset switch to factory defaults">
    <eos>clear ip address
         set ip protocol dhcp
         clear config all\
    </eos>
    <xos>rm *
         unconfigure switch all\
    </xos>
    <hint>EOS commands do not delete saved files.</hint>
  </howto>
  <howto desc="Configure Management IP Address">
    <eos>\
      set host vlan &lt;VLANID&gt;
      set ip address &lt;IP&gt; mask &lt;NETMASK&gt; gateway &lt;GATEWAYIP&gt;\
    </eos>
    <xos>\
      configure vlan &lt;VLANNAME&gt; ipaddress &lt;IP&gt;/&lt;PREFIXLEN&gt;
      configure iproute add default &lt;GATEWAYIP&gt; [vr &lt;VRNAME&gt;]\
    </xos>
    <hint>\
      Use "vlan Mgmt" and "vr VR-Mgmt" for XOS management port.\
    </hint>
  </howto>
  <howto desc="Configure Router IP Address">
    <eos>\
      router
      enable
      configure
      interface &lt;INTERFACE&gt;
      ip address &lt;IP&gt; &lt;NETMASK&gt;
      exit
      ip route 0.0.0.0 0.0.0.0 &lt;GATEWAYIP&gt;
      exit\
    </eos>
    <xos>\
      configure vlan &lt;VLANNAME&gt; ipaddress &lt;IP&gt;/&lt;PREFIXLEN&gt;
      enable ipforwarding vlan &lt;VLANNAME&gt;
      configure iproute add default &lt;GATEWAYIP&gt; [vr &lt;VRNAME&gt;]\
    </xos>
    <hint>\
      This configures an SVI for layer 3 forwarding.\
    </hint>
  </howto>
  <howto desc="Create a VLAN">
    <eos>\
      set vlan create &lt;VLANID&gt;
      set vlan name &lt;VLANID&gt; &lt;VLANNAME&gt;
      set port vlan &lt;PORTSTRING&gt; &lt;VLANLIST&gt; modify-egress
      set vlan egress &lt;VLANID&gt; &lt;PORTSTRING&gt; tagged\
    </eos>
    <xos>\
      create vlan &lt;VLANNAME&gt; tag &lt;VLANID&gt;
      configure vlan Default delete ports &lt;PORTSTRING&gt;
      configure vlan &lt;VLANNAME&gt; add ports &lt;PORTSTRING&gt;
      configure vlan &lt;VLANNAME&gt; add ports &lt;PORTSTRING&gt; tagged\
    </xos>
    <hint>\
      Untagged ports must be deleted from their current VLAN before they can
      be added to a new VLAN on XOS.\
    </hint>
  </howto>
  <howto desc="Configure a Quiet Switch">
    <eos>\
      set spantree disable
      set gvrp disable
      set lacp disable
      set cdp state disable
      set ciscodp status disable
      set lldp port status disabled *.*.*
      set flowcontrol disable
      clear port advertise *.*.* pause
      set mac agetime &lt;SECONDS&gt;\
    </eos>
    <xos>\
      disable edp ports all
      disable lldp ports all
      disable stpd
      disable flow-control rx-pause ports all
      disable flow-control tx-pause ports all
      configure fdb agingtime &lt;SECONDS&gt;\
    </xos>
    <hint>\
      XOS does not support GVRP.
      LACP is off by default and enabled per port on XOS.\
    </hint>
  </howto>
  <howto desc="Configure SNMPv3">
    <eos>\
      set snmp user &lt;USERNAME&gt; authentication sha &lt;AUTHPASS&gt; \
encryption aes privacy &lt;PRIVPASS&gt;
      set snmp group &lt;GROUPNAME&gt; user &lt;USERNAME&gt; security-model usm
      set snmp access &lt;GROUPNAME&gt; security-model usm privacy read All \
write All notify All\
    </eos>
    <xos>\
      configure snmpv3 add user &lt;USERNAME&gt; authentication sha \
&lt;AUTHPASS&gt; privacy aes &lt;PRIVPASS&gt;
      configure snmpv3 add group &lt;GROUPNAME&gt; user &lt;USERNAME&gt; \
sec-model usm
      configure snmpv3 add access &lt;GROUPNAME&gt; sec-model usm sec-level \
priv read-view defaultAdminView write-view defaultAdminView notify-view \
defaultAdminView\
    </xos>
    <hint>\
      The SSHv2 module has to be installed to use encryption.
      You should remove default SNMP credentials, disable unneeded SNMP
      versions and protect SNMP access via ACL or policy.\
    </hint>
  </howto>
  <howto desc="Configure SNMPv1 Trap Receiver">
    <eos>\
      set snmp targetparams TARGET_PARAMS user &lt;COMMUNITY_NAME&gt; \
      security-model v1 message-processing v1
      set snmp targetaddr TARGET_ADDR &lt;SERVER_IP_ADDRESS&gt; param \
      TARGET_PARAMS\
    </eos>
    <xos>\
      configure snmp add trapreceiver &lt;SERVER_IP_ADDRESS&gt; community \
      &lt;COMMUNITY_NAME&gt; vr VR-Default\
    </xos>
    <hint>\
      On EOS, the user needs access rights "notify" to send traps.\
    </hint>
  </howto>
  <howto desc="Set Passwords for Default Accounts">
    <eos>\
      set password admin
      set password rw
      set password ro\
    </eos>
    <xos>\
      configure account admin
      configure account user\
    </xos>
    <hint>\
      EOS admin and XOS admin are equivalent.
      EOS ro and XOS user are equivalent.
      There is no counterpart for EOS rw on XOS.\
    </hint>
  </howto>
  <howto desc="Clear Default Non-Admin Accounts">
    <eos>\
      clear system login rw
      clear system login ro\
    </eos>
    <xos>\
      delete account user\
    </xos>
    <hint>\
      EOS admin and XOS admin are equivalent.
      EOS ro and XOS user are equivalent.
      There is no counterpart for EOS rw on XOS.\
    </hint>
  </howto>
  <howto desc="Remove or Disable Default SNMP Credentials">
    <eos>\
      clear snmp community public
      clear snmp user public\
    </eos>
    <xos>\
      disable snmp community public
      disable snmp community private
      disable snmpv3 default-user
      disable snmpv3 default-group
      configure snmp delete community readonly all
      configure snmp delete community readwrite all
      configure snmpv3 delete user admin
      configure snmpv3 delete user initial
      configure snmpv3 delete user initialmd5
      configure snmpv3 delete user initialsha
      configure snmpv3 delete user initialmd5Priv
      configure snmpv3 delete user initialshaPriv\
    </xos>
    <hint>\
      All unused SNMP credentials should be disabled or deleted.\
    </hint>
  </howto>
  <howto desc="Create a Port Mirror">
    <eos>\
      set port mirroring create &lt;SOURCE_PORT&gt; &lt;DESTINATION_PORT&gt;\
    </eos>
    <xos>\
      create mirror &lt;MIRROR_NAME&gt;
      enable mirror &lt;MIRROR_NAME&gt; to port &lt;DESTINATION_PORT&gt;
      configure mirror &lt;MIRROR_NAME&gt; add port &lt;SOURCE_PORT&gt; \
ingress-and-egress\
    </xos>
    <hint>\
      XOS supports complex port mirror condiguration.\
    </hint>
  </howto>
</howtos>
"""

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
