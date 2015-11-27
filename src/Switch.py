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

"""Model of a generic switch.

Classes:
Switch represents a generic switch. Usually subclassed for vendors.
CmdInterpreter applies a given configuration. Needs to be subclassed.
ConfigWriter writes configuration commands. Needs to be subclassed.
"""

import cmd
import ipaddress
import json

import ACL
import Account
import Loopback
import Port
import RadiusServer
import SnmpTargetAddr
import SnmpTargetParams
import SntpServer
import SyslogServer
import TacacsServer
import VLAN


class Switch:

    """Model of a generic switch, usually subclassed.

    This class should be used as an abstract base class defining the
    Switch interface. Create a subclass to represent a switch class
    using the same operating system.
    """

    DEFAULT_PORT_NAME = 'nn'

    def __init__(self):
        self._model = None
        self._os = None
        self._ports = []
        self._hw_desc = []
        self._cmd = CmdInterpreter()
        self._writer = ConfigWriter(self)
        self._stack = False
        self._vlans = []
        self._loopbacks = []
        self._lags = []
        self._stps = []
        self._acls = []
        self._syslog_servers = {}
        self._sntp_servers = []
        self._radius_servers = {}
        self._tacacs_servers = {}
        self._ipv4_static_routes = set()
        self._use_oob_mgmt = False
        self._snmp_target_params = {}
        self._snmp_target_addrs = {}
        self._user_accounts = {}
        self._init_configurable_attributes()

    def _init_configurable_attributes(self):
        self._lacp_support = (None, None)
        self._max_lag = (None, None)
        self._single_port_lag = (None, None)
        self._applied_defaults = False
        self._prompt = (None, None)
        self._snmp_sys_name = (None, None)
        self._snmp_sys_contact = (None, None)
        self._snmp_sys_location = (None, None)
        self._banner_login = (None, None)
        self._banner_motd = (None, None)
        self._banner_login_ack = (None, None)
        self._telnet_inbound = (None, None)
        self._telnet_outbound = (None, None)
        self._ssh_inbound = (None, None)
        self._ssh_outbound = (None, None)
        self._http = (None, None)
        self._http_secure = (None, None)
        self._ssl = (None, None)
        self._mgmt_ip = (None, None)
        self._mgmt_mask = (None, None)
        self._mgmt_vlan = (None, None)
        self._mgmt_gw = (None, None)
        self._mgmt_protocol = (None, None)
        self._idle_timer = (None, None)
        self._sntp_client = (None, None)
        self._ipv4_routing = (None, None)
        self._tz_name = (None, None)
        self._tz_off_min = (None, None)
        self._tz_dst_state = (None, None)
        self._tz_dst_name = (None, None)
        self._tz_dst_start = (None, None)
        self._tz_dst_end = (None, None)
        self._tz_dst_off_min = (None, None)
        self._radius_mgmt_acc_enabled = (None, None)
        self._radius_interface = (None, None)
        self._tacacs_enabled = (None, None)
        self._tacacs_interface = (None, None)

    def __str__(self):
        description = ' Model: ' + str(self._model) + '\n'
        if self._stack:
            description += '  [This switch is a stack.]\n'
        description += ' OS:    ' + str(self._os)
        description += '\n Prompt: ' + str(self._prompt)
        description += '\n SNMP SysName: ' + str(self._snmp_sys_name)
        description += '\n SNMP SysContact: ' + str(self._snmp_sys_contact)
        description += '\n SNMP SysLocation: ' + str(self._snmp_sys_location)
        description += '\n Login Banner: ' + str(self._banner_login)
        description += '\n Login Banner Acknowledge: '
        description += str(self._banner_login_ack)
        description += '\n MOTD Banner: ' + str(self._banner_motd)
        description += '\n Inbound Telnet: ' + str(self._telnet_inbound)
        description += '\n Outbound Telnet: ' + str(self._telnet_outbound)
        description += '\n Inbound SSH: ' + str(self._ssh_inbound)
        description += '\n Outbound SSH: ' + str(self._ssh_outbound)
        description += '\n SSL: ' + str(self._ssl)
        description += '\n HTTP: ' + str(self._http)
        description += '\n HTTPS: ' + str(self._http_secure)
        description += '\n Mgmt IP: ' + str(self._mgmt_ip)
        description += '\n Mgmt Netmask: ' + str(self._mgmt_mask)
        description += '\n Mgmt VLAN: ' + str(self._mgmt_vlan)
        description += '\n Mgmt Gateway: ' + str(self._mgmt_gw)
        description += '\n Mgmt Protocol: ' + str(self._mgmt_protocol)
        description += '\n Idle Timeout: ' + str(self._idle_timer)
        description += '\n Syslog Servers:'
        for s in self._syslog_servers:
            description += ' (' + str(s) + ':' + str(self._syslog_servers[s])
            description += ')'
        description += '\n SNTP Client Mode: ' + str(self._sntp_client)
        description += '\n SNTP Servers:'
        for s in self._sntp_servers:
            description += ' (' + str(s) + ')'
        description += '\n RADIUS Servers:'
        for r in self._radius_servers:
            description += ' (' + str(r) + ': ' + str(self._radius_servers[r])
            description += ')'
        description += '\n RADIUS for Management Access: '
        description += str(self._radius_mgmt_acc_enabled)
        description += '\n RADIUS Interface: ' + str(self._radius_interface)
        description += '\n TACACS+: ' + str(self._tacacs_enabled)
        description += '\n TACACS+ Interface: ' + str(self._tacacs_interface)
        description += '\n TACACS+ Servers:'
        for t in self._tacacs_servers:
            description += ' (' + str(t) + ': ' + str(self._tacacs_servers[t])
            description += ')'
        description += '\n Ports:'
        for p in self._ports:
            description += ' (' + str(p) + ')'
        description += '\n VLANs:'
        for v in self._vlans:
            description += ' (' + str(v) + ')'
        description += '\n Loopbacks:'
        for l in self._loopbacks:
            description += ' (' + str(l) + ')'
        description += '\n LAGs:'
        for l in self._lags:
            description += ' (' + str(l) + ')'
        description += '\n Global LACP: ' + str(self._lacp_support)
        description += '\n Max. LAGs: ' + str(self._max_lag)
        description += '\n Single Port LAG: ' + str(self._single_port_lag)
        description += '\n Spanning Tree:'
        for s in self._stps:
            description += ' (' + str(s) + ')'
        description += '\n ACLs:'
        for a in self._acls:
            description += ' (' + str(a) + ')'
        description += '\n IPv4 Routing: ' + str(self._ipv4_routing)
        description += '\n IPv4 Static Routes: '
        description += str(self._ipv4_static_routes)
        description += '\n Timezone Name: ' + str(self._tz_name)
        description += '\n Timezone Offset (Minutes): ' + str(self._tz_off_min)
        description += '\n Timezone DST State: ' + str(self._tz_dst_state)
        description += '\n Timezone DST Name: ' + str(self._tz_dst_name)
        description += '\n Timezone DST Start: ' + str(self._tz_dst_start)
        description += '\n Timezone DST End: ' + str(self._tz_dst_end)
        description += ('\n Timezone DST Offset (Minutes): ' +
                        str(self._tz_dst_off_min))
        description += '\n SNMP Target Parameters:'
        for t in self._snmp_target_params:
            description += ' (' + str(t) + ': '
            description += str(self._snmp_target_params[t]) + ')'
        description += '\n SNMP Target Addresses:'
        for t in self._snmp_target_addrs:
            description += ' (' + str(t) + ': '
            description += str(self._snmp_target_addrs[t]) + ')'
        description += '\n User Accounts:'
        for u in self._user_accounts:
            description += ' (' + str(self._user_accounts[u]) + ')'
        description += '\n'
        return description

    def init_conf_values(self):
        self._init_configurable_attributes()
        default_vlan = VLAN.VLAN(tag=1, switch=self)
        for p in self._ports:
            p.init_conf_values()
            default_vlan.add_ingress_port(p.get_name(), 'untagged')
            default_vlan.add_egress_port(p.get_name(), 'untagged')
        for l in self._lags:
            default_vlan.add_ingress_port(l.get_name(), 'untagged')
            default_vlan.add_egress_port(l.get_name(), 'untagged')
        self._vlans = [default_vlan]

    def apply_default_settings(self):
        self._applied_defaults = True

    def _apply_default_port_settings(self, port):
        pass

    def defaults_were_applied(self):
        return self._applied_defaults

    def get_model(self):
        return self._model

    def get_os(self):
        return self._os

    def get_ports(self):
        return self._ports

    def set_combo_using_sfp(self, sfp_list):
        """Register that the given combo ports use SFP modules."""
        err = []
        for name in sfp_list:
            p_list = self.get_ports_by_name(name)
            if not p_list:
                err.append('ERROR: Non-existing port "' + name + '" cannot use'
                           ' an SFP module')
            for p in p_list:
                if (p.get_connector() == 'combo' or
                        p.get_connector() == 'sfp'):
                    p.set_connector_used('sfp')
                else:
                    n = p.get_name()
                    err.append(
                        'ERROR: Port {} cannot use an SFP module'.format(n)
                    )
        return err

    def is_stack(self):
        return self._stack

    def set_stack(self, is_stack):
        self._stack = is_stack

    def uses_oob_mgmt(self):
        return self._use_oob_mgmt

    def _build_port_name(self, index, name_dict, slot):
        return Switch.DEFAULT_PORT_NAME

    def _add_ports(self, ports_dict, slot):
        start_index = int(ports_dict['label']['start'])
        end_index = int(ports_dict['label']['end']) + 1
        start_name = int(ports_dict['name']['start'])
        end_name = int(ports_dict['name']['end']) + 1
        for i, n in zip(range(start_index, end_index),
                        range(start_name, end_name)):
            label = str(i)
            name = self._build_port_name(str(n), ports_dict['name'], slot)
            p = Port.Port(label, name, ports_dict['data'])
            self._ports.append(p)

    def add_lag(self, lag):
        if self._max_lag[0] is None or len(self._lags) < self._max_lag[0]:
            for l in self._lags:
                if l.get_name() == lag.get_name():
                    return ('ERROR: LAG with name "' + lag.get_name() +
                            '" already exists, cannot add it to switch again')
            self._lags.append(lag)
            return ''
        else:
            return 'ERROR: Could not add LAG to ' + self._model

    def create_lag_name(self, lag_number, lag_ports):
        return '_new_lag_' + str(lag_number)

    def _setup_hw(self):
        """Initialize the hardware model based on a hardware description.

        The hardware description is provided using JSON. This JSON data
        structure is added as the specialized attribute of a Switch subclass
        (respectively in a subclass of an OS specific subclass of Switch).
        """
        self._ports = []
        for slot, port_lst in enumerate(self._hw_desc, 1):
            for l in port_lst:
                data = json.loads(l)
                self._add_ports(data['ports'], slot)

    def _port_name_matches_description(self, name, description):
        if name == description:
            return True
        return False

    def get_ports_by_name(self, name):
        pl = []
        for p in self._ports + self._lags:
            if self._port_name_matches_description(p.get_name(), name):
                pl.append(p)
        return pl

    def get_physical_ports_by_name(self, name):
        pl = []
        for p in self._ports:
            if self._port_name_matches_description(p.get_name(), name):
                pl.append(p)
        return pl

    def get_lags_by_name(self, name):
        ll = []
        for l in self._lags:
            if self._port_name_matches_description(l.get_name(), name):
                ll.append(l)
        return ll

    def normalize_config(self, config):
        return config, []

    def expand_macros(self, config):
        return config, []

    def configure(self, line):
        return self._cmd.onecmd(line)

    def create_config(self, use_oob_mgmt):
        self._use_oob_mgmt = use_oob_mgmt
        return self._writer.generate()

    def get_cmd(self):
        return self._cmd

    def get_vlan(self, name=None, tag=None):
        if name is None and tag is None:
            return None
        elif name is None:
            def pred(v, n, t):
                return v.get_tag() == t
        elif tag is None:
            def pred(v, n, t):
                return v.get_name() == n
        else:
            def pred(v, n, t):
                return v.get_name() == n and v.get_tag() == t
        vl = [vlan for vlan in self._vlans if pred(vlan, name, tag)]
        if len(vl) == 1:
            return vl[0]
        else:
            return None

    def get_all_vlans(self):
        return self._vlans

    def add_vlan(self, vlan):
        exists = self.get_vlan(vlan.get_name(), vlan.get_tag())
        if not exists:
            self._vlans.append(vlan)

    def is_port_in_non_default_vlan(self, portname):
        for vlan in self._vlans:
            if vlan.get_tag() == 1:
                continue
            if vlan.contains_port(portname):
                return True
        return False

    def get_lacp_support(self):
        return self._lacp_support[0]

    def get_lacp_support_reason(self):
        return self._lacp_support[1]

    def set_lacp_support(self, state, reason):
        try:
            self._lacp_support = (bool(state), reason)
        except:
            return None
        return self._lacp_support[0]

    def get_lags(self):
        return self._lags

    def get_logical_ports(self):
        """Return a list of the logical ports.

        A logical port is either a physical port that is not part of a LAG,
        a seperatly configured logical port (e.g. lag.0.1), or the master
        port of the LAG (used by XOS)
        """
        member_ports = []
        for lag in self._lags:
            members = lag.get_members()
            member_ports.extend(members)
        logical_ports = [p for p in self._ports
                         if p.get_name() not in member_ports]
        return logical_ports + self._lags

    def get_lag_by_number(self, number):
        if number < 1 or number > len(self._lags):
            return None
        else:
            return self._lags[number - 1]

    def get_lag_ports(self, number):
        if number < 1 or number > len(self._lags):
            return []
        return self._lags[number - 1].get_members()

    def get_single_port_lag(self):
        return self._single_port_lag[0]

    def get_single_port_lag_reason(self):
        return self._single_port_lag[1]

    def set_single_port_lag(self, state, reason):
        try:
            self._single_port_lag = (bool(state), reason)
        except:
            return None
        return self._single_port_lag[0]

    def get_max_lag(self):
        return self._max_lag[0]

    def get_max_lag_reason(self):
        return self._max_lag[1]

    def set_max_lag(self, number, reason):
        try:
            self._max_lag = (int(number), reason)
        except:
            return None
        return self._max_lag[0]

    def get_stps(self):
        return self._stps

    def get_stp_by_mst_instance(self, sid):
        for stp in self._stps:
            if (stp.get_mst_instance() is not None and
                    stp.get_mst_instance() == sid):
                return stp
        return None

    def add_stp(self, stp):
        if stp not in self._stps:
            self._stps.append(stp)
        return self._stps

    def delete_last_n_stps(self, number):
        self._stps = self._stps[:-number]

    def delete_stp_by_instance_id(self, sid):
        err = ''
        index_list = []
        for i in range(0, len(self._stps)):
            if (self._stps[i].get_mst_instance() and
               self._stps[i].get_mst_instance() == sid):
                index_list.append(i)
        nr_sid_stps = len(index_list)
        if nr_sid_stps <= 0:
            return ('WARN: Cannot delete MST instance "' + str(sid) + '": '
                    ' Instance does not exist')
        elif nr_sid_stps > 1:
            err = ('WARN: Found more than 1 MST instance "' + str(sid) + '": '
                   'Deleting all')
        index_list.reverse()
        for i in index_list:
            self._stps.pop(i)
        return err

    def set_prompt(self, name, reason):
        self._prompt = (name, reason)

    def get_prompt(self):
        return self._prompt[0]

    def get_prompt_reason(self):
        return self._prompt[1]

    def set_snmp_sys_name(self, name, reason):
        self._snmp_sys_name = (name, reason)

    def get_snmp_sys_name(self):
        return self._snmp_sys_name[0]

    def get_snmp_sys_name_reason(self):
        return self._snmp_sys_name[1]

    def set_snmp_sys_contact(self, name, reason):
        self._snmp_sys_contact = (name, reason)

    def get_snmp_sys_contact(self):
        return self._snmp_sys_contact[0]

    def get_snmp_sys_contact_reason(self):
        return self._snmp_sys_contact[1]

    def set_snmp_sys_location(self, name, reason):
        self._snmp_sys_location = (name, reason)

    def get_snmp_sys_location(self):
        return self._snmp_sys_location[0]

    def get_snmp_sys_location_reason(self):
        return self._snmp_sys_location[1]

    def set_banner_login(self, banner_str, reason):
        self._banner_login = (banner_str, reason)

    def get_banner_login(self):
        return self._banner_login[0]

    def get_banner_login_reason(self):
        return self._banner_login[1]

    def set_banner_motd(self, banner_str, reason):
        self._banner_motd = (banner_str, reason)

    def get_banner_motd(self):
        return self._banner_motd[0]

    def get_banner_motd_reason(self):
        return self._banner_motd[1]

    def set_banner_login_ack(self, do_ack, reason):
        self._snmp_sys_location = (do_ack, reason)

    def get_banner_login_ack(self):
        return self._banner_login_ack[0]

    def get_banner_login_ack_reason(self):
        return self._banner_login_ack[1]

    def set_telnet_inbound(self, enabled, reason):
        self._telnet_inbound = (enabled, reason)

    def get_telnet_inbound(self):
        return self._telnet_inbound[0]

    def get_telnet_inbound_reason(self):
        return self._telnet_inbound[1]

    def set_telnet_outbound(self, enabled, reason):
        self._telnet_outbound = (enabled, reason)

    def get_telnet_outbound(self):
        return self._telnet_outbound[0]

    def get_telnet_outbound_reason(self):
        return self._telnet_outbound[1]

    def set_ssh_inbound(self, enabled, reason):
        self._ssh_inbound = (enabled, reason)

    def get_ssh_inbound(self):
        return self._ssh_inbound[0]

    def get_ssh_inbound_reason(self):
        return self._ssh_inbound[1]

    def set_ssh_outbound(self, enabled, reason):
        self._ssh_outbound = (enabled, reason)

    def get_ssh_outbound(self):
        return self._ssh_outbound[0]

    def get_ssh_outbound_reason(self):
        return self._ssh_outbound[1]

    def set_ssl(self, enabled, reason):
        self._ssl = (enabled, reason)

    def get_ssl(self):
        return self._ssl[0]

    def get_ssl_reason(self):
        return self._ssl[1]

    def set_http(self, enabled, reason):
        self._http = (enabled, reason)

    def get_http(self):
        return self._http[0]

    def get_http_reason(self):
        return self._http[1]

    def set_http_secure(self, enabled, reason):
        self._http_secure = (enabled, reason)

    def get_http_secure(self):
        return self._http_secure[0]

    def get_http_secure_reason(self):
        return self._http_secure[1]

    def set_mgmt_ip(self, address, reason):
        try:
            ip = str(ipaddress.IPv4Address(address))
        except:
            return False
        self._mgmt_ip = (ip, reason)
        return True

    def get_mgmt_ip(self):
        return self._mgmt_ip[0]

    def get_mgmt_ip_reason(self):
        return self._mgmt_ip[1]

    def set_mgmt_mask(self, mask, reason):
        try:
            netmask = str(ipaddress.IPv4Address(mask))
        except:
            return False
        self._mgmt_mask = (netmask, reason)
        return True

    def get_mgmt_mask(self):
        return self._mgmt_mask[0]

    def get_mgmt_mask_reason(self):
        return self._mgmt_mask[1]

    def set_mgmt_vlan(self, vlan, reason):
        self._mgmt_vlan = (vlan, reason)

    def get_mgmt_vlan(self):
        return self._mgmt_vlan[0]

    def get_mgmt_vlan_reason(self):
        return self._mgmt_vlan[1]

    def set_mgmt_gw(self, gateway, reason):
        try:
            gw = str(ipaddress.IPv4Address(gateway))
        except:
            return False
        self._mgmt_gw = (gw, reason)
        return True

    def get_mgmt_gw(self):
        return self._mgmt_gw[0]

    def get_mgmt_gw_reason(self):
        return self._mgmt_gw[1]

    def set_mgmt_protocol(self, protocol, reason):
        self._mgmt_protocol = (protocol, reason)

    def get_mgmt_protocol(self):
        return self._mgmt_protocol[0]

    def get_mgmt_protocol_reason(self):
        return self._mgmt_protocol[1]

    def set_idle_timer(self, value, reason):
        self._idle_timer = (value, reason)

    def get_idle_timer(self):
        return self._idle_timer[0]

    def get_idle_timer_reason(self):
        return self._idle_timer[1]

    def _create_syslog_server(self):
        return SyslogServer.SyslogServer()

    def get_syslog_server(self, index):
        if index not in self._syslog_servers:
            self._syslog_servers[index] = self._create_syslog_server()
        return self._syslog_servers.get(index)

    def get_all_syslog_servers(self):
        return self._syslog_servers

    def _create_sntp_server(self):
        return SntpServer.SntpServer()

    def get_sntp_server(self, idx):
        if 0 <= idx < len(self._sntp_servers):
            return self._sntp_servers[idx]
        elif idx == len(self._sntp_servers):
            self._sntp_servers.append(self._create_sntp_server())
            return self._sntp_servers[idx]
        else:
            return None

    def get_all_sntp_servers(self):
        return self._sntp_servers

    def _create_radius_server(self):
        return RadiusServer.RadiusServer()

    def get_radius_server(self, index):
        if index not in self._radius_servers:
            self._radius_servers[index] = self._create_radius_server()
        return self._radius_servers.get(index)

    def get_all_radius_servers(self):
        return self._radius_servers

    def _create_tacacs_server(self):
        return TacacsServer.TacacsServer()

    def get_tacacs_server(self, index):
        if index not in self._tacacs_servers:
            self._tacacs_servers[index] = self._create_tacacs_server()
        return self._tacacs_servers.get(index)

    def get_all_tacacs_servers(self):
        return self._tacacs_servers

    def set_sntp_client(self, mode, reason):
        self._sntp_client = (mode, reason)

    def get_sntp_client(self):
        return self._sntp_client[0]

    def get_sntp_client_reason(self):
        return self._sntp_client[1]

    def get_all_loopbacks(self):
        return list(self._loopbacks)

    def get_loopback(self, number):
        for lo in self._loopbacks:
            if lo.get_number() == number:
                return lo

    def add_loopback(self, number):
        for l in self._loopbacks:
            if l.get_number() == number:
                return
        lo = Loopback.Loopback(number)
        self._loopbacks.append(lo)

    def get_ipv4_routing(self):
        return self._ipv4_routing[0]

    def get_ipv4_routing_reason(self):
        return self._ipv4_routing[1]

    def set_ipv4_routing(self, state, reason):
        if state:
            self._ipv4_routing = (True, reason)
        else:
            self._ipv4_routing = (False, reason)

    def enable_ipv4_routing(self):
        return self.set_ipv4_routing(True, 'config')

    def disable_ipv4_routing(self):
        return self.set_ipv4_routing(False, 'config')

    def get_all_ipv4_static_routes(self):
        return self._ipv4_static_routes

    def set_all_ipv4_static_routes(self, routes):
        self._ipv4_static_routes = set(routes)

    def add_ipv4_static_route(self, route):
        self._ipv4_static_routes.add(route)

    def get_tz_name(self):
        return self._tz_name[0]

    def get_tz_name_reason(self):
        return self._tz_name[1]

    def set_tz_name(self, name, reason):
        self._tz_name = (name, reason)

    def get_tz_off_min(self):
        return self._tz_off_min[0]

    def get_tz_off_min_reason(self):
        return self._tz_off_min[1]

    def set_tz_off_min(self, minutes, reason):
        self._tz_off_min = (minutes, reason)

    def get_tz_dst_state(self):
        return self._tz_dst_state[0]

    def get_tz_dst_state_reason(self):
        return self._tz_dst_state[1]

    def set_tz_dst_state(self, state, reason):
        self._tz_dst_state = (state, reason)

    def enable_tz_dst(self, reason):
        return self.set_tz_dst_state('enabled', reason)

    def disable_tz_dst(self, reason):
        return self.set_tz_dst_state('disabled', reason)

    def get_tz_dst_name(self):
        return self._tz_dst_name[0]

    def get_tz_dst_name_reason(self):
        return self._tz_dst_name[1]

    def set_tz_dst_name(self, name, reason):
        self._tz_dst_name = (name, reason)

    def get_tz_dst_start(self):
        return self._tz_dst_start[0]

    def get_tz_dst_start_reason(self):
        return self._tz_dst_start[1]

    def set_tz_dst_start(self, week, day, month, hour, minute, reason):
        self._tz_dst_start = ((week, day, month, hour, minute), reason)

    def get_tz_dst_end(self):
        return self._tz_dst_end[0]

    def get_tz_dst_end_reason(self):
        return self._tz_dst_end[1]

    def set_tz_dst_end(self, week, day, month, hour, minute, reason):
        self._tz_dst_end = ((week, day, month, hour, minute), reason)

    def get_tz_dst_off_min(self):
        return self._tz_dst_off_min[0]

    def get_tz_dst_off_min_reason(self):
        return self._tz_dst_off_min[1]

    def set_tz_dst_off_min(self, minutes, reason):
        self._tz_dst_off_min = (minutes, reason)

    def get_radius_mgmt_acc_enabled(self):
        return self._radius_mgmt_acc_enabled[0]

    def get_radius_mgmt_acc_enabled_reason(self):
        return self._radius_mgmt_acc_enabled[1]

    def set_radius_mgmt_acc_enabled(self, state, reason):
        self._radius_mgmt_acc_enabled = (state, reason)

    def get_radius_interface(self):
        return self._radius_interface[0]

    def get_radius_interface_reason(self):
        return self._radius_interface[1]

    def get_radius_interface_type(self):
        if self._radius_interface[0] is not None:
            return self._radius_interface[0][0]

    def get_radius_interface_number(self):
        if self._radius_interface[0] is not None:
            return self._radius_interface[0][1]

    def set_radius_interface(self, interface, reason):
        self._radius_interface = (interface, reason)

    def get_tacacs_enabled(self):
        return self._tacacs_enabled[0]

    def get_tacacs_enabled_reason(self):
        return self._tacacs_enabled[1]

    def set_tacacs_enabled(self, state, reason):
        self._tacacs_enabled = (state, reason)

    def get_tacacs_interface(self):
        return self._tacacs_interface[0]

    def get_tacacs_interface_reason(self):
        return self._tacacs_interface[1]

    def get_tacacs_interface_type(self):
        if self._tacacs_interface[0] is not None:
            return self._tacacs_interface[0][0]

    def get_tacacs_interface_number(self):
        if self._tacacs_interface[0] is not None:
            return self._tacacs_interface[0][1]

    def set_tacacs_interface(self, interface, reason):
        self._tacacs_interface = (interface, reason)

    def _create_snmp_target_params(self):
        return SnmpTargetParams.SnmpTargetParams()

    def get_snmp_target_params(self, name):
        if name not in self._snmp_target_params:
            self._snmp_target_params[name] = self._create_snmp_target_params()
        return self._snmp_target_params.get(name)

    def get_all_snmp_target_params(self):
        return self._snmp_target_params

    def _create_snmp_target_addr(self):
        return SnmpTargetAddr.SnmpTargetAddr()

    def get_snmp_target_addr(self, name):
        if name not in self._snmp_target_addrs:
            self._snmp_target_addrs[name] = self._create_snmp_target_addr()
        return self._snmp_target_addrs.get(name)

    def get_all_snmp_target_addrs(self):
        return self._snmp_target_addrs

    def _create_user_account(self):
        return Account.UserAccount()

    def get_user_account(self, name):
        if name not in self._user_accounts:
            self._user_accounts[name] = self._create_user_account()
        return self._user_accounts.get(name)

    def get_all_user_accounts(self):
        return self._user_accounts

    def del_user_account(self, name):
        return self._user_accounts.pop(name, None)

    def transfer_config(self, from_switch):
        reason_def = 'transfer_def'
        reason_conf = 'transfer_conf'

        t_lacp_support = from_switch.get_lacp_support()
        if self._lacp_support[0] != t_lacp_support:
            if from_switch.get_lacp_support_reason() == 'default':
                self._lacp_support = (t_lacp_support, reason_def)
            else:
                self._lacp_support = (t_lacp_support, reason_conf)

        t_max_lag = from_switch.get_max_lag()
        if self._max_lag[0] != t_max_lag:
            if from_switch.get_max_lag_reason() == 'default':
                self._max_lag = (t_max_lag, reason_def)
            else:
                self._max_lag = (t_max_lag, reason_conf)

        t_single_port_lag = from_switch.get_single_port_lag()
        if self._single_port_lag[0] != t_single_port_lag:
            if from_switch.get_single_port_lag_reason() == 'default':
                self._single_port_lag = (t_single_port_lag, reason_def)
            else:
                self._single_port_lag = (t_single_port_lag, reason_conf)

        t_prompt = from_switch.get_prompt()
        if t_prompt is not None and self._prompt[0] != t_prompt:
            if from_switch.get_prompt_reason() == 'default':
                self._prompt = (t_prompt, reason_def)
            else:
                self._prompt = (t_prompt, reason_conf)

        t_snmp_sys_name = from_switch.get_snmp_sys_name()
        if (t_snmp_sys_name is not None and
           self._snmp_sys_name[0] != t_snmp_sys_name):
            if from_switch.get_snmp_sys_name_reason() == 'default':
                self._snmp_sys_name = (t_snmp_sys_name, reason_def)
            else:
                self._snmp_sys_name = (t_snmp_sys_name, reason_conf)

        t_snmp_sys_contact = from_switch.get_snmp_sys_contact()
        if (t_snmp_sys_contact is not None and
           self._snmp_sys_contact[0] != t_snmp_sys_contact):
            if from_switch.get_snmp_sys_contact_reason() == 'default':
                self._snmp_sys_contact = (t_snmp_sys_contact, reason_def)
            else:
                self._snmp_sys_contact = (t_snmp_sys_contact, reason_conf)

        t_snmp_sys_location = from_switch.get_snmp_sys_location()
        if (t_snmp_sys_location is not None and
           self._snmp_sys_location[0] != t_snmp_sys_location):
            if from_switch.get_snmp_sys_location_reason() == 'default':
                self._snmp_sys_location = (t_snmp_sys_location, reason_def)
            else:
                self._snmp_sys_location = (t_snmp_sys_location, reason_conf)

        t_banner_login_ack = from_switch.get_banner_login_ack()
        if (t_banner_login_ack is not None and
           self._banner_login_ack[0] != t_banner_login_ack):
            if from_switch.get_banner_login_ack_reason() == 'default':
                self._banner_login_ack = (t_banner_login_ack, reason_def)
            else:
                self._banner_login_ack = (t_banner_login_ack, reason_conf)

        t_banner_login = from_switch.get_banner_login()
        if (t_banner_login is not None and
           self._banner_login[0] != t_banner_login):
            if from_switch.get_banner_login_reason() == 'default':
                self._banner_login = (t_banner_login, reason_def)
            else:
                self._banner_login = (t_banner_login, reason_conf)

        t_banner_motd = from_switch.get_banner_motd()
        if (t_banner_motd is not None and
           self._banner_motd[0] != t_banner_motd):
            if from_switch.get_banner_motd_reason() == 'default':
                self._banner_motd = (t_banner_motd, reason_def)
            else:
                self._banner_motd = (t_banner_motd, reason_conf)

        t_telnet_inbound = from_switch.get_telnet_inbound()
        if (t_telnet_inbound is not None and
           self._telnet_inbound[0] != t_telnet_inbound):
            if from_switch.get_telnet_inbound_reason() == 'default':
                self._telnet_inbound = (t_telnet_inbound, reason_def)
            else:
                self._telnet_inbound = (t_telnet_inbound, reason_conf)

        t_telnet_outbound = from_switch.get_telnet_outbound()
        if (t_telnet_outbound is not None and
           self._telnet_outbound[0] != t_telnet_outbound):
            if from_switch.get_telnet_outbound_reason() == 'default':
                self._telnet_outbound = (t_telnet_outbound, reason_def)
            else:
                self._telnet_outbound = (t_telnet_outbound, reason_conf)

        t_ssh_inbound = from_switch.get_ssh_inbound()
        if (t_ssh_inbound is not None and
           self._ssh_inbound[0] != t_ssh_inbound):
            if from_switch.get_ssh_inbound_reason() == 'default':
                self._ssh_inbound = (t_ssh_inbound, reason_def)
            else:
                self._ssh_inbound = (t_ssh_inbound, reason_conf)

        t_ssh_outbound = from_switch.get_ssh_outbound()
        if (t_ssh_outbound is not None and
           self._ssh_outbound[0] != t_ssh_outbound):
            if from_switch.get_ssh_outbound_reason() == 'default':
                self._ssh_outbound = (t_ssh_outbound, reason_def)
            else:
                self._ssh_outbound = (t_ssh_outbound, reason_conf)

        t_ssl = from_switch.get_ssl()
        if (t_ssl is not None and
           self._ssl[0] != t_ssl):
            if from_switch.get_ssl_reason() == 'default':
                self._ssl = (t_ssl, reason_def)
            else:
                self._ssl = (t_ssl, reason_conf)

        t_http = from_switch.get_http()
        if (t_http is not None and
           self._http[0] != t_http):
            if from_switch.get_http_reason() == 'default':
                self._http = (t_http, reason_def)
            else:
                self._http = (t_http, reason_conf)

        t_http_secure = from_switch.get_http_secure()
        if (t_http_secure is not None and
           self._http_secure[0] != t_http_secure):
            if from_switch.get_http_secure_reason() == 'default':
                self._http_secure = (t_http_secure, reason_def)
            else:
                self._http_secure = (t_http_secure, reason_conf)

        t_mgmt_ip = from_switch.get_mgmt_ip()
        if (t_mgmt_ip is not None and
           self._mgmt_ip[0] != t_mgmt_ip):
            if from_switch.get_mgmt_ip_reason() == 'default':
                self._mgmt_ip = (t_mgmt_ip, reason_def)
            else:
                self._mgmt_ip = (t_mgmt_ip, reason_conf)

        t_mgmt_mask = from_switch.get_mgmt_mask()
        if (t_mgmt_mask is not None and
           self._mgmt_mask[0] != t_mgmt_mask):
            if from_switch.get_mgmt_mask_reason() == 'default':
                self._mgmt_mask = (t_mgmt_mask, reason_def)
            else:
                self._mgmt_mask = (t_mgmt_mask, reason_conf)

        t_mgmt_vlan = from_switch.get_mgmt_vlan()
        if (t_mgmt_vlan is not None and
           self._mgmt_vlan[0] != t_mgmt_vlan):
            if from_switch.get_mgmt_vlan_reason() == 'default':
                self._mgmt_vlan = (t_mgmt_vlan, reason_def)
            else:
                self._mgmt_vlan = (t_mgmt_vlan, reason_conf)

        t_mgmt_gw = from_switch.get_mgmt_gw()
        if (t_mgmt_gw is not None and
           self._mgmt_gw[0] != t_mgmt_gw):
            if from_switch.get_mgmt_gw_reason() == 'default':
                self._mgmt_gw = (t_mgmt_gw, reason_def)
            else:
                self._mgmt_gw = (t_mgmt_gw, reason_conf)

        t_mgmt_protocol = from_switch.get_mgmt_protocol()
        if (t_mgmt_protocol is not None and
           self._mgmt_protocol[0] != t_mgmt_protocol):
            if from_switch.get_mgmt_protocol_reason() == 'default':
                self._mgmt_protocol = (t_mgmt_protocol, reason_def)
            else:
                self._mgmt_protocol = (t_mgmt_protocol, reason_conf)

        t_idle_timer = from_switch.get_idle_timer()
        if (t_idle_timer is not None and
           self._idle_timer[0] != t_idle_timer):
            if from_switch.get_idle_timer_reason() == 'default':
                self._idle_timer = (t_idle_timer, reason_def)
            else:
                self._idle_timer = (t_idle_timer, reason_conf)

        for sys_srv_idx in from_switch.get_all_syslog_servers():
            t_sys_srv = self.get_syslog_server(sys_srv_idx)
            t_sys_srv.transfer_config(from_switch._syslog_servers[sys_srv_idx])

        for idx, sntp_srv in enumerate(from_switch.get_all_sntp_servers()):
            t_sntp_srv = self.get_sntp_server(idx)
            t_sntp_srv.transfer_config(sntp_srv)

        for rad_srv_idx in from_switch.get_all_radius_servers():
            t_rad_srv = self.get_radius_server(rad_srv_idx)
            t_rad_srv.transfer_config(from_switch._radius_servers[rad_srv_idx])

        for tac_srv_idx in from_switch.get_all_tacacs_servers():
            t_tac_srv = self.get_tacacs_server(tac_srv_idx)
            t_tac_srv.transfer_config(from_switch._tacacs_servers[tac_srv_idx])

        t_sntp_client = from_switch.get_sntp_client()
        if (t_sntp_client is not None and
           self._sntp_client[0] != t_sntp_client):
            if from_switch.get_sntp_client_reason() == 'default':
                self._sntp_client = (t_sntp_client, reason_def)
            else:
                self._sntp_client = (t_sntp_client, reason_conf)

        t_ipv4_routing = from_switch.get_ipv4_routing()
        if (t_ipv4_routing is not None and
           self._ipv4_routing[0] != t_ipv4_routing):
            if from_switch.get_ipv4_routing_reason() == 'default':
                self._ipv4_routing = (t_ipv4_routing, reason_def)
            else:
                self._ipv4_routing = (t_ipv4_routing, reason_conf)

        self.set_all_ipv4_static_routes(
            from_switch.get_all_ipv4_static_routes())

        t_tz_name = from_switch.get_tz_name()
        if (t_tz_name is not None and
           self._tz_name[0] != t_tz_name):
            if from_switch.get_tz_name_reason() == 'default':
                self._tz_name = (t_tz_name, reason_def)
            else:
                self._tz_name = (t_tz_name, reason_conf)

        t_tz_off_min = from_switch.get_tz_off_min()
        if (t_tz_off_min is not None and
           self._tz_off_min[0] != t_tz_off_min):
            if from_switch.get_tz_off_min_reason() == 'default':
                self._tz_off_min = (t_tz_off_min, reason_def)
            else:
                self._tz_off_min = (t_tz_off_min, reason_conf)

        t_tz_dst_state = from_switch.get_tz_dst_state()
        if (t_tz_dst_state is not None and
           self._tz_dst_state[0] != t_tz_dst_state):
            if from_switch.get_tz_dst_state_reason() == 'default':
                self._tz_dst_state = (t_tz_dst_state, reason_def)
            else:
                self._tz_dst_state = (t_tz_dst_state, reason_conf)

        t_tz_dst_name = from_switch.get_tz_dst_name()
        if (t_tz_dst_name is not None and
           self._tz_dst_name[0] != t_tz_dst_name):
            if from_switch.get_tz_dst_name_reason() == 'default':
                self._tz_dst_name = (t_tz_dst_name, reason_def)
            else:
                self._tz_dst_name = (t_tz_dst_name, reason_conf)

        t_tz_dst_start = from_switch.get_tz_dst_start()
        if (t_tz_dst_start is not None and
           self._tz_dst_start[0] != t_tz_dst_start):
            if from_switch.get_tz_dst_start_reason() == 'default':
                self._tz_dst_start = (t_tz_dst_start, reason_def)
            else:
                self._tz_dst_start = (t_tz_dst_start, reason_conf)

        t_tz_dst_end = from_switch.get_tz_dst_end()
        if (t_tz_dst_end is not None and
           self._tz_dst_end[0] != t_tz_dst_end):
            if from_switch.get_tz_dst_end_reason() == 'default':
                self._tz_dst_end = (t_tz_dst_end, reason_def)
            else:
                self._tz_dst_end = (t_tz_dst_end, reason_conf)

        t_tz_dst_off_min = from_switch.get_tz_dst_off_min()
        if (t_tz_dst_off_min is not None and
           self._tz_dst_off_min[0] != t_tz_dst_off_min):
            if from_switch.get_tz_dst_off_min_reason() == 'default':
                self._tz_dst_off_min = (t_tz_dst_off_min, reason_def)
            else:
                self._tz_dst_off_min = (t_tz_dst_off_min, reason_conf)

        t_radius_mgmt_acc_enabled = from_switch.get_radius_mgmt_acc_enabled()
        if (t_radius_mgmt_acc_enabled is not None and
           self._radius_mgmt_acc_enabled[0] != t_radius_mgmt_acc_enabled):
            if from_switch.get_radius_mgmt_acc_enabled_reason() == 'default':
                self._radius_mgmt_acc_enabled = (t_radius_mgmt_acc_enabled,
                                                 reason_def)
            else:
                self._radius_mgmt_acc_enabled = (t_radius_mgmt_acc_enabled,
                                                 reason_conf)

        t_tacacs_enabled = from_switch.get_tacacs_enabled()
        if (t_tacacs_enabled is not None and
           self._tacacs_enabled[0] != t_tacacs_enabled):
            if from_switch.get_tacacs_enabled_reason() == 'default':
                self._tacacs_enabled = (t_tacacs_enabled, reason_def)
            else:
                self._tacacs_enabled = (t_tacacs_enabled, reason_conf)

        t_radius_interface = from_switch.get_radius_interface()
        if (t_radius_interface is not None and
           self._radius_interface[0] != t_radius_interface):
            if from_switch.get_radius_interface_reason() == 'default':
                self._radius_interface = (t_radius_interface, reason_def)
            else:
                self._radius_interface = (t_radius_interface, reason_conf)

        t_tacacs_interface = from_switch.get_tacacs_interface()
        if (t_tacacs_interface is not None and
           self._tacacs_interface[0] != t_tacacs_interface):
            if from_switch.get_tacacs_interface_reason() == 'default':
                self._tacacs_interface = (t_tacacs_interface, reason_def)
            else:
                self._tacacs_interface = (t_tacacs_interface, reason_conf)

        for snmp_tgt_prm_name in from_switch.get_all_snmp_target_params():
            t_snmp_tgt_prm = self.get_snmp_target_params(snmp_tgt_prm_name)
            t_snmp_tgt_prm.transfer_config(
                from_switch._snmp_target_params[snmp_tgt_prm_name])

        for snmp_tgt_addr_name in from_switch.get_all_snmp_target_addrs():
            t_snmp_tgt_addr = self.get_snmp_target_addr(snmp_tgt_addr_name)
            t_snmp_tgt_addr.transfer_config(
                from_switch._snmp_target_addrs[snmp_tgt_addr_name])

        for user_account_name in from_switch.get_all_user_accounts():
            t_user_account = self.get_user_account(user_account_name)
            t_user_account.transfer_config(
                from_switch._user_accounts[user_account_name])

    def get_acls(self):
        return self._acls

    def get_acl_by_name(self, name):
        if not name:
            return None
        for acl in self._acls:
            if acl.get_name() == name:
                return acl
        return None

    def get_acl_by_number(self, number):
        if not number:
            return None
        for acl in self._acls:
            if acl.get_number() == number:
                return acl
        return None

    # TODO This is ambiguous
    def add_acl(self, number=None, name=None):
        if number is None and not name:
            return 'ERROR: ACL needs name or number'
        if number and name:
            return 'ERROR: ACL can have either name or number, but not both'
        acl = None
        if number and self.get_acl_by_number(number):
            return 'ERROR: ACL "' + str(number) + '" already exists'
        elif name and self.get_acl_by_name(name):
            return 'ERROR: ACL "' + str(name) + '" already exists'
        acl = ACL.ACL(number=number, name=name)
        self._acls.append(acl)
        return ''

    def add_complete_acl(self, new_acl):
        self._acls.append(new_acl)


class CmdInterpreter(cmd.Cmd):

    """Interface definition for a command interpreter based on cmd."""

    def __init__(self):
        super().__init__()
        self._comments = []
        self._state = []

    def _is_comment(self, line):
        for c in self._comments:
            if line.lstrip().startswith(c):
                return True
        return False

    def emptyline(self):
        return ''

    def default(self, line):
        if self._is_comment(line):
            return 'INFO: Ignoring comment "' + line + '"'
        return 'NOTICE: Ignoring unknown command "' + line + '"'

    def get_comment(self):
        if self._comments:
            return self._comments[0]
        else:
            return None

    def _check_quoting(self, s):
        err = ''
        if (len(s.split()) != 1 and
                not (s.startswith('"') and s.rstrip().endswith('"'))):
            err += 'WARN: Names containing spaces must be '
            err += 'enclosed in double quotes (' + s + ')'
        elif (s.startswith('"') and not s.rstrip().endswith('"')):
            err = "WARN: No closing double quote in '" + s + "'"
        return err


class ConfigWriter:

    """Interface definition of a configuration writer.

    This is used to register feature modules and to check for configuration
    parts that are not considered by the used subclass of ConfigWriter.

    Actual generation of configuration commands is implemented using
    subclasses.
    """

    def __init__(self, switch):
        self._feature_modules = ['port', 'lag', 'vlan', 'stp', 'acl',
                                 'basic_layer_3', 'mgmt']
        self._switch = switch

    def check_unwritten(self):
        """Check if some configuration has not been considered.

        This is a generic check if the subclassed ConfigWriter actually used
        supports and considers every configuration supported by the feature
        modules.
        """
        unwritten = []
        # feature module ports
        for p in self._switch.get_ports():
            if p.get_speed_reason() == 'transfer_conf':
                msg = 'WARN: Speed of port "{}" set to "{}"'.format(
                    p.get_name(), p.get_speed())
                msg += ' omitted from configuration file'
                unwritten.append(msg)
            if p.get_duplex_reason() == 'transfer_conf':
                msg = 'WARN: Duplex of port "{}" set to "{}"'.format(
                    p.get_name(), p.get_duplex())
                msg += ' omitted from configuration file'
                unwritten.append(msg)
            if p.get_auto_neg_reason() == 'transfer_conf':
                msg = 'WARN: Auto-negotiation of port "%s" set to "%s"' % (
                    p.get_name(), p.get_auto_neg())
                msg += ' omitted from configuration file'
                unwritten.append(msg)
            if p.get_admin_state_reason() == 'transfer_conf':
                msg = 'WARN: Admin state of port "{}" set to "{}"'.format(
                    p.get_name(), p.get_admin_state())
                msg += ' omitted from configuration file'
                unwritten.append(msg)
            if p.get_lacp_enabled_reason() == 'transfer_conf':
                msg = 'WARN: LACP state of port "{}" set to "{}"'.format(
                    p.get_name(), p.get_lacp_enabled())
                msg += ' omitted from configuration file'
                unwritten.append(msg)
            if p.get_lacp_aadminkey_reason() == 'transfer_conf':
                msg = 'WARN: LACP aadminkey of port "{}" set to "{}"'.format(
                    p.get_name(), p.get_lacp_aadminkey())
                msg += ' omitted from configuration file'
                unwritten.append(msg)
            if p.get_stp_enabled_reason() == 'transfer_conf':
                msg = 'WARN: STP status of port "{}" set to "{}"'.format(
                    p.get_name(), p.get_stp_enabled())
                msg += ' omitted from configuration file'
                unwritten.append(msg)
            if p.get_stp_auto_edge_reason() == 'transfer_conf':
                msg = ('WARN: STP auto edge detection of port "{}" set to'
                       ' "{}"'.format(p.get_name(), p.get_stp_auto_edge()))
                msg += ' omitted from configuration file'
                unwritten.append(msg)
            if p.get_stp_edge_reason() == 'transfer_conf':
                msg = 'WARN: STP edge status of port "{}" set to "{}"'.format(
                    p.get_name(), p.get_stp_edge())
                msg += ' omitted from configuration file'
                unwritten.append(msg)
            if (p.get_stp_bpdu_guard_reason() == 'transfer_conf' and
                    p.get_stp_edge()):
                msg = 'WARN: STP SpanGuard of port "{}" set to "{}"'.format(
                    p.get_name(), p.get_stp_bpdu_guard())
                msg += ' omitted from configuration file'
                unwritten.append(msg)
            if p.get_stp_bpdu_guard_recovery_time_reason() == 'transfer_conf':
                msg = ('WARN: STP SpanGuard recovery time of port "{}" set to'
                       ' "{}"'.format(p.get_name(),
                                      p.get_stp_bpdu_guard_recovery_time()))
                msg += ' omitted from configuration file'
                unwritten.append(msg)
            if p.get_ipv4_acl_in_reason() == 'transfer_conf':
                msg = 'WARN: Inbound ACL of port "{}" set to "{}"'.format(
                    p.get_name(), str(p.get_ipv4_acl_in()))
                msg += ' omitted from configuration file'
                unwritten.append(msg)
        # TODO: implement "unwritten" check for feature module VLAN
        # feature module lacp
        if self._switch.get_lacp_support_reason() == 'transfer_conf':
            msg = 'WARN: '
            msg += 'Enabled' if self._switch.get_lacp_support() else 'Disabled'
            msg += ' global LACP support omitted from configuration file'
            unwritten.append(msg)
        if self._switch.get_max_lag_reason() == 'transfer_conf':
            msg = 'WARN: Maximum number of LAGs set to "{}"'.format(
                  self._switch.get_max_lag())
            msg += ' omitted from configuration file'
            unwritten.append(msg)
        if self._switch.get_single_port_lag_reason() == 'transfer_conf':
            msg = 'WARN: '
            msg += ('Enabled' if self._switch.get_single_port_lag()
                    else 'Disabled')
            msg += ' single port LAG support omitted from configuration file'
            unwritten.append(msg)
        # feature module STP
        for stp in self._switch.get_stps():
            if stp.get_name_reason() == 'transfer_conf':
                unwritten.append('WARN: STP process name "' + stp.get_name() +
                                 '" configured, but omitted from configuration'
                                 ' file')
            if stp.get_enabled_reason() == 'transfer_conf':
                unwritten.append('ERROR: STP enabled, but omitted from'
                                 ' configuration file')
            if stp.get_version_reason() == 'transfer_conf':
                unwritten.append('ERROR: STP version "' +
                                 str(stp.get_version()) + '" configured, but' +
                                 ' omitted from configuration file')
            if stp.get_priority_reason() == 'transfer_conf':
                unwritten.append('ERROR: STP priority "' +
                                 str(stp.get_priority()) + '" configured, but'
                                 ' omitted from configuration file')
            if stp.get_mst_cfgname_reason() == 'transfer_conf':
                unwritten.append('ERROR: MST configuration name "' +
                                 stp.get_mst_cfgname() + '" configured, but'
                                 ' omitted from configuration file')
            if stp.get_mst_rev_reason() == 'transfer_conf':
                unwritten.append('ERROR: MST configuration revision "' +
                                 str(stp.get_mst_rev()) + '" configured, but'
                                 ' omitted from configuration file')
            if stp.get_mst_instance_reason() == 'transfer_conf':
                unwritten.append('ERROR: MST instance "' +
                                 str(stp.get_mst_instance()) + '" configured,'
                                 ' but omitted from configuration file')
            if stp.get_vlans_reason() == 'transfer_conf':
                unwritten.append('ERROR: MST instance "' +
                                 str(stp.get_mst_instance()) +
                                 '" with associated'
                                 ' VLANs configured, but omitted from'
                                 ' configuration file')
        # feature module management
        if self._switch.get_prompt_reason() == 'transfer_conf':
            unwritten.append('WARN: CLI prompt "' +
                             str(self._switch.get_prompt()) + '" configured,'
                             ' but omitted from configuration file')
        if self._switch.get_snmp_sys_name_reason() == 'transfer_conf':
            unwritten.append('WARN: SNMP system name "' +
                             str(self._switch.get_snmp_sys_name()) +
                             '" configured, but omitted from configuration'
                             ' file')
        if self._switch.get_snmp_sys_contact_reason() == 'transfer_conf':
            unwritten.append('WARN: SNMP system contact "' +
                             str(self._switch.get_snmp_sys_contact()) +
                             '" configured, but omitted from configuration'
                             ' file')
        if self._switch.get_snmp_sys_location_reason() == 'transfer_conf':
            unwritten.append('WARN: SNMP system location "' +
                             str(self._switch.get_snmp_sys_location()) +
                             '" configured, but omitted from configuration'
                             ' file')
        if self._switch.get_banner_login_reason() == 'transfer_conf':
            unwritten.append('WARN: Login banner "' +
                             str(self._switch.get_banner_login()) +
                             '" configured, but omitted from configuration'
                             ' file')
        if self._switch.get_banner_login_ack_reason() == 'transfer_conf':
            unwritten.append('WARN: Login banner acknowledgement'
                             ' configured, but omitted from configuration'
                             ' file')
        if self._switch.get_banner_motd_reason() == 'transfer_conf':
            unwritten.append('WARN: Message of the day banner "' +
                             str(self._switch.get_banner_motd()) +
                             '" configured, but omitted from configuration'
                             ' file')
        if self._switch.get_telnet_inbound_reason() == 'transfer_conf':
            unwritten.append('WARN: Inbound Telnet is ' + 'en' if
                             self._switch.get_telnet_inbound() else 'dis' +
                             'abled, but omitted from configuration file')
        if self._switch.get_telnet_outbound_reason() == 'transfer_conf':
            unwritten.append('WARN: Outbound Telnet is ' + 'en' if
                             self._switch.get_telnet_outbound() else 'dis' +
                             'abled, but omitted from configuration file')
        if self._switch.get_ssh_inbound_reason() == 'transfer_conf':
            unwritten.append('WARN: Inbound SSH is ' + 'en' if
                             self._switch.get_ssh_inbound() else 'dis' +
                             'abled, but omitted from configuration file')
        if self._switch.get_ssh_outbound_reason() == 'transfer_conf':
            unwritten.append('WARN: Outbound SSH is ' + 'en' if
                             self._switch.get_ssh_outbound() else 'dis' +
                             'abled, but omitted from configuration file')
        if self._switch.get_ssl_reason() == 'transfer_conf':
            unwritten.append('WARN: SSL is ' + 'en' if
                             self._switch.get_ssl() else 'dis' +
                             'abled, but omitted from configuration file')
        if self._switch.get_http_reason() == 'transfer_conf':
            unwritten.append('WARN: HTTP is ' + 'en' if
                             self._switch.get_http() else 'dis' +
                             'abled, but omitted from configuration file')
        if self._switch.get_http_secure_reason() == 'transfer_conf':
            unwritten.append('WARN: HTTPS is ' + 'en' if
                             self._switch.get_http_secure() else 'dis' +
                             'abled, but omitted from configuration file')
        if self._switch.get_mgmt_ip_reason() == 'transfer_conf':
            unwritten.append('WARN: Management IP address "' +
                             str(self._switch.get_mgmt_ip()) +
                             '" omitted from translation')
        if self._switch.get_mgmt_mask_reason() == 'transfer_conf':
            unwritten.append('WARN: Management Netmask "' +
                             str(self._switch.get_mgmt_mask()) +
                             '" omitted from translation')
        if self._switch.get_mgmt_vlan_reason() == 'transfer_conf':
            unwritten.append('WARN: Management VLAN "' +
                             str(self._switch.get_mgmt_vlan()) +
                             '" omitted from translation')
        if self._switch.get_mgmt_gw_reason() == 'transfer_conf':
            unwritten.append('WARN: Management gateway IP "' +
                             str(self._switch.get_mgmt_gw()) +
                             '" omitted from translation')
        if self._switch.get_mgmt_protocol_reason() == 'transfer_conf':
            unwritten.append('WARN: Management IP protocol "' +
                             str(self._switch.get_mgmt_protocol()) +
                             '" omitted from translation')
        if self._switch.get_idle_timer_reason() == 'transfer_conf':
            unwritten.append('WARN: Idle Timeout "' +
                             str(self._switch.get_idle_timer()) +
                             '" omitted from translation')
        for idx in self._switch.get_all_syslog_servers():
            if (self._switch._syslog_servers[idx].get_is_configured() and
                    not self._switch._syslog_servers[idx].get_is_written()):
                unwritten.append('WARN: syslog server ' + str(idx) +
                                 ' configured, but omitted from translation')
        for sntp_srv in self._switch.get_all_sntp_servers():
            if sntp_srv.get_is_configured() and not sntp_srv.get_is_written():
                unwritten.append('WARN: SNTP server ' + str(sntp_srv) +
                                 ' configured, but omitted from translation')
        for idx in self._switch.get_all_radius_servers():
            if (self._switch._radius_servers[idx].get_is_configured() and
                    not self._switch._radius_servers[idx].get_is_written()):
                unwritten.append('WARN: RADIUS server ' + str(idx) +
                                 ' configured, but omitted from translation')
        for idx in self._switch.get_all_tacacs_servers():
            if (self._switch._tacacs_servers[idx].get_is_configured() and
                    not self._switch._tacacs_servers[idx].get_is_written()):
                unwritten.append('WARN: TACACS+ server ' + str(idx) +
                                 ' configured, but omitted from translation')
        if self._switch.get_sntp_client_reason() == 'transfer_conf':
            unwritten.append('WARN: SNTP client mode "' +
                             str(self._switch.get_sntp_client()) +
                             '" omitted from translation')
        if self._switch.get_tz_name_reason() == 'transfer_conf':
            unwritten.append('WARN: Timezone name "' +
                             str(self._switch.get_tz_name()) +
                             '" omitted from translation')
        if self._switch.get_tz_off_min_reason() == 'transfer_conf':
            unwritten.append('WARN: Timezone offset "' +
                             str(self._switch.get_tz_off_min()) +
                             '" (minutes) omitted from translation')
        if self._switch.get_tz_dst_state_reason() == 'transfer_conf':
            unwritten.append('WARN: Timezone DST state "' +
                             str(self._switch.get_tz_dst_state()) +
                             '" omitted from translation')
        if self._switch.get_tz_dst_name_reason() == 'transfer_conf':
            unwritten.append('WARN: Timezone DST name "' +
                             str(self._switch.get_tz_dst_name()) +
                             '" omitted from translation')
        if self._switch.get_tz_dst_start_reason() == 'transfer_conf':
            unwritten.append('WARN: Timezone DST start "' +
                             str(self._switch.get_tz_dst_start()) +
                             '" omitted from translation')
        if self._switch.get_tz_dst_end_reason() == 'transfer_conf':
            unwritten.append('WARN: Timezone DST end "' +
                             str(self._switch.get_tz_dst_end()) +
                             '" omitted from translation')
        if self._switch.get_tz_dst_off_min_reason() == 'transfer_conf':
            unwritten.append('WARN: Timezone DST offset "' +
                             str(self._switch.get_tz_dst_off_min()) +
                             '" (minutes) omitted from translation')
        _tc = 'transfer_conf'
        if self._switch.get_radius_mgmt_acc_enabled_reason() == _tc:
            unwritten.append('WARN: RADIUS for management access "' +
                             str(self._switch.get_radius_mgmt_acc_enabled()) +
                             '" omitted from translation')
        if self._switch.get_radius_interface_reason() == 'transfer_conf':
            unwritten.append('WARN: RADIUS interface "' +
                             str(self._switch.get_radius_interface_type()) +
                             ' ' +
                             str(self._switch.get_radius_interface_number()) +
                             '" omitted from translation')
        if self._switch.get_tacacs_enabled_reason() == 'transfer_conf':
            unwritten.append('WARN: TACACS+ for management access "' +
                             str(self._switch.get_tacacs_enabled()) +
                             '" omitted from translation')
        if self._switch.get_tacacs_interface_reason() == 'transfer_conf':
            unwritten.append('WARN: TACACS+ interface "' +
                             str(self._switch.get_tacacs_interface_type()) +
                             ' ' +
                             str(self._switch.get_tacacs_interface_number()) +
                             '" omitted from translation')
        for name in self._switch.get_all_snmp_target_params():
            if (self._switch._snmp_target_params[name].is_configured() and not
                    self._switch._snmp_target_params[name].get_is_written()):
                unwritten.append('WARN: SNMP target parameters ' + str(name) +
                                 ' configured, but omitted from translation')
        for name in self._switch.get_all_snmp_target_addrs():
            if (self._switch._snmp_target_addrs[name].is_configured() and not
                    self._switch._snmp_target_addrs[name].get_is_written()):
                unwritten.append('WARN: SNMP target address ' + str(name) +
                                 ' configured, but omitted from translation')
        for name in self._switch.get_all_user_accounts():
            if (self._switch._user_accounts[name].is_configured() and not
                    self._switch._user_accounts[name].get_is_written()):
                unwritten.append('WARN: User account ' + str(name) +
                                 ' configured, but omitted from translation')
        # feature module Basic Layer 3
        if self._switch.get_ipv4_routing_reason() == 'transfer_conf':
            state = 'enabl' if self._switch.get_ipv4_routing() else 'disabl'
            unwritten.append('WARN: global IPv4 routing is ' + state +
                             'ed, but omitted from translation')
        return unwritten

    def port(self):
        return [], ['ERROR: Generic switch cannot generate port configuration']

    def vlan(self):
        return [], ['ERROR: Generic switch cannot generate VLAN configuration']

    def lag(self):
        return [], ['ERROR: Generic switch cannot generate LAG configuration']

    def stp(self):
        return [], ['ERROR: Generic switch cannot generate STP configuration']

    def acl(self):
        return [], ['ERROR: Generic switch cannot generate ACL configuration']

    def mgmt(self):
        return [], ['ERROR: Generic switch cannot generate management '
                    'configuration']

    def basic_layer_3(self):
        return [], ['ERROR: Generic switch cannot generate basic layer 3'
                    ' configuration']

    def generate(self):
        config = []
        errors = []
        for fm in self._feature_modules:
            fm_config, fm_errors = getattr(self, fm)()
            config.extend(fm_config)
            errors.extend(fm_errors)
        errors.extend(self.check_unwritten())
        return config, errors

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
