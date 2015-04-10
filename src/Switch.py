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
import json

import ACL
import Port
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
        self._lags = []
        self._stps = []
        self._acls = []
        self._init_configurable_attributes()

    def _init_configurable_attributes(self):
        self._lacp_support = (None, None)
        self._max_lag = (None, None)
        self._single_port_lag = (None, None)
        self._applied_defaults = False

    def __str__(self):
        description = ' Model: ' + str(self._model) + '\n'
        if self._stack:
            description += '  [This switch is a stack.]\n'
        description += ' OS:    ' + str(self._os) + '\n'
        description += ' Ports:'
        for p in self._ports:
            description += ' (' + str(p) + ')'
        description += '\n'
        description += ' VLANs:'
        for v in self._vlans:
            description += ' (' + str(v) + ')'
        description += '\n'
        description += ' LAGs:'
        for l in self._lags:
            description += ' (' + str(l) + ')'
        description += '\n'
        description += ' Global LACP: ' + str(self._lacp_support) + '\n'
        description += ' Max. LAGs: ' + str(self._max_lag) + '\n'
        description += ' Single Port LAG: ' + str(self._single_port_lag)
        description += '\n'
        description += ' Spanning Tree:'
        for s in self._stps:
            description += ' (' + str(s) + ')'
        description += '\n'
        description += ' ACLs:'
        for a in self._acls:
            description += ' (' + str(a) + ')'
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

    def create_config(self):
        return self._writer.generate()

    def get_cmd(self):
        return self._cmd

    def get_vlan(self, name=None, tag=None):
        if name is None and tag is None:
            return None
        elif name is None:
            pred = lambda v, n, t: v.get_tag() == t
        elif tag is None:
            pred = lambda v, n, t: v.get_name() == n
        else:
            pred = lambda v, n, t: v.get_name() == n and v.get_tag() == t
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
            lag_name = lag.get_name()
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


class ConfigWriter:

    """Interface definition of a configuration writer.

    This is used to register feature modules and to check for configuration
    parts that are not considered by the used subclass of ConfigWriter.

    Actual generation of configuration commands is implemented using
    subclasses.
    """

    def __init__(self, switch):
        self._feature_modules = ['port', 'lag', 'vlan', 'stp', 'acl']
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
