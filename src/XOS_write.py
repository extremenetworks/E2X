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

""" XOS_write implements writing of XOS configuration commands.

Classes:
XosConfigWriter, a specialization (subclass) of ConfigWriter, implements
XOS specific methods for feature modules.
"""

import Switch
import Utils


class XosConfigWriter(Switch.ConfigWriter):

    """ConfigWriter specialization (subclass) for XOS.

    XosConfigWriter implements writing of XOS configuration commands
    according to the configuration of the (target) switch model. Writing
    is separated in feature models, called from the generic ConfigWriter
    class. There is one method per feature module.

    Methods:
    port() implements port specific configuration (feature module "port").
    vlan() implements VLAN specific configuration (feature module "VLAN").
    lag() implements LAG specific configuration (feature module "LAG").
    stp() implements spanning tree configuration (feature module "STP").
    acl() implements IPv4 access control lists (feature module "ACL").
    mgmt() implements switch management specifics (FM "Management").
    """

    def __init__(self, switch):
        super().__init__(switch)

    def _replace_special_characters(self, name, allow_space=False):
        trans_dict = (str.maketrans('"<>: &*', '_______') if not allow_space
                      else str.maketrans('"<>:&*', '______'))
        return name.translate(trans_dict)

    def _is_exos_keyword(self, word):
        """Replace reserved keywords by prepending a prefix."""

        # reserved keywords taken from XOS 16.1 User Guide
        reserved_keywords = {
            'aaa', 'access-list', 'account', 'accounts', 'all', 'bandwidth',
            'banner', 'bfd', 'bgp', 'bootp', 'bootprelay', 'brm', 'bvlan',
            'cancel', 'cfgmgr', 'cfm', 'checkpoint-data', 'clear-flow', 'cli',
            'cli-config-logging', 'clipaging', 'configuration', 'configure',
            'continuous', 'count', 'counters', 'cpu-monitoring', 'cvlan',
            'debug', 'debug-mode', 'devmgr', 'dhcp', 'dhcp-client',
            'dhcp-server', 'diagnostics', 'diffserv', 'dns-client',
            'dont-fragment', 'dos-protect', 'dot1ag', 'dot1p', 'dot1q', 'ds',
            'eaps', 'edp', 'egress', 'elrp', 'elrp-client', 'elsm', 'ems',
            'epm', 'esrp', 'fabric', 'failover', 'failsafe-account', 'fans',
            'fdb', 'fdbentry', 'firmware', 'flood-group', 'flooding',
            'flow-control', 'flow-redirect', 'forwarding', 'from', 'get',
            'hal', 'hclag', 'heartbeat', 'icmp', 'identity-management',
            'idletimeout', 'idmgr', 'igmp', 'image', 'ingress', 'inline-power',
            'internal-memory', 'interval', 'iob-debug-level', 'iparp',
            'ipconfig', 'ipforwarding', 'ipmc', 'ipmcforwarding', 'ipmroute',
            'ip-mtu', 'ip-option', 'iproute', 'ip-security', 'ipstats', 'ipv4',
            'IPv4', 'ipv6', 'IPv6', 'ipv6acl', 'irdp', 'isid', 'isis',
            'jumbo-frame', 'jumbo-frame-size', 'l2stats', 'l2vpn', 'lacp',
            'learning', 'learning-domain', 'license', 'license-info',
            'licenses', 'lldp', 'log', 'loopback-mode', 'mac', 'mac-binding',
            'mac-lockdown-timeout', 'management', 'mcast', 'memory',
            'memorycard', 'meter', 'mirroring', 'mld', 'mpls', 'mrinfo',
            'msdp', 'msgsrv', 'msm', 'msm-failover', 'mstp', 'mtrace',
            'multiple-response-timeout', 'mvr', 'neighbor-discovery',
            'netlogin', 'nettools', 'node', 'nodemgr', 'odometers', 'ospf',
            'ospfv3', 'pim', 'policy', 'ports', 'power', 'primary',
            'private-vlan', 'process', 'protocol', 'put', 'qosprofile',
            'qosscheduler', 'radius', 'radius-accounting', 'rip', 'ripng',
            'rmon', 'router-discovery', 'rtmgr', 'safe-default-script',
            'script', 'secondary', 'session', 'sflow', 'sharing', 'show',
            'slot', 'slot-poll-interval', 'smartredundancy', 'snmp', 'snmpv3',
            'sntp-client', 'source', 'ssl', 'stacking', 'stacking-support',
            'stack-topology', 'start-size', 'stp', 'stpd', 'subvlan-proxy-arp',
            'svlan', 'switch', 'switch-mode', 'sys-health-check', 'syslog',
            'sys-recovery-level', 'tacacs', 'tacacs-accounting',
            'tacacs-authorization', 'tech', 'telnet', 'telnetd', 'temperature',
            'tftpd', 'thttpd', 'time', 'timeout', 'timezone', 'tos', 'traffic',
            'trusted-ports', 'trusted-servers', 'ttl', 'tunnel', 'udp',
            'udp-echo-server', 'udp-profile', 'update', 'upm', 'var',
            'version', 'virtual-router', 'vlan', 'vman', 'vpls', 'vr', 'vrrp',
            'watchdog', 'web', 'xmlc', 'xmld', 'xml-mode', 'xml-notification',
        }
        return word in reserved_keywords

    def port(self):
        conf, err = [], []
        reason = 'written'
        # stacking mode uses different port names and requires prior
        # configuration, so emit a NOTICE message
        if self._switch.is_stack():
            err.append('NOTICE: Creating configuration for switch / stack in'
                       ' stacking mode')
            err.append('NOTICE: Stacking must be configured before applying'
                       ' this configuration')
            err.append('NOTICE: See the ExtremeXOS Configuration Guide on how'
                       ' to configure stacking')
        for p in self._switch.get_ports():
            # enable / disable port
            if (p.get_admin_state_reason() and
                    p.get_admin_state_reason().startswith('transfer')):
                admin_state = p.get_admin_state()
                if admin_state:
                    line = 'enable'
                else:
                    line = 'disable'
                line += ' ports {}'.format(p.get_name())
                conf.append(line)
                p.set_admin_state(admin_state, reason)
            # port speed, duplex, and auto-negotiation
            if (p.get_auto_neg_reason() and
                    p.get_auto_neg_reason().startswith('transfer')):
                auto_neg = p.get_auto_neg()
                speed = p.get_speed()
                duplex = p.get_duplex()
                line = 'configure ports ' + p.get_name()
                if not auto_neg and (speed is None or duplex is None):
                    msg = 'ERROR: Auto-negotiation of port "' + p.get_name()
                    msg += '" disabled, but speed or duplex not defined'
                    err.append(msg)
                elif auto_neg:
                    line += ' auto on'
                    p.set_auto_neg(auto_neg, reason)
                    conf.append(line)
                else:
                    line += ' auto off speed %s duplex %s' % (speed, duplex)
                    p.set_auto_neg(auto_neg, reason)
                    p.set_speed(speed, reason)
                    p.set_duplex(duplex, reason)
                    conf.append(line)
            # port description (short)
            if (p.get_short_description_reason() and
                    p.get_short_description_reason().startswith('transfer')):
                desc_orig = p.get_short_description()
                desc = self._replace_special_characters(desc_orig)
                if desc != desc_orig:
                    err.append('NOTICE: Changed "' + desc_orig + '" to "' +
                               desc + '"')
                line = 'configure ports ' + p.get_name()
                line += ' display-string ' + desc
                conf.append(line)
                p.set_short_description(desc, reason)
            # port description
            if (p.get_description_reason() and
                    p.get_description_reason().startswith('transfer')):
                desc_orig = p.get_description()
                desc = self._replace_special_characters(desc_orig)
                if desc != desc_orig:
                    err.append('NOTICE: Changed "' + desc_orig + '" to "' +
                               desc + '"')
                line = 'configure ports ' + p.get_name()
                line += ' description-string "' + desc + '"'
                conf.append(line)
                p.set_description(desc, reason)
            # jumbo frames
            if (p.get_jumbo_reason() and
                    p.get_jumbo_reason().startswith('transfer')):
                state = p.get_jumbo()
                if state:
                    line = 'enable '
                else:
                    line = 'disable '
                line += 'jumbo-frame ports ' + p.get_name()
                conf.append(line)
                p.set_jumbo(state, reason)
            # inbound ACL
            if (p.get_ipv4_acl_in_reason() and
                    p.get_ipv4_acl_in_reason().startswith('transfer')):
                acl_lst = p.get_ipv4_acl_in()
                acl_id = None
                if len(acl_lst) > 1:
                    err.append('ERROR: XOS allows only one ACL per port (' +
                               'port "' + p.get_name() + '")')
                elif len(acl_lst) == 1:
                    acl_id = acl_lst[0]
                if acl_id is not None:
                    line = ('configure access-list acl_' + str(acl_id) +
                            ' ports ' + p.get_name() + ' ingress')
                    conf.append(line)
                p.set_ipv4_acl_in(acl_lst, reason)

        return conf, err

    def _remove_non_master_lag_ports(self, vlan):
        pass

    def _verify_untagged_ports(self):
        err = []
        port_list = self._switch.get_ports()
        vlan_list = self._switch.get_all_vlans()
        port_egress, port_ingress = {}, {}
        for p in port_list:
            port_egress[p.get_name()], port_ingress[p.get_name()] = [], []
        for v in vlan_list:
            vlan_egress = v.get_egress_ports('untagged')
            for p in vlan_egress:
                port_egress[p].append((v.get_name(), v.get_tag()))
            vlan_ingress = v.get_ingress_ports('untagged')
            for p in vlan_ingress:
                port_ingress[p].append((v.get_name(), v.get_tag()))
        for p_name in port_egress:
            if len(port_egress[p_name]) > 1:
                msg = 'ERROR: Port "' + p_name + '" has multiple untagged'
                msg += ' egress VLANs:'
                for v in port_egress[p_name]:
                    msg += ' ' + str(v)
                err.append(msg)
        for p_name in port_ingress:
            if len(port_ingress[p_name]) > 1:
                msg = 'ERROR: Port "' + p_name + '" has multiple untagged'
                msg += ' ingress VLANs:'
                for v in port_ingress[p_name]:
                    msg += ' ' + str(v)
                err.append(msg)
        for p in port_list:
            if (port_egress[p.get_name()] != port_ingress[p.get_name()]):
                msg = 'ERROR: Untagged VLAN egress and ingress differs for '
                msg += 'port "' + p.get_name() + '"'
                err.append(msg)
        return err

    def _normalize_default_vlan(self, vlan):
        err = []
        if not vlan.get_name():
            vlan.set_name('Default', True)
        if vlan.get_name() != 'Default':
            msg = 'INFO: ' if vlan.has_default_name() else 'ERROR: '
            msg += 'Cannot rename VLAN 1 from "Default" to "'
            msg += vlan.get_name() + '"'
            err.append(msg)
            vlan.set_name('Default')
        # remove default PVID of 1 if VLAN 1 egress is missing
        # this can result from 'clear vlan egress 1 *.*.*'
        untagged_egress = vlan.get_egress_ports('untagged')
        tagged_egress = vlan.get_egress_ports('tagged')
        untagged_ingress = vlan.get_ingress_ports('untagged')
        for p_name in untagged_ingress:
            if p_name not in untagged_egress and p_name not in tagged_egress:
                err.append('NOTICE: Port "' + str(p_name) + '" has PVID of 1, '
                           'but VLAN 1 missing from egress, ignoring PVID')
                vlan.del_ingress_port(p_name, 'untagged')
        return err

    def _normalize_vlan(self, vlan):
        err = []
        v_name = vlan.get_name()
        if v_name:
            if v_name.lower() == 'mgmt':
                err.append('ERROR: Cannot use name "Mgmt" for regular VLAN')
                v_name = None
            elif ' ' in v_name:
                err.append('NOTICE: Replaced " " with "_" in VLAN name "' +
                           v_name + '"')
                v_name = v_name.replace(' ', '_')
            elif self._is_exos_keyword(v_name):
                err.append('NOTICE: Replaced VLAN name "' + v_name +
                           '" with "vl_' + v_name + '" because "' + v_name +
                           '" is a reserved keyword in XOS')
                v_name = 'vl_' + v_name
            vlan.set_name(v_name)
        v_tag = vlan.get_tag()
        if not v_name and not v_tag:
            err.append('ERROR: VLAN cannot have neither tag nor name, '
                       'removing all ports')
            vlan.del_all_ports()
        untagged_egress = vlan.get_egress_ports('untagged')
        tagged_egress = vlan.get_egress_ports('tagged')
        untagged_ingress = vlan.get_ingress_ports('untagged')
        tagged_ingress = vlan.get_ingress_ports('tagged')
        if not v_tag and tagged_egress:
            err.append('ERROR: VLAN "' + str(v_name) + '" without tag cannot'
                       ' have tagged egress ports')
            tagged_egress = []
        old_e_len, old_i_len = -1, -1
        while (old_e_len < len(untagged_egress) or
               old_i_len < len(untagged_ingress)):
            old_e_len, old_i_len = len(untagged_egress), len(untagged_ingress)
            for p_name in tagged_egress:
                if p_name not in tagged_ingress:
                    err.append('ERROR: Port "' + str(p_name) +
                               '" in tagged egress' +
                               ' list of VLAN "' + str(v_name) + '" but'
                               ' missing from tagged ingress: adding ingress')
                    vlan.add_ingress_port(p_name, 'tagged')
            # refresh vlan list copies
            untagged_egress = vlan.get_egress_ports('untagged')
            tagged_egress = vlan.get_egress_ports('tagged')
            untagged_ingress = vlan.get_ingress_ports('untagged')
            tagged_ingress = vlan.get_ingress_ports('tagged')
            for p_name in untagged_ingress:
                # PVID set to VID that is tagged on trunk
                if p_name in tagged_ingress:
                    err.append('WARN: Port "' + p_name + '" both untagged '
                               'and tagged in VLAN "' + str(v_name) +
                               '" (tag ' + str(v_tag) + ')')
                    err.append('WARN: Removing untagged ingress of "' +
                               str(v_name) + '" VLAN ' +
                               '(tag ' + str(v_tag) + ') from port "' +
                               p_name + '"')
                    vlan.del_ingress_port(p_name, 'untagged')
                # PVID not tagged on trunk, but neither untagged on port
                elif p_name not in untagged_egress:
                    err.append('ERROR: Port "' + p_name + '" in untagged '
                               'ingress list of VLAN "' + str(v_name) +
                               '" missing in untagged egress list: adding to'
                               ' egress')
                    vlan.add_egress_port(p_name, 'untagged')
            # refresh vlan list copies
            untagged_egress = vlan.get_egress_ports('untagged')
            tagged_egress = vlan.get_egress_ports('tagged')
            untagged_ingress = vlan.get_ingress_ports('untagged')
            tagged_ingress = vlan.get_ingress_ports('tagged')
        return err

    def _handle_default_vlan(self, vlan):
        conf, err = [], []
        v_name = vlan.get_name()
        u_list = vlan.get_egress_ports('untagged')
        t_list = vlan.get_egress_ports('tagged')
        all_ports = self._switch.get_ports()
        del_list = [p.get_name() for p in all_ports
                    if (p.get_name() not in u_list) and
                       (p.get_name() not in t_list)]
        if del_list:
            del_seq = Utils.create_compact_sequence(del_list)
            if not del_seq:
                del_seq = Utils.create_sequence(del_list)
        else:
            del_seq = ''
        if del_seq:
            conf.append('configure vlan ' + v_name + ' delete ports ' +
                        del_seq)
        if t_list:
            t_seq = Utils.create_compact_sequence(t_list)
            if not t_seq:
                t_seq = Utils.create_sequence(t_list)
        else:
            t_seq = ''
        if t_seq:
            conf.append('configure vlan ' + v_name + ' add ports ' + t_seq +
                        ' tagged')
        return conf, err

    def _handle_additional_vlan(self, vlan):
        conf, err = [], []
        v_name, v_tag = vlan.get_name(), vlan.get_tag()
        if not v_name:
            if v_tag:
                v_name = 'VLAN_' + '{:04d}'.format(v_tag)
                vlan.set_name(v_name, 'generated')
        cmd = 'create vlan ' + v_name
        if v_tag:
            cmd += ' tag ' + str(v_tag)
        conf.append(cmd)
        u_list = vlan.get_egress_ports('untagged')
        if u_list:
            u_seq = Utils.create_compact_sequence(u_list)
            if not u_seq:
                u_seq = Utils.create_sequence(u_list)
        else:
            u_seq = ''
        t_list = vlan.get_egress_ports('tagged')
        if t_list:
            t_seq = Utils.create_compact_sequence(t_list)
            if not t_seq:
                t_seq = Utils.create_sequence(t_list)
        else:
            t_seq = ''
        if u_seq:
            conf.append('configure vlan ' + v_name + ' add ports ' + u_seq +
                        ' untagged')
        if t_seq:
            conf.append('configure vlan ' + v_name + ' add ports ' + t_seq +
                        ' tagged')
        return conf, err

    def vlan(self):
        conf, err = [], []
        notified_about_global_bootprelay = False
        need_bootprelay_enable = False
        ipv4_routing = self._switch.get_ipv4_routing()
        self._switch.set_ipv4_routing(ipv4_routing, 'written')
        non_master_lag_ports = self._get_all_non_master_lag_ports()
        vlan_list = self._switch.get_all_vlans()
        for vlan in vlan_list:
            for member in non_master_lag_ports:
                vlan.del_port(member, 'all')
            if vlan.get_tag() == 1:
                e = self._normalize_default_vlan(vlan)
                err.extend(e)
                c, e = self._handle_default_vlan(vlan)
            else:
                e = self._normalize_vlan(vlan)
                err.extend(e)
                c, e = self._handle_additional_vlan(vlan)
            conf.extend(c)
            err.extend(e)
            ipv4_acl_in_lst = vlan.get_ipv4_acl_in()
            if len(ipv4_acl_in_lst) > 1:
                err.append('ERROR: Only one ACL per VLAN possible with XOS' +
                           ' (VLAN "' + vlan.get_name() + '", tag ' +
                           str(vlan.get_tag()) + ', ACLs: ' +
                           str(ipv4_acl_in_lst) + ')')
                ipv4_acl_in = None
            elif ipv4_acl_in_lst:
                ipv4_acl_in = ipv4_acl_in_lst[0]
            else:
                ipv4_acl_in = None
            if isinstance(ipv4_acl_in, int):
                ipv4_acl_in = 'acl_' + str(ipv4_acl_in)
            if ipv4_acl_in:
                conf.append('configure access-list ' + ipv4_acl_in + ' vlan ' +
                            vlan.get_name() + ' ingress')
            ipv4_addresses = vlan.get_ipv4_addresses()
            for (idx, ipv4_addr) in enumerate(ipv4_addresses):
                if idx == 0:
                    conf.append('configure vlan ' + vlan.get_name() +
                                ' ipaddress ' + ipv4_addr[0] + ' ' +
                                ipv4_addr[1])
                    if ipv4_routing:
                        conf.append('enable ipforwarding vlan ' +
                                    vlan.get_name())
                else:
                    conf.append('configure vlan ' + vlan.get_name() + ' add '
                                'secondary-ipaddress ' + ipv4_addr[0] + ' ' +
                                ipv4_addr[1])
            if vlan.get_svi_shutdown() is True:
                err.append('WARN: XOS cannot disable switched virtual '
                           'interfaces, ignoring shutdown state of interface '
                           'VLAN ' + str(vlan.get_tag()))
            for dhcp_relay in vlan.get_ipv4_helper_addresses():
                need_bootprelay_enable = True
                c = 'configure bootprelay add ' + dhcp_relay
                if c not in conf:
                    conf.append(c)
                if not notified_about_global_bootprelay:
                    err.append('NOTICE: XOS uses a global list of BOOTP / '
                               'DHCP relay servers instead of per VLAN relay '
                               'servers')
                    notified_about_global_bootprelay = True
        if need_bootprelay_enable:
            conf.append('enable bootprelay all')
            err.append('NOTICE: enabling BOOTP / DHCP relay on all VLANs')
        errors = self._verify_untagged_ports()
        err.extend(errors)
        return conf, err

    def _populate_lag_member_ports(self):
        err = []
        reason = 'written'
        physical_ports = self._switch.get_ports()
        lags = self._switch.get_lags()
        for l in lags:
            key = l.get_lacp_aadminkey()
            lacp = l.get_lacp_enabled()
            for p in physical_ports:
                p_key = p.get_lacp_aadminkey()
                p_key_is_default = (p.get_lacp_aadminkey_reason() ==
                                    'default' or
                                    p.get_lacp_aadminkey_reason() ==
                                    'transfer_def')
                p_lacp = p.get_lacp_enabled()
                if p_key == key and (p_lacp == lacp or not p_key_is_default):
                    l.add_member_port(p.get_name())
                    p.set_lacp_aadminkey(key, reason)
                    if p_lacp != lacp:
                        err.append('ERROR: LAG "' + l.get_name() +
                                   '" configured with LACP ' +
                                   ('enabled' if lacp else 'disabled') +
                                   ', but member port "' + p.get_name() +
                                   '" has LACP ' +
                                   ('enabled' if p_lacp else 'disabled'))
                    p.set_lacp_enabled(p_lacp, reason)
            if not l.get_members():
                err.append('WARN: LAG with key "' + str(key) +
                           '" configured, but no ports associated')
        return err

    def _get_all_non_master_lag_ports(self):
        non_master_lag_ports = []
        for l in self._switch.get_lags():
            non_master_lag_ports.extend(l.get_members()[1:])
        return non_master_lag_ports

    def lag(self):
        conf, err = [], []
        if not self._switch.get_single_port_lag():
            if self._switch.get_single_port_lag_reason() == 'transfer_conf':
                err.append('ERROR: XOS always allows single port LAGs')
            else:
                if self._switch.defaults_were_applied():
                    err.append('NOTICE: XOS always allows single port LAGs')
            self._switch.set_single_port_lag(False, 'warned')
        if self._switch.get_max_lag_reason() == 'transfer_conf':
            err.append('WARN: Maximum number of LAGs cannot be configured'
                       ' on XOS')
            self._switch.set_max_lag(None, 'not supported')
        if self._switch.get_lacp_support_reason() == 'transfer_conf':
            err.append('ERROR: LACP cannot be enabled/disabled globally'
                       ' on XOS')
            self._switch.set_lacp_support(True, 'not configurable')
        errors = self._populate_lag_member_ports()
        err.extend(errors)
        lag_list = self._switch.get_lags()
        for l in lag_list:
            master_port = l.get_master_port()
            member_ports = l.get_members()
            if master_port:
                port_seq = Utils.create_compact_sequence(member_ports)
                if not port_seq:
                    port_seq = Utils.create_sequence(member_ports)
                cmd = 'enable sharing ' + master_port + ' grouping '
                cmd += port_seq + ' algorithm address-based L3'
                if l.get_lacp_enabled():
                    cmd += ' lacp'
                conf.append(cmd)
                if (len(member_ports) == 1 and
                        (not self._switch.get_single_port_lag())):
                    err.append('ERROR: LAG consisting of one port ("' +
                               member_ports[0] + '") only, but'
                               ' single port LAG not enabled on source switch')
                # port description (short)
                short_desc_reas = l.get_short_description_reason()
                if (short_desc_reas and
                        short_desc_reas.startswith('transfer')):
                    desc_orig = l.get_short_description()
                    desc = self._replace_special_characters(desc_orig)
                    if desc != desc_orig:
                        err.append('NOTICE: Changed "' + desc_orig + '" to "' +
                                   desc + '"')
                    for p in member_ports:
                        line = 'configure ports ' + p
                        line += ' display-string ' + desc
                        conf.append(line)
                    l.set_short_description(desc, 'written')
                # port description
                if (l.get_description_reason() and
                        l.get_description_reason().startswith('transfer')):
                    desc_orig = l.get_description()
                    desc = self._replace_special_characters(desc_orig)
                    if desc != desc_orig:
                        err.append('NOTICE: Changed "' + desc_orig + '" to "' +
                                   desc + '"')
                    for p in member_ports:
                        line = 'configure ports ' + p
                        line += ' description-string "' + desc + '"'
                        conf.append(line)
                    l.set_description(desc, 'written')
        return conf, err

    def _get_stp_processes_for_port(self, port_name):
        stp_list = []
        port_vlans = []
        for vlan in self._switch.get_all_vlans():
            if port_name in vlan.get_egress_ports():
                port_vlans.append(vlan.get_tag())
        mst = False
        for stp in self._switch.get_stps():
            stp_name = stp.get_name()
            if stp.get_version() == 'mstp':
                mst = True
            for vlan in port_vlans:
                if vlan in stp.get_vlans():
                    if stp_name not in stp_list:
                        stp_list.append(stp_name)
        if mst and stp_list:
            cist = self._switch.get_stp_by_mst_instance(0)
            if cist is not None:
                cist_name = cist.get_name()
            else:
                cist_name = None
            if cist_name not in stp_list:
                stp_list.insert(0, cist_name)
            if stp_list.index(cist_name) != 0:
                stp_list.remove(cist_name)
                stp_list.insert(0, cist_name)
        return stp_list

    def stp(self):
        conf, err = [], []
        reason = 'written'
        stp_list = self._switch.get_stps()
        if not stp_list:
            if self._switch.defaults_were_applied():
                err.append('WARN: Cannot delete STP process "s0"'
                           ', but it is disabled by default')
            return conf, err
        # Special case EOS default STP and EOS 'set spantree version rstp',
        # with optional bridge priority change:
        # Create an XOS STP configuration that acts as an RSTP speaking
        # bridge.
        stp = None
        if len(stp_list) == 1:
            stp = stp_list[0]
            stp_name = stp.get_name()
        use_basic_stp_config = False
        if stp and stp_name == 's0' and stp.is_disabled():
            # do nothing, s0 is disabled by default and cannot be deleted
            use_basic_stp_config = True
        if stp and stp_name == 's0' and stp.is_enabled():
            stp_version = stp.get_version()
            is_basic_stp_cfg = stp.is_basic_stp_config()
            if (is_basic_stp_cfg and
                    (stp_version == 'mstp' or stp_version == 'rstp' or
                     stp_version == 'stp')):
                use_basic_stp_config = True
                err.append('INFO: Creating XOS equivalent of EOS default'
                           ' MSTP respectively RSTP configuration')
                c = 'configure stpd s0 delete vlan Default ports all'
                conf.append(c)
                conf.append('disable stpd s0 auto-bind vlan Default')
                conf.append('configure stpd s0 mode mstp cist')
                conf.append('create stpd s1')
                conf.append('configure stpd s1 mode mstp msti 1')
                for v in self._switch.get_all_vlans():
                    conf.append('enable stpd s1 auto-bind vlan ' +
                                str(v.get_name()))
                prio_reason = stp.get_priority_reason()
                if prio_reason and prio_reason.startswith('transfer'):
                    prio = stp.get_priority()
                    conf.append('configure stpd s0 priority ' + str(prio))
                    stp.set_priority(prio, reason)
                conf.append('enable stpd s0')
                conf.append('enable stpd s1')
                stp.set_version(stp_version, reason)
                stp.set_enabled(stp.is_enabled(), reason)
        # Try to translate a more complex STP config to XOS
        if not use_basic_stp_config:
            instance_with_vlans = False
            no_instance_has_default_vlan = True
            for stp in stp_list:
                stp_name = stp.get_name()
                if not stp_name:
                    if (stp.get_version() == 'mstp' and
                            stp.get_mst_instance() is not None):
                        stp_name = 's' + str(stp.get_mst_instance())
                        stp.set_name(stp_name, 'generated')
                        err.append('INFO: Generated name "' + stp_name +
                                   '" for MST instance ' +
                                   str(stp.get_mst_instance()))
                    else:
                        err.append('ERROR: XOS STP processes need a name')
                        continue
                if stp_name != 's0':
                    conf.append('create stpd ' + stp_name)
                    conf.append('configure stpd ' + stp_name +
                                ' default-encapsulation dot1d')
                    stp.set_name(stp_name, reason)
                version = None
                if (stp.get_version_reason() and
                        stp.get_version_reason().startswith('transfer')):
                    version = stp.get_version()
                    if not version:
                        err.append('ERROR: STP version must be specified'
                                   ', but missing from STP process "' +
                                   stp_name + '"')
                    elif version == 'stp':
                        if stp_name != 's0':
                            conf.append('configure stpd ' + stp_name +
                                        ' mode dot1d')
                    elif version == 'rstp':
                        conf.append('configure stpd ' + stp_name +
                                    ' mode dot1w')
                    elif version == 'mstp':
                        # this is done later with CIST / MSTI
                        pass
                    else:
                        err.append('ERROR: STP process "' + stp_name + '" has'
                                   ' unsupported version "' + version + '"')
                        continue
                    stp.set_version(version, reason)
                if version is not None and version == 'mstp':
                    if stp_name == 's0':
                        cfgname = stp.get_mst_cfgname()
                        cfgname_reason = stp.get_mst_cfgname_reason()
                        if (cfgname_reason is not None and
                                cfgname_reason.startswith('transfer')):
                            conf.append('configure mstp region ' + cfgname)
                            stp.set_mst_cfgname(cfgname, reason)
                        revision = stp.get_mst_rev()
                        revision_reason = stp.get_mst_rev_reason()
                        if (revision_reason is not None and
                                revision_reason.startswith('transfer')):
                            conf.append('configure mstp revision ' +
                                        str(revision))
                            stp.set_mst_rev(revision, reason)
                        conf.append('configure stpd s0 delete vlan Default'
                                    ' ports all')
                        conf.append('disable stpd s0 auto-bind vlan'
                                    ' Default')
                        conf.append('configure stpd s0 mode mstp cist')
                        for v_tag in stp.get_vlans():
                            if self._switch.get_vlan(tag=v_tag) is not None:
                                err.append('ERROR: Existing VLAN ' +
                                           str(v_tag) + ' mapped to MST '
                                           'instance 0 (CIST), but XOS cannot'
                                           ' map any VLANs to the CIST')
                        stp.set_vlans_reason(reason)
                    else:
                        sid = stp.get_mst_instance()
                        if sid != 0:
                            conf.append('configure stpd ' + stp_name +
                                        ' mode mstp msti ' + str(sid))
                            stp.set_mst_instance(sid, reason)
                        else:
                            err.append('ERROR: E2X expects "s0" as CIST')
                        for v in self._switch.get_all_vlans():
                            v_name = v.get_name()
                            v_tag = v.get_tag()
                            if v_tag in stp.get_vlans():
                                conf.append('enable stpd ' + stp_name +
                                            ' auto-bind vlan ' + v_name)
                                instance_with_vlans = True
                                if v_tag == 1:
                                    no_instance_has_default_vlan = False
                        omitted_vlans = []
                        for v_tag in stp.get_vlans():
                            if self._switch.get_vlan(tag=v_tag) is None:
                                omitted_vlans.append(v_tag)
                        if omitted_vlans:
                            err.append('WARN: XOS can only map configured '
                                       'VLANs to MST instances, the following '
                                       'VLANs have been omitted from MST '
                                       'instance ' + str(sid) + ': ' +
                                       str(omitted_vlans))
                        stp.set_vlans_reason(reason)
                if (stp.get_priority_reason() and
                        stp.get_priority_reason().startswith('transfer')):
                    prio = stp.get_priority()
                    if prio != 32768:
                        conf.append('configure stpd ' + stp_name +
                                    ' priority ' + str(prio))
                    stp.set_priority(prio, reason)
                if (stp.get_enabled_reason() and
                        stp.get_enabled_reason().startswith('transfer')):
                    conf.append(('enable' if stp.is_enabled() else 'disable') +
                                ' stpd ' + str(stp_name))
                    stp.set_enabled(stp.is_enabled(), reason)
            # check if this STP configuration makes sense
            if len(stp_list) == 1:
                err.append('ERROR: XOS needs at least one MST'
                           ' instance, CIST only is not possible')
            if not instance_with_vlans:
                err.append('ERROR: No VLANs associated with any MST '
                           'instance')
            if no_instance_has_default_vlan:
                err.append('WARN: VLAN "Default" with tag "1" is not part of'
                           ' any MST instance')
        # write per port STP configuration
        port_list = self._switch.get_logical_ports()
        info_auto_edge = False
        warn_auto_edge = False
        warn_edge_no_guard = False
        for port in port_list:
            p_name = port.get_name()
            is_enabled = port.get_stp_enabled()
            is_enabled_reason = port.get_stp_enabled_reason()
            is_auto = port.get_stp_auto_edge()
            is_edge = port.get_stp_edge()
            has_bpdu_guard = port.get_stp_bpdu_guard()
            recovery = port.get_stp_bpdu_guard_recovery_time()
            recovery_reason = port.get_stp_bpdu_guard_recovery_time_reason()
            stp_list = self._get_stp_processes_for_port(p_name)
            if stp_list:
                for stp_name in stp_list:
                    # STP disabled
                    if (not is_enabled and is_enabled_reason and
                            is_enabled_reason.startswith('transfer')):
                        conf.append('disable stpd ' + str(stp_name) +
                                    ' ports ' + str(p_name))
                        port.set_stp_enabled(is_enabled, reason)
                    # edge port
                    elif is_edge:
                        c = 'configure stpd ' + str(stp_name)
                        c += ' ports link-type edge ' + str(p_name)
                        if has_bpdu_guard:
                            c += ' edge-safeguard enable'
                            if (recovery is not None and
                                    recovery_reason is not None and
                                    recovery_reason.startswith('transfer')):
                                c += ' recovery-timeout ' + str(recovery)
                        else:
                            warn_edge_no_guard = True
                        conf.append(c)
                    elif (is_auto and
                          port.get_stp_auto_edge_reason() == 'transfer_conf'):
                        warn_auto_edge = True
                    elif is_auto:
                        info_auto_edge = True
                    port.set_stp_edge(is_edge, reason)
                    port.set_stp_auto_edge(is_auto, reason)
                    port.set_stp_bpdu_guard(has_bpdu_guard, reason)
                    port.set_stp_bpdu_guard_recovery_time(recovery, reason)
        if info_auto_edge:
            err.append('INFO: XOS does not support automatic RSTP/MSTP edge'
                       ' port detection')
        if warn_auto_edge:
            err.append('WARN: XOS does not support automatic edge'
                       ' port detection')
        if warn_edge_no_guard:
            err.append('WARN: XOS does not send BPDUs on RSTP/MSTP edge'
                       ' ports without edge-safeguard')
        # return STP configuration and error messages
        return conf, err

    def acl(self):
        conf, err = [], []
        acl_nr = 0
        for acl in self._switch.get_acls():
            acl_lst = []
            # generate a name for the ACL
            acl_nr += 1
            acl_name = ''
            if not acl.get_name() and not acl.get_number():
                acl_name = 'acl_nr' + str(acl_nr)
            elif acl.get_number():
                acl_name = 'acl_' + str(acl.get_number())
            else:
                acl_name = 'acl_' + str(acl.get_name())
            acl.set_name(acl_name)
            acl_lst.append(acl_name)
            ace_nr = 0
            ace_name = None
            for ace in acl.get_entries():
                # generate a name for the entry
                ace_nr += 10
                ace_name = ace.get_number()
                if not ace_name:
                    ace_name = str(ace_nr)
                else:
                    ace_name = str(ace_name)
                # generate the match statements
                match_lst = []
                match_proto = ace.get_protocol()
                if match_proto and match_proto != 'ip':
                    match_lst.append('protocol ' + match_proto)
                match_source = ace.get_source()
                match_source_mask = ace.get_source_mask_inverted()
                if match_source and match_source_mask:
                    if str(match_source_mask) == '0.0.0.0':
                        match_source_mask = '0'
                    match_lst.append('source-address ' + str(match_source) +
                                     '/' + str(match_source_mask))
                match_source_op = ace.get_source_op()
                match_source_port = ace.get_source_port()
                if match_source_op and match_source_port:
                    if match_source_op == 'eq':
                        match_lst.append('source-port ' +
                                         str(match_source_port))
                    else:
                        err.append('ERROR: ACL source operator "' +
                                   match_source_op + '" not supported')

                match_dest = ace.get_dest()
                match_dest_mask = ace.get_dest_mask_inverted()
                if match_dest and match_dest_mask:
                    if str(match_dest_mask) == '0.0.0.0':
                        match_dest_mask = '0'
                    match_lst.append('destination-address ' + str(match_dest) +
                                     '/' + str(match_dest_mask))
                match_dest_op = ace.get_dest_op()
                match_dest_port = ace.get_dest_port()
                if match_dest_op and match_dest_port:
                    if match_dest_op == 'eq':
                        match_lst.append('destination-port ' +
                                         str(match_dest_port))
                    else:
                        err.append('ERROR: ACL destination operator "' +
                                   match_dest_op + '" not supported')
                # generate the action statement
                action = ace.get_action()
                # create a string describing this ACE
                ace_str = 'entry ' + ace_name + ' {\n  if {\n'
                for match in match_lst:
                    ace_str += '    ' + match + ';\n'
                ace_str += '  } then {\n'
                ace_str += '    ' + str(action) + ';\n  }\n}\n'
                acl_lst.append(ace_str)
            # append explicit deny any [any] to match EOS ACLs
            ace_nr += 10
            if ace_name is not None:
                if (int(ace_name) >= ace_nr):
                    ace_nr = (int(ace_name) + 10) // 10 * 10
                ace_str = self._switch.get_cmd().get_comment()[0]
                ace_str += ' next entry added to match EOS ACL implicit deny\n'
                ace_str += ('entry ' + str(ace_nr) +
                            ' {\n  if {\n    source-address 0.0.0.0/0;\n'
                            '  } then {\n    deny;\n  }\n}\n')
                acl_lst.append(ace_str)
            conf.append(acl_lst)
        return conf, err

    def mgmt(self):
        conf, err = [], []
        # snmp sysName (from EOS prompt or system name)
        prompt = self._switch.get_prompt()
        sysname = self._switch.get_snmp_sys_name()
        if prompt and sysname:
            if prompt != sysname:
                err.append('WARN: The XOS prompt is derived from the snmp '
                           'system name, ignoring the configured prompt')
            self._switch.set_prompt(prompt, 'written')
            prompt = None
        if not sysname and prompt:
            sysname = prompt
            self._switch.set_prompt(prompt, 'written')
        if sysname:
            sname = self._replace_special_characters(sysname, allow_space=True)
            if sname != sysname:
                err.append('WARN: Changed sysName from "' + str(sysname) +
                           '" to "' + str(sname) + '"')
            conf.append('configure snmp sysName "' + str(sname) + '"')
            self._switch.set_snmp_sys_name(sname, 'written')
        # system contact
        syscontact = self._switch.get_snmp_sys_contact()
        if syscontact:
            scontact = self._replace_special_characters(syscontact,
                                                        allow_space=True)
            if scontact != syscontact:
                err.append('WARN: Changed syscontact from "' +
                           str(syscontact) + '" to "' + str(scontact) + '"')
            conf.append('configure snmp sysContact "' + str(scontact) + '"')
            self._switch.set_snmp_sys_contact(scontact, 'written')
        # system location
        syslocation = self._switch.get_snmp_sys_location()
        if syslocation:
            slocation = self._replace_special_characters(syslocation,
                                                         allow_space=True)
            if slocation != syslocation:
                err.append('WARN: Changed syslocation from "' +
                           str(syslocation) + '" to "' + str(slocation) + '"')
            conf.append('configure snmp sysLocation "' + str(slocation) + '"')
            self._switch.set_snmp_sys_location(slocation, 'written')
        # login banner
        banner_login = self._switch.get_banner_login()
        if banner_login:
            banner_lines = banner_login.split('\n')
            if '' in banner_lines:
                err.append('WARN: XOS banner cannot contain empty lines, '
                           'omitting empty lines')
                banner_lines = [l for l in banner_lines if l]
            conf_line = 'configure banner before-login'
            login_ack = self._switch.get_banner_login_ack()
            if login_ack:
                conf_line += ' acknowledge'
                banner_lines.append('Press RETURN to proceed to login')
            conf_line += ' save-to-configuration'
            conf.append(conf_line)
            conf.extend(banner_lines)
            # empty line signals end of banner
            conf.append('')
            self._switch.set_banner_login(banner_login, 'written')
            self._switch.set_banner_login_ack(login_ack, 'written')
        # MOTD banner
        banner_motd = self._switch.get_banner_motd()
        if banner_motd:
            banner_lines = banner_motd.split('\n')
            if '' in banner_lines:
                err.append('WARN: XOS banner cannot contain empty lines, '
                           'omitting empty lines')
                banner_lines = [l for l in banner_lines if l]
            conf_line = 'configure banner after-login'
            conf.append(conf_line)
            conf.extend(banner_lines)
            # empty line signals end of banner
            conf.append('')
            self._switch.set_banner_motd(banner_motd, 'written')
        # telnet
        telnet_in = self._switch.get_telnet_inbound()
        telnet_in_reason = self._switch.get_telnet_inbound_reason()
        telnet_out = self._switch.get_telnet_outbound()
        telnet_out_reason = self._switch.get_telnet_outbound_reason()
        if telnet_in is not None and not telnet_in:
            conf.append('disable telnet')
        elif telnet_in_reason and telnet_in_reason.startswith('transfer'):
            conf.append('enable telnet')
        if telnet_out is not None and not telnet_out:
            err.append('WARN: Outbound telnet cannot be disabled on XOS')
        elif telnet_out_reason and telnet_out_reason.startswith('transfer'):
            err.append('INFO: Outbound telnet is always enabled on XOS')
        self._switch.set_telnet_inbound(telnet_in, 'written')
        self._switch.set_telnet_outbound(telnet_out, 'written')
        # ssh
        ssh_in = self._switch.get_ssh_inbound()
        ssh_in_reason = self._switch.get_ssh_inbound_reason()
        ssh_out = self._switch.get_ssh_outbound()
        ssh_out_reason = self._switch.get_ssh_outbound_reason()
        ssh_xmod_notice_added = None
        ssh_xmod_notice = ('NOTICE: ssh.xmod needs to be installed for SSH' +
                           ' commands to work')
        if ssh_in is not None and ssh_in_reason.startswith('transfer'):
            if not ssh_in:
                conf.append('disable ssh2')
            else:
                conf.append('configure ssh2 key')
                conf.append('enable ssh2')
                err.append(ssh_xmod_notice)
                ssh_xmod_notice_added = True
        if ssh_out is not None and not ssh_out:
            err.append('WARN: Outbound ssh cannot be disabled on XOS')
        elif ssh_out_reason and ssh_out_reason.startswith('transfer'):
            if not ssh_xmod_notice_added:
                err.append('NOTICE: ssh.xmod needs to be installed for SSH')
            err.append(ssh_xmod_notice)
        self._switch.set_ssh_inbound(ssh_in, 'written')
        self._switch.set_ssh_outbound(ssh_out, 'written')
        # HTTP/HTTPS
        ssl = self._switch.get_ssl()
        http = self._switch.get_http()
        http_reason = self._switch.get_http_reason()
        https = self._switch.get_http_secure()
        if http_reason is not None and http_reason.startswith('transfer'):
            if http:
                conf.append('enable web http')
            else:
                conf.append('disable web http')
        if https and ssl:
            conf.append('enable web https')
            err.append('NOTICE: ssh.xmod needs to be installed for HTTPS')
            err.append('NOTICE: You need to manually create a certificate for'
                       ' HTTPS to work (configure ssl certificate)')
        if not https and ssl:
            err.append('WARN: SSL cannot be enabled independently from ' +
                       'HTTPS on XOS')
        self._switch.set_ssl(ssl, 'written')
        self._switch.set_http(http, 'written')
        self._switch.set_http_secure(https, 'written')
        # management ip, vlan, protocol
        mgmt_ip = self._switch.get_mgmt_ip()
        mgmt_mask = self._switch.get_mgmt_mask()
        mgmt_gw = self._switch.get_mgmt_gw()
        mgmt_vlan = self._switch.get_mgmt_vlan()
        mgmt_proto = self._switch.get_mgmt_protocol()
        oob = self._switch.uses_oob_mgmt()
        # determine the management VLAN
        if oob:
            if mgmt_vlan != 'Mgmt' and mgmt_vlan != 1:
                err.append('NOTICE: using OOB management port, overwriting'
                           'configured VLAN "' + str(mgmt_vlan) + '"')
            mgmt_vlan = 'Mgmt'
        if mgmt_ip and not mgmt_vlan:
            err.append('ERROR: cannot configure management IP without VLAN')
        mvn = None
        if mgmt_vlan:
            try:
                mvt = int(mgmt_vlan)
                mvn = self._switch.get_vlan(tag=mvt).get_name()
            except:
                try:
                    mvn = self._switch.get_vlan(name=mgmt_vlan).get_name()
                except:
                    pass
            # Mgmt VLAN is lost during VLAN transfer, but cannot be deleted
            if mvn is None and not mgmt_vlan == 'Mgmt':
                err.append('ERROR: management VLAN "' + str(mgmt_vlan) +
                           '" does not exist')
            elif mgmt_vlan == 'Mgmt':
                mvn = mgmt_vlan
        # check if the mgmt VLAN has other IPs configured
        vlan_clash = False
        mgmt_vlan_object = self._switch.get_vlan(name=mvn)
        if mgmt_vlan_object and mgmt_vlan_object.get_ipv4_addresses():
            vlan_clash = True
        # configure management VLAN IP
        if vlan_clash:
            err.append('ERROR: Both SVI and host management IP configured'
                       ' for the same VLAN (' + mvn + ')')
        elif mvn:
            if mgmt_ip and mgmt_mask:
                conf.append('configure vlan ' + mvn + ' ipaddress ' +
                            str(mgmt_ip) + ' ' + str(mgmt_mask))
                self._switch.set_mgmt_ip(mgmt_ip, 'written')
                self._switch.set_mgmt_mask(mgmt_mask, 'written')
                self._switch.set_mgmt_vlan(mvn, 'written')
                if mgmt_proto == 'bootp' or mgmt_proto == 'dhcp':
                    r = self._switch.get_mgmt_protocol_reason()
                    e = 'WARN: ' if r == 'transfer_def' else 'ERROR: '
                    e += ('Management IPv4 address configured statically,'
                          ' but dynamic IPv4 address assignment active,'
                          ' using static IPv4 address only')
                    err.append(e)
            elif mgmt_proto == 'bootp':
                conf.append('enable bootp vlan ' + mvn)
                self._switch.set_mgmt_protocol(mgmt_proto, 'written')
            elif mgmt_proto == 'dhcp':
                conf.append('enable dhcp vlan ' + mvn)
                self._switch.set_mgmt_protocol(mgmt_proto, 'written')
        # configure management default gateway
        if mgmt_gw and not vlan_clash:
            c = 'configure iproute add default ' + str(mgmt_gw)
            if oob:
                c += ' vr VR-Mgmt'
            conf.append(c)
            self._switch.set_mgmt_gw(mgmt_gw, 'written')
        # idle timeout
        timeout = self._switch.get_idle_timer()
        to_reason = self._switch.get_idle_timer_reason()
        if to_reason is not None and to_reason.startswith('transfer'):
            if timeout == 0:
                conf.append('disable idletimeout')
            elif timeout:
                conf.append('configure idletimeout ' + str(timeout))
            self._switch.set_idle_timer(timeout, 'written')
        # syslog servers
        for idx, sls in self._switch.get_all_syslog_servers().items():
            severity_level_mapping = {
                '1': 'critical',
                '2': 'critical',
                '3': 'critical',
                '4': 'error',
                '5': 'warning',
                '6': 'notice',
                '7': 'info',
                '8': 'debug-data',
            }
            xos_severities = {
                "critical", "debug-data", "debug-summary", "debug-verbose",
                "error", "info", "notice", "warning",
            }
            description = sls.get_description()
            facility = sls.get_facility()
            ip = sls.get_ip()
            port = sls.get_port()
            severity = sls.get_severity()
            state = sls.get_state()
            # XOS needs at least an IP and a facility
            if ip is None:
                err.append('ERROR: A SysLog target on XOS needs an IP address'
                           ' (set logging server ' + str(idx) + ' ...)')
                continue
            if facility is None:
                facility = sls.get_default_facility()
            if facility is None:
                err.append('ERROR: A SysLog target on XOS needs a facility'
                           ' (set logging server ' + str(idx) + ' ...)')
                continue
            if facility not in {"local0", "local1", "local2", "local3",
                                "local4", "local5", "local6", "local7"}:
                err.append('ERROR: SysLog facility "' + facility + '" is not'
                           'supported on XOS (set logging server ' +
                           str(idx) + ' ...)')
                continue
            # try to fill in some (optional) defaults
            if port is None:
                port = sls.get_default_port()
            if severity is None:
                severity = sls.get_default_severity()
            # translate EOS severity number to XOS name
            if severity is not None and severity not in xos_severities:
                severity = severity_level_mapping[severity]
            c = 'configure syslog add ' + str(ip)
            if port:
                c += ':' + str(port)
            if oob:
                c += ' vr VR-Mgmt'
            c += ' ' + facility
            conf.append(c)
            if severity in xos_severities:
                c = 'configure log target syslog ' + str(ip)
                if port:
                    c += ':' + str(port)
                c += ' '
                if oob:
                    c += 'vr VR-Mgmt '
                c += facility + ' severity ' + severity
                conf.append(c)
            elif severity is not None:
                err.append('WARN: Ignoring unknown SysLog severity "' +
                           str(severity) + '" (set logging server ' +
                           str(idx) + ' ...)')
            if state == 'enable':
                c = 'enable log target syslog ' + str(ip)
                if port:
                    c += ':' + str(port)
                if oob:
                    c += ' vr VR-Mgmt'
                c += ' ' + facility
                conf.append(c)
            # tell about ignoring the description
            if description:
                err.append('NOTICE: XOS cannot add descriptions to SysLog'
                           ' servers (set logging server ' + str(idx) + ')')
            sls.set_is_written(True)
        # SNTP Server
        sntp_server_list = self._switch.get_all_sntp_servers()
        for sntp in sntp_server_list:
            if sntp.get_precedence() is None:
                if sntp.get_default_precedence() is not None:
                    sntp.set_precedence(sntp.get_default_precedence())
                else:
                    sntp.set_precedence(2**32)

        def _sntp_srv_prec(s):
            return s.get_precedence()

        sntp_server_list.sort(key=_sntp_srv_prec)
        if len(sntp_server_list) > 0:
            c = ('configure sntp-client primary ' +
                 str(sntp_server_list[0].get_ip()))
            if oob:
                c += ' vr VR-Mgmt'
            conf.append(c)
            sntp_server_list[0].set_is_written(True)
        if len(sntp_server_list) > 1:
            c = ('configure sntp-client secondary ' +
                 str(sntp_server_list[1].get_ip()))
            if oob:
                c += ' vr VR-Mgmt'
            conf.append(c)
            sntp_server_list[1].set_is_written(True)
        if len(sntp_server_list) > 2:
            err.append('ERROR: XOS supports at most two SNTP servers')
        # SNTP Client
        sntp_client = self._switch.get_sntp_client()
        if sntp_client == 'unicast':
            if not sntp_server_list:
                err.append('ERROR: At least one SNTP server needed for unicast'
                           ' SNTP client')
            else:
                conf.append('enable sntp-client')
                self._switch.set_sntp_client(sntp_client, 'written')
        elif sntp_client == 'broadcast':
            if sntp_server_list:
                err.append('WARN: XOS uses unicast SNTP if an SNTP server is'
                           ' configured')
            conf.append('enable sntp-client')
            self._switch.set_sntp_client(sntp_client, 'written')
        elif sntp_client == 'disable':
            if not self._switch.get_sntp_client_reason() == 'default':
                conf.append('disable sntp-client')
                self._switch.set_sntp_client(sntp_client, 'written')
        # timezone
        write_timezone = False
        c = 'configure timezone '
        tz_name = self._switch.get_tz_name()
        if tz_name:
            c += 'name ' + tz_name + ' '
            self._switch.set_tz_name(tz_name, 'written')
            write_timezone = True
        tz_offset = self._switch.get_tz_off_min()
        if tz_offset is not None:
            c += str(tz_offset) + ' '
            self._switch.set_tz_off_min(tz_offset, 'written')
            write_timezone = True
        tz_dst_state = self._switch.get_tz_dst_state()
        if not tz_dst_state:
            c += 'noautodst'
            if tz_dst_state is not None:
                self._switch.set_tz_dst_state(tz_dst_state, 'written')
        else:
            c += 'autodst '
            tz_dst_name = self._switch.get_tz_dst_name()
            tz_dst_start = self._switch.get_tz_dst_start()
            tz_dst_end = self._switch.get_tz_dst_end()
            tz_dst_offset = self._switch.get_tz_dst_off_min()
            if (write_timezone and
                    (self._switch.get_tz_dst_start_reason() == 'default' or
                     self._switch.get_tz_dst_end_reason() == 'default' or
                     self._switch.get_tz_dst_off_min_reason() == 'default')):
                err.append('NOTICE: Using XOS default value(s) for daylight'
                           'saving time (DST)')
            if tz_dst_name:
                c += 'name ' + tz_dst_name + ' '
                self._switch.set_tz_dst_name(tz_dst_name, 'written')
            c += str(tz_dst_offset) + ' '
            c += ('begins every ' + tz_dst_start[0] + ' ' + tz_dst_start[1] +
                  ' ' + tz_dst_start[2] + ' at ' + str(tz_dst_start[3]) + ' ' +
                  str(tz_dst_start[4]) + ' ')
            c += ('ends every ' + tz_dst_end[0] + ' ' + tz_dst_end[1] + ' ' +
                  tz_dst_end[2] + ' at ' + str(tz_dst_end[3]) + ' ' +
                  str(tz_dst_end[4]))
            self._switch.set_tz_dst_state(tz_dst_state, 'written')
            self._switch.set_tz_dst_start(tz_dst_start[0], tz_dst_start[1],
                                          tz_dst_start[2], tz_dst_start[3],
                                          tz_dst_start[4], 'written')
            self._switch.set_tz_dst_end(tz_dst_end[0], tz_dst_end[1],
                                        tz_dst_end[2], tz_dst_end[3],
                                        tz_dst_end[4], 'written')
            self._switch.set_tz_dst_off_min(tz_dst_offset, 'written')
        if write_timezone:
            conf.append(c)
        # RADIUS for management access
        rad_idx_lst = sorted(self._switch.get_all_radius_servers())
        mgmt_acc_rad_srv_cnt = 0
        rad_client_ip = None
        reported_no_rad_client_ip_error = False
        rad_client_intf_type = self._switch.get_radius_interface_type()
        rad_client_intf_number = self._switch.get_radius_interface_number()
        if (rad_client_intf_type is not None and
                rad_client_intf_number is not None):
            if rad_client_intf_type == 'vlan':
                v = self._switch.get_vlan(tag=rad_client_intf_number)
                if v is not None:
                    addr_lst = v.get_ipv4_addresses()
                    if addr_lst:
                        rad_client_ip = addr_lst[0][0]
            elif rad_client_intf_type == 'loopback':
                l = self._switch.get_loopback(rad_client_intf_number)
                if l is not None:
                    addr_lst = l.get_ipv4_addresses()
                    if addr_lst:
                        rad_client_ip = addr_lst[0][0]
            else:
                err.append('WARN: Unknown interface type "' +
                           rad_client_intf_type + '" used for RADIUS'
                           ' client interface')
            if rad_client_ip is not None:
                rad_client_intf = self._switch.get_radius_interface()
                self._switch.set_radius_interface(rad_client_intf, 'written')
        elif mgmt_ip:
            rad_client_ip = mgmt_ip
        else:
            lo_zero = self._switch.get_loopback(0)
            lo_zero_ips = None
            if lo_zero:
                lo_zero_ips = lo_zero.get_ipv4_addresses()
            if lo_zero_ips:
                rad_client_ip = lo_zero_ips[0][0]
        for idx in rad_idx_lst:
            r = self._switch.get_radius_server(idx)
            r_realm = r.get_realm()
            if r_realm != 'management-access':
                continue
            if mgmt_acc_rad_srv_cnt > 1:
                err.append('ERROR: XOS supports at most two RADIUS servers'
                           ' for management access')
                break
            r_ip = r.get_ip()
            r_port = r.get_port()
            r_secret = r.get_secret()
            c = 'configure radius mgmt-access '
            c += 'primary' if mgmt_acc_rad_srv_cnt == 0 else 'secondary'
            c += ' server ' + str(r_ip) + ' ' + str(r_port) + ' client-ip '
            c += str(rad_client_ip)
            if r_secret:
                c += ' shared-secret ' + str(r_secret)
            if oob:
                c += ' vr VR-Mgmt'
            else:
                c += ' vr VR-Default'
            mgmt_acc_rad_srv_cnt += 1
            if rad_client_ip:
                conf.append(c)
                r.set_is_written(True)
            elif not reported_no_rad_client_ip_error:
                err.append('ERROR: XOS needs RADIUS client IP, but cannot'
                           ' determine EOS RADIUS client IP')
                err.append('NOTICE: EOS uses either the host IP or the'
                           ' Loopback 0 IP as RADIUS client IP by default')
                reported_no_rad_client_ip_error = True
        # en/disable RADIUS for management access
        rad_mgmt = self._switch.get_radius_mgmt_acc_enabled()
        rad_mgmt_reason = self._switch.get_radius_mgmt_acc_enabled_reason()
        if (rad_mgmt is not None and not rad_mgmt and rad_mgmt_reason and
                rad_mgmt_reason.startswith('transfer')):
            conf.append('disable radius mgmt-access')
        if (rad_mgmt is not None and rad_mgmt and rad_mgmt_reason and
                rad_mgmt_reason.startswith('transfer')):
            conf.append('enable radius mgmt-access')
        self._switch.set_radius_mgmt_acc_enabled(rad_mgmt, 'written')
        # TACACS+ for management access
        tac_idx_lst = sorted(self._switch.get_all_tacacs_servers())
        tac_srv_cnt = 0
        tac_client_ip = None
        reported_no_tac_client_ip_error = False
        tac_client_intf_type = self._switch.get_tacacs_interface_type()
        tac_client_intf_number = self._switch.get_tacacs_interface_number()
        if (tac_client_intf_type is not None and
                tac_client_intf_number is not None):
            if tac_client_intf_type == 'vlan':
                v = self._switch.get_vlan(tag=tac_client_intf_number)
                if v is not None:
                    addr_lst = v.get_ipv4_addresses()
                    if addr_lst:
                        tac_client_ip = addr_lst[0][0]
            elif tac_client_intf_type == 'loopback':
                l = self._switch.get_loopback(tac_client_intf_number)
                if l is not None:
                    addr_lst = l.get_ipv4_addresses()
                    if addr_lst:
                        tac_client_ip = addr_lst[0][0]
            else:
                err.append('WARN: Unknown interface type "' +
                           tac_client_intf_type + '" used for TACACS+'
                           ' client interface')
            if tac_client_ip is not None:
                tac_client_intf = self._switch.get_tacacs_interface()
                self._switch.set_tacacs_interface(tac_client_intf, 'written')
        elif mgmt_ip:
            tac_client_ip = mgmt_ip
        else:
            lo_zero = self._switch.get_loopback(0)
            lo_zero_ips = None
            if lo_zero:
                lo_zero_ips = lo_zero.get_ipv4_addresses()
            if lo_zero_ips:
                tac_client_ip = lo_zero_ips[0][0]
        for idx in tac_idx_lst:
            t = self._switch.get_tacacs_server(idx)
            if tac_srv_cnt > 1:
                err.append('ERROR: XOS supports at most two TACACS+ servers')
                break
            t_ip = t.get_ip()
            t_port = t.get_port()
            c1 = 'configure tacacs '
            c1 += 'primary' if tac_srv_cnt == 0 else 'secondary'
            c1 += ' server ' + str(t_ip) + ' ' + str(t_port) + ' client-ip '
            c1 += str(tac_client_ip)
            if oob:
                c1 += ' vr VR-Mgmt'
            else:
                c1 += ' vr VR-Default'
            t_secret = t.get_secret()
            c2 = None
            if t_secret:
                c2 = 'configure tacacs '
                c2 += 'primary' if tac_srv_cnt == 0 else 'secondary'
                c2 += ' shared-secret ' + str(t_secret)
            tac_srv_cnt += 1
            if tac_client_ip:
                conf.append(c1)
                if c2 is not None:
                    conf.append(c2)
                t.set_is_written(True)
            elif not reported_no_tac_client_ip_error:
                err.append('ERROR: XOS needs TACACS+ client IP, but cannot'
                           ' determine EOS TACACS+ client IP')
                err.append('NOTICE: On EOS, TACACS+ uses either the host IP'
                           ' or the Loopback 0 IP as TACACS+ client IP by'
                           ' default')
                reported_no_tac_client_ip_error = True
        # en/disable TACACS+ for management access
        tac_mgmt = self._switch.get_tacacs_enabled()
        tac_mgmt_reason = self._switch.get_tacacs_enabled_reason()
        if (tac_mgmt is not None and not tac_mgmt and tac_mgmt_reason and
                tac_mgmt_reason.startswith('transfer')):
            conf.append('disable tacacs')
        if (tac_mgmt is not None and tac_mgmt and tac_mgmt_reason and
                tac_mgmt_reason.startswith('transfer')):
            conf.append('enable tacacs')
        self._switch.set_tacacs_enabled(tac_mgmt, 'written')
        # SNMPv1 or SNMPv2c trap receiver
        snmp_param_names = sorted(self._switch._snmp_target_params.keys())
        snmp_target_names = sorted(self._switch._snmp_target_addrs.keys())
        for trap_rec_name in snmp_target_names:
            trap_rec = self._switch.get_snmp_target_addr(trap_rec_name)
            ip, param_name = trap_rec.get_ip(), trap_rec.get_params()
            if (not ip or not param_name or
                    (param_name not in snmp_param_names)):
                err.append('ERROR: incomplete configuration for SNMP trap'
                           ' receiver "' + trap_rec_name + '"')
                continue
            params = self._switch.get_snmp_target_params(param_name)
            community = params.get_user()
            if not community:
                err.append('ERROR: user (community) missing from SNMP target'
                           ' parameters "' + param_name + '"')
                continue
            conf.append('configure snmp add trapreceiver ' + str(ip) +
                        ' community ' + str(community))
            trap_rec.set_is_written(True)
            params.set_is_written(True)
        # user accounts
        account_names = sorted(self._switch._user_accounts.keys())
        # admin is mapped to admin -> nothing to do
        # rw is not mapped -> just warn
        # ro is mapped to user -> copy settings
        if 'rw' in account_names:
            err.append('NOTICE: Ignoring user account "rw" as XOS does not'
                       ' differentiate super-user rights from read-write')
            acc_rw = self._switch.get_user_account('rw')
            acc_rw.set_is_written(True)
            account_names.remove('rw')
        if 'ro' in account_names:
            err.append('NOTICE: Transfering "ro" user account settings to'
                       ' "user"')
            acc_ro = self._switch.get_user_account('ro')
            acc_ro.set_is_written(True)
            acc_user = self._switch.get_user_account('user')
            # if defaults are ignored, no account "user" existed before
            if 'user' not in account_names:
                account_names.append('user')
            acc_user.transfer_config(acc_ro)
            acc_user.set_name('user')
            account_names.remove('ro')
        elif 'user' in account_names:
            acc_user = self._switch.get_user_account('user')
            if acc_user.get_is_default() is True:
                err.append('NOTICE: Removing default user account "user"'
                           ' because equivalent EOS default user account "ro"'
                           ' is missing')
                conf.append('delete account user')
                account_names.remove('user')
        # write remaining accounts
        for a_name in account_names:
            acc = self._switch.get_user_account(a_name)
            a_pass = acc.get_password()
            if not acc.get_is_default():
                if self._is_exos_keyword(a_name):
                    err.append('WARN: Replaced account name "' + a_name + '"'
                               ' with "acc_' + a_name + '" because "' +
                               a_name + '" is a reserved keyword in XOS')
                    a_name = 'acc_' + a_name
                c = 'create account '
                if acc.get_type() in {'super-user', 'read-write'}:
                    c += 'admin '
                else:
                    c += 'user '
                c += a_name
                if a_pass:
                    c += ' ' + a_pass
                conf.append(c)
            elif a_pass:
                err.append('ERROR: Cannot configure clear text password on'
                           ' default user account "' + a_name +
                           '" non-interactively')
                err.append('INFO: Password for default user account "' +
                           a_name + '" can be configured interactively using '
                           '"configure account ' + a_name + '" on XOS')
            if not a_pass:
                err.append('NOTICE: User account "' + a_name + '" has no'
                           ' password, consider setting with "configure'
                           ' account ' + a_name + '" on XOS')
            a_state = acc.get_state()
            if a_state == 'disable':
                conf.append('disable account ' + a_name)
            acc.set_is_written(True)
        # return configuration and errors
        return conf, err

    def basic_layer_3(self):
        conf, err = [], []
        ipv4_routing = self._switch.get_ipv4_routing()
        self._switch.set_ipv4_routing(ipv4_routing, 'written')
        # SVI IPv4 addresses are implemented in method vlan()
        # Loopback Interfaces
        for lo in self._switch.get_all_loopbacks():
            vlan_name = 'Interface_Loopback_' + str(lo.get_number())
            if self._switch.get_vlan(name=vlan_name) is not None:
                err.append('ERROR: Cannot create VLAN "' + vlan_name + '" '
                           'for interface Loopback ' + str(lo.get_number()) +
                           ' because it already exists')
                continue
            conf.append('create vlan ' + vlan_name)
            conf.append('enable loopback-mode vlan ' + vlan_name)

            ipv4_addresses = lo.get_ipv4_addresses()
            for (idx, ipv4_addr) in enumerate(ipv4_addresses):
                if idx == 0:
                    conf.append('configure vlan ' + vlan_name +
                                ' ipaddress ' + ipv4_addr[0] + ' ' +
                                ipv4_addr[1])
                    if ipv4_routing:
                        conf.append('enable ipforwarding vlan ' + vlan_name)
                else:
                    conf.append('configure vlan ' + vlan_name + ' add '
                                'secondary-ipaddress ' + ipv4_addr[0] + ' ' +
                                ipv4_addr[1])
            if lo.get_svi_shutdown() is True:
                err.append('WARN: XOS cannot disable switched virtual '
                           'interfaces, ignoring shutdown state of interface '
                           'Loopback ' + str(lo.get_number()))
        # IPv4 routes need to come after VLAN IPv4 addresses
        for route in sorted(self._switch.get_all_ipv4_static_routes()):
            if route[0] == '0.0.0.0' and route[1] == '0.0.0.0':
                conf.append('configure iproute add default ' + route[2])
            else:
                conf.append('configure iproute add ' + route[0] + ' ' +
                            route[1] + ' ' + route[2])
        return conf, err

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
