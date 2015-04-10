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

"""Definition of EOS switch attributes and models.

Classes:
EosSwitch defines attributes specific to Enterasys Operating System (EOS).
C5K125_48P2 defines attributes specific to a C5K125-48P2 switch.
C5K125_48 defines attributes specific to a C5K125-48 switch.
C5G124_24 defines attributes specific to a C5G124-24 switch.

Variables:
devices defines the switch models supported by this module.
"""

import re

import EOS_read
import LAG
import STP
import Switch
import Utils


class EosSwitch(Switch.Switch):

    """EOS specific attributes for a switch.

    Derived from the Switch class, the EosSwitch class describes a model for
    Enterasys OS based switches. Subclass EosSwitch to describe a specific
    switch model.

    Methods:
    apply_default_settings() applies EOS defaults to the switch.
    apply_default_lag_settings() applies EOS LAG defaults to the switch.
    normalize_config() converts EOS keywords to lower case.
    expand_macros() expands macro commands in the input configuration.
    """

    def __init__(self):
        super().__init__()
        self._model = 'generic'
        self._os = 'EOS'
        self._cmd = EOS_read.EosCommand(self)
        self._sep = '.'
        self._macros = self._register_macros()
        self._init_lags()

    def _init_lags(self, number=6):
        for i in range(1, number + 1):
            lag_name = 'lag.0.' + str(i)
            lag = LAG.LAG(number=i, name=lag_name, use_lacp=True)
            self._lags.append(lag)

    def _build_port_name(self, index, name_dict, slot):
        sep = self._sep
        name = name_dict['prefix'] + sep + str(slot) + sep + str(index)
        return name

    def apply_default_settings(self):
        """Apply EOS default settings."""
        reason = 'default'
        # physical ports
        for p in self._ports:
            self._apply_default_port_settings(p)
        # link aggregation groups
        for l in self._lags:
            self.apply_default_lag_settings(l)
        self._lacp_support = (True, reason)
        self._max_lag = (6, reason)
        self._single_port_lag = (False, reason)
        # VLANs
        self.get_vlan(tag=1).set_name('DEFAULT VLAN', True)
        # spanning tree
        stp = STP.STP()
        stp.enable(reason)
        stp.set_version('mstp', reason)
        stp.set_priority(32768, reason)
        stp.set_mst_rev(0, reason)
        stp.set_mst_instance(0, reason)
        stp.add_vlans(range(1, 4095), reason)
        self._stps.append(stp)
        for p in self._ports + self._lags:
            self._apply_default_common_port_settings(p)
        super().apply_default_settings()

    def _apply_default_port_settings(self, port):
        """Apply EOS default settings."""
        reason = 'default'
        port.set_speed(10, reason)
        port.set_duplex('half', reason)
        port.set_auto_neg(True, reason)
        port.set_admin_state(True, reason)
        port.set_jumbo(True, reason)
        port.set_lacp_enabled(False, reason)
        port.set_lacp_aadminkey(32768, reason)

    def apply_default_lag_settings(self, lag):
        """Apply EOS default settings."""
        reason = 'default'
        lag.set_admin_state(True, reason)
        lag.set_lacp_enabled(True, reason)
        lag.set_lacp_aadminkey(32768, reason)

    def _apply_default_common_port_settings(self, port):
        reason = 'default'
        port.set_stp_enabled(True, reason)
        port.set_stp_auto_edge(True, reason)
        port.set_stp_edge(False, reason)
        port.set_stp_bpdu_guard(False, reason)
        port.set_stp_bpdu_guard_recovery_time(300, reason)

    def _verify_port_string_syntax(self, portstring):
        """Verify that a given string is syntactically correct."""
        port_type = '[a-zA-Z]+(,[a-zA-Z]+)*'
        lst_el = '[0-9]+(-[0-9]+)?'
        lst = '{0}(,{0})*'.format(lst_el)
        port_str = '(\*|({0}))\.(\*|({1}))\.(\*|({1}))'.format(port_type, lst)
        port_str_lst = '{0}(;{0})*'.format(port_str)
        anchored_ps_regex = '^' + port_str_lst + '$'

        regex = re.compile(anchored_ps_regex)
        return True if regex.match(portstring) else False

    def _port_name_matches_description(self, name, description):
        """Match a port name against a port string."""
        sep = self._sep
        description = description.strip()
        if name == description:
            return True
        if not self._verify_port_string_syntax(description):
            return False
        ret = False
        # port strings can be concatenated using ;
        if ';' in description:
            port_string_list = description.split(';')
            for ps in port_string_list:
                ret = ret or self._port_name_matches_description(name, ps)
        # this port string is a 3-tuple
        else:
            (n_speed, n_slot, n_port) = name.split('.')
            (d_speed, d_slot, d_port) = description.split('.')
            speed_match = ((d_speed == '*') or
                           (n_speed in Utils.expand_sequence(d_speed)))
            slot_match = ((d_slot == '*') or
                          (n_slot in Utils.expand_sequence(d_slot)))
            port_match = ((d_port == '*') or
                          (n_port in Utils.expand_sequence(d_port)))
            ret = speed_match and slot_match and port_match
        return ret

    def normalize_config(self, config):
        """Convert keywords to lower case."""
        keywords = {'enable', 'disable', 'cfgname', 'rev', 'sid', 'mstp',
                    'rstp', 'stpcompatible', 'version', 'msti', 'mstmap',
                    'mstcfgid', 'priority', 'spanguard', 'autoedge',
                    'portadmin', 'adminedge', 'egress', 'create', 'name',
                    'lacp', 'port', 'alias', 'speed', 'duplex', 'negotiation',
                    'jumbo', 'vlan', 'aadminkey', 'static', 'singleportlag',
                    'access-group', 'access-list', 'spantree', 'set', 'clear',
                    'router', 'exit', 'configure', 'terminal', 'interface',
                    'ip', 'udp', 'tcp', 'icmp', 'address', 'sequence', 'any',
                    'host', 'permit', 'deny', 'in', 'out', 'key', 'prompt',
                    'system', 'contact', 'location', 'banner', 'ssh', 'telnet',
                    'webview', 'logout', 'logging', 'server', 'sntp', 'client',
                    'summertime', 'recurring', 'timezone', 'radius', 'realm',
                    'management-access', 'network-access', 'all', 'tacacs',
                    'snmp', 'targetaddr', 'login', 'shutdown', 'no',
                    'helper-address', 'routing', 'cdp', 'ciscodp', 'lldp',
                    'broadcast', 'ingress-filter', 'trap', 'mac', 'lock',
                    'igmp', 'ipv6', 'ipv6mode', 'inbound', 'outbound',
                    'loopback',
                    }
        comments = self.get_cmd().get_comment()
        return (Utils.words_to_lower(config, keywords, comments), [])

    def expand_macros(self, config):
        """Expand macro commands in the configuration to basic commands."""
        expanded_config, all_errors = [], []
        for l in config:
            expanded, errors = self._expand_line(l)
            expanded_config.extend(expanded)
            all_errors.extend(errors)
        return expanded_config, all_errors

    def _expand_line(self, line):
        for m in self._macros:
            if line.startswith(m):
                return getattr(self, self._macros[m])(line)
        return [line], []

    def _register_macros(self):
        """Dictionary of supported macro expansion methods."""
        return {'set lacp static': '_expand_set_lacp_static'}

    def _expand_set_lacp_static(self, line):
        """Expand 'set lacp static' macro command."""
        error = False
        cmd_lst = line.split()
        expanded_lst, error_lst = [], []
        error_lst.append('DEBUG: Macro expansion of: ' + line)
        portstring, key, lag_lst = None, -1, []
        if len(cmd_lst) < 4:
            # line: set lacp static
            error = True
            error_lst.append('ERROR: Incomplete "set lacp static" macro')
        else:
            # line: set lacp static LAG [...]
            lag = cmd_lst[3]
            lag_lst = lag.split('.')
            if (len(lag_lst) != 3 or lag_lst[0].lower() != 'lag' or
                    lag_lst[1] != '0' or lag_lst[2] == '*'):
                error = True
                error_lst.append('ERROR: Illegal LAG string "' + lag + '" in '
                                 '"set lacp static" macro')
            if not error:
                try:
                    key = int(lag_lst[2])
                except:
                    error = True
                    error_lst.append('ERROR: Illegal LAG number "' +
                                     lag_lst[2] + '" in "set lacp static"'
                                     ' macro')
        if error:
            pass
        elif len(cmd_lst) == 4:
            # line: set lacp static LAG
            pass
        elif len(cmd_lst) == 5:
            # line: set lacp static LAG PORTSTRING
            portstring = cmd_lst[4]
        elif len(cmd_lst) == 6 or len(cmd_lst) == 7:
            # line: set lacp static LAG key KEY [PORTSTRING]
            if cmd_lst[4].lower() == 'key':
                try:
                    key = int(cmd_lst[5])
                except:
                    error = True
                    error_lst.append('ERROR: LACP actor key must be an'
                                     ' integer')
                if len(cmd_lst) == 7:
                    portstring = cmd_lst[6]
            else:
                error = True
                error_lst.append('ERROR: Keyword "key" expected, got "' +
                                 cmd_lst[4] + '"')
        else:
            error = True
            error_lst.append('ERROR: Too many arguments to ' +
                             '"set lacp static" macro')
        if portstring and not self._verify_port_string_syntax(portstring):
            error = True
            error_lst.append('ERROR: Port string expected, but got "' +
                             portstring + '"')
        if error:
            # keep original line in configuration
            expanded_lst = [line]
            error_lst.append('ERROR: Could not expand "set lacp static" macro')
        else:
            expanded_lst.append('set lacp static ' + lag)
            expanded_lst.append('set lacp aadminkey ' + lag + ' ' + str(key))
            if portstring:
                expanded_lst.append('set port lacp port ' + portstring +
                                    ' aadminkey ' + str(key))
                expanded_lst.append('set port lacp port ' + portstring +
                                    ' disable')
            for line in expanded_lst:
                error_lst.append('DEBUG: Macro expansion to: ' + line)
        return expanded_lst, error_lst


# Dictionary of hardware descriptions
hardware_descriptions = {
    'C5K125-24': [
        '{"ports":{"label":{"start":1,"end":22},'
        '"name":{"prefix":"ge","start":1,"end":22},'
        '"data":{"type":"rj45","speedrange":[10,100,1000],"PoE":"no"}}}',
        '{"ports":{"label":{"start":23,"end":24},'
        '"name":{"prefix":"ge","start":23,"end":24},'
        '"data":{"type":"combo","speedrange":[10,100,1000],"PoE":"no"}}}',
        '{"ports":{"label":{"start":25,"end":26},'
        '"name":{"prefix":"tg","start":25,"end":26},'
        '"data":{"type":"sfp","speedrange":[1000,10000],"PoE":"no"}}}',
    ],
    'C5K125-24P2': [
        '{"ports":{"label":{"start":1,"end":22},'
        '"name":{"prefix":"ge","start":1,"end":22},'
        '"data":{"type":"rj45","speedrange":[10,100,1000],"PoE":"yes"}}}',
        '{"ports":{"label":{"start":23,"end":24},'
        '"name":{"prefix":"ge","start":23,"end":24},'
        '"data":{"type":"combo","speedrange":[10,100,1000],"PoE":"yes"}}}',
        '{"ports":{"label":{"start":25,"end":26},'
        '"name":{"prefix":"tg","start":25,"end":26},'
        '"data":{"type":"sfp","speedrange":[1000,10000],"PoE":"no"}}}',
    ],
    'C5K125-48P2': [
        '{"ports":{"label":{"start":1,"end":46},'
        '"name":{"prefix":"ge","start":1,"end":46},'
        '"data":{"type":"rj45","speedrange":[10,100,1000],"PoE":"yes"}}}',
        '{"ports":{"label":{"start":47,"end":48},'
        '"name":{"prefix":"ge","start":47,"end":48},'
        '"data":{"type":"combo","speedrange":[10,100,1000],"PoE":"yes"}}}',
        '{"ports":{"label":{"start":49,"end":50},'
        '"name":{"prefix":"tg","start":49,"end":50},'
        '"data":{"type":"sfp","speedrange":[1000,10000],"PoE":"no"}}}',
    ],
    'C5K125-48': [
        '{"ports":{"label":{"start":1,"end":46},'
        '"name":{"prefix":"ge","start":1,"end":46},'
        '"data":{"type":"rj45","speedrange":[10,100,1000],"PoE":"no"}}}',
        '{"ports":{"label":{"start":47,"end":48},'
        '"name":{"prefix":"ge","start":47,"end":48},'
        '"data":{"type":"combo","speedrange":[10,100,1000],"PoE":"no"}}}',
        '{"ports":{"label":{"start":49,"end":50},'
        '"name":{"prefix":"tg","start":49,"end":50},'
        '"data":{"type":"sfp","speedrange":[1000,10000],"PoE":"no"}}}',
    ],
    'C5G124-24': [
        '{"ports":{"label":{"start":1,"end":20},'
        '"name":{"prefix":"ge","start":1,"end":20},'
        '"data":{"type":"rj45","speedrange":[10,100,1000],"PoE":"no"}}}',
        '{"ports":{"label":{"start":21,"end":24},'
        '"name":{"prefix":"ge","start":21,"end":24},'
        '"data":{"type":"combo","speedrange":[10,100,1000],"PoE":"no"}}}',
    ],
    'C5G124-24P2': [
        '{"ports":{"label":{"start":1,"end":20},'
        '"name":{"prefix":"ge","start":1,"end":20},'
        '"data":{"type":"rj45","speedrange":[10,100,1000],"PoE":"yes"}}}',
        '{"ports":{"label":{"start":21,"end":24},'
        '"name":{"prefix":"ge","start":21,"end":24},'
        '"data":{"type":"combo","speedrange":[10,100,1000],"PoE":"yes"}}}',
    ],
    'C5G124-48': [
        '{"ports":{"label":{"start":1,"end":44},'
        '"name":{"prefix":"ge","start":1,"end":44},'
        '"data":{"type":"rj45","speedrange":[10,100,1000],"PoE":"no"}}}',
        '{"ports":{"label":{"start":45,"end":48},'
        '"name":{"prefix":"ge","start":45,"end":48},'
        '"data":{"type":"combo","speedrange":[10,100,1000],"PoE":"no"}}}',
    ],
    'C5G124-48P2': [
        '{"ports":{"label":{"start":1,"end":44},'
        '"name":{"prefix":"ge","start":1,"end":44},'
        '"data":{"type":"rj45","speedrange":[10,100,1000],"PoE":"yes"}}}',
        '{"ports":{"label":{"start":45,"end":48},'
        '"name":{"prefix":"ge","start":45,"end":48},'
        '"data":{"type":"combo","speedrange":[10,100,1000],"PoE":"yes"}}}',
    ],
    'C5K175-24': [
        '{"ports":{"label":{"start":1,"end":24},'
        '"name":{"prefix":"ge","start":1,"end":24},'
        '"data":{"type":"sfp","speedrange":[1000],"PoE":"no"}}}',
        '{"ports":{"label":{"start":25,"end":26},'
        '"name":{"prefix":"tg","start":25,"end":26},'
        '"data":{"type":"sfp","speedrange":[1000,10000],"PoE":"no"}}}',
    ],
}


class EosSwitchHardware(EosSwitch):

    def __init__(self, model):
        super().__init__()
        self._model = model
        self._hw_desc = []
        if ',' in model:
            self._stack = True
        switches = self._model.split(',')
        for s in switches:
            if not s:
                continue
            self._hw_desc.append(hardware_descriptions[s])
        self._setup_hw()

# Dictionary of supported switch models used to register devices in the CM
devices = {
    'C5G124-24': {'use_as': 'source', 'os': 'EOS'},
    'C5G124-24P2': {'use_as': 'source', 'os': 'EOS'},
    'C5G124-48': {'use_as': 'source', 'os': 'EOS'},
    'C5G124-48P2': {'use_as': 'source', 'os': 'EOS'},
    'C5K125-24': {'use_as': 'source', 'os': 'EOS'},
    'C5K125-24P2': {'use_as': 'source', 'os': 'EOS'},
    'C5K125-48': {'use_as': 'source', 'os': 'EOS'},
    'C5K125-48P2': {'use_as': 'source', 'os': 'EOS'},
    'C5K175-24': {'use_as': 'source', 'os': 'EOS'},
    }

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4