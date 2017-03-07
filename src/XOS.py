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

"""Definition of XOS switch attributes and models.

Classes:
XosSwitch defines attributes specific to ExtremeXOS Network Operating
System (XOS).
SummitX460_48p defines attributes specific to a Summit X460-48p switch.
SummitX460_48p_2xf defines attributes specific to a Summit X460-48p switch with
an XGM3S-2XF module.
SummitX460_48p_2sf defines attributes specific to a Summit X460-48p switch with
an XGM3S-2SF module.
SummitX460_48p_4sf defines attributes specific to a Summit X460-48p switch with
an XGM3S-4SF module.
SummitX460_48p_2sf_4sf defines attributes specific to a Summit X460-48p switch
with both XGM3S-2SF and XGM3S-4SF modules.
SummitX460_24t defines attributes specific to a Summit X460-24t switch.

Variables:
devices defines the switch models supported by this module.
"""

import json

import STP
import Switch
import SyslogServer
import VLAN
import XOS_read
import XOS_write


class XosSwitch(Switch.Switch):

    """XOS specific attributes for a switch.

    Derived from the Switch class, the XosSwitch class describes a model for
    ExtremeXOS Network Operating System based switches. Subclass XosSwitch to
    describe a specific switch model.

    Methods:
    apply_default_settings() applies XOS defaults to the switch.
    apply_default_lag_settings() applies XOS LAG defaults to the switch.
    """

    def __init__(self):
        super().__init__()
        self._model = 'generic'
        self._os = 'XOS'
        self._cmd = XOS_read.XosCommand(self)
        self._writer = XOS_write.XosConfigWriter(self)
        self._sep = ':'
        self.add_vlan(VLAN.VLAN(name='Mgmt', switch=self))

    def _build_port_name(self, index, name_dict, slot):
        if self.is_stack():
            name = str(slot) + self._sep + str(index)
        else:
            name = str(index)
        return name

    def apply_default_settings(self):
        """Apply XOS default settings."""
        reason = 'default'
        for p in self._ports:
            self._apply_default_port_settings(p)
        self.get_vlan(tag=1).set_name('Default', True)
        self._single_port_lag = (True, reason)
        stp = STP.STP()
        stp.disable(reason)
        stp.set_name('s0', reason)
        stp.set_version('stp', reason)
        stp.set_priority(32768, reason)
        stp.set_mst_rev(3, reason)
        stp.add_vlan(1, reason)
        self._stps.append(stp)
        self._telnet_inbound = (True, reason)
        self._telnet_outbound = (True, reason)
        self._ssh_inbound = (False, reason)
        self._ssl = (False, reason)
        self._http = (True, reason)
        self._http_secure = (False, reason)
        self._mgmt_vlan = ('Mgmt', reason)
        self._mgmt_protocol = ('none', reason)
        self._idle_timer = (20, reason)
        self._sntp_client = ('disable', reason)
        self._ipv4_routing = (False, reason)
        self._tz_dst_start = (('second', 'sunday', 'march', '2', '00'), reason)
        self._tz_dst_end = (('first', 'sunday', 'november', '2', '00'), reason)
        self._tz_dst_off_min = (60, reason)
        self._radius_mgmt_acc_enabled = (False, reason)
        self._tacacs_enabled = (False, reason)
        admin = self.get_user_account('admin')
        admin.set_is_default(True)
        admin.set_name('admin')
        admin.set_type('super-user')
        admin.set_state('enabled')
        user = self.get_user_account('user')
        user.set_is_default(True)
        user.set_name('user')
        user.set_type('read-only')
        user.set_state('enabled')
        super().apply_default_settings()

    def _apply_default_port_settings(self, port):
        """Apply XOS default port settings."""
        reason = 'default'
        port.set_auto_neg(True, reason)
        port.set_admin_state(True, reason)
        port.set_jumbo(False, reason)
        port.set_lacp_enabled(False, reason)
        port.set_stp_edge(False, reason)
        port.set_stp_bpdu_guard(False, reason)
        port.set_stp_bpdu_guard_recovery_time(300, reason)

    def apply_default_lag_settings(self, lag):
        """Apply XOS default LAG settings (same as port)."""
        self._apply_default_port_settings(lag)

    def create_lag_name(self, lag_number, lag_ports):
        """Build the name of a LAG (master port)."""
        if lag_ports:
            return lag_ports[0]
        else:
            return ''

    def _create_syslog_server(self):
        ret = SyslogServer.SyslogServer()
        defaults = {
            'def_port': '514',
            'def_state': 'disable',
            'def_severity': 'debug-data',
        }
        ret.update_attributes(defaults)
        return ret


# Dictionary of hardware descriptions
hardware_descriptions = {
    'SummitX460-48p': [
        '{"ports": {"label": {"start": 1, "end": 48},'
        '            "name": {"prefix": "", "start": 1, "end": 48},'
        '            "data": {"type": "rj45",'
        '                     "speedrange": [10, 100, 1000],'
        '                     "PoE": "yes"}}}',
        '{"ports": {"label": {"start": 49, "end": 52},'
        '            "name": {"prefix": "", "start": 49, "end": 52},'
        '            "data": {"type": "sfp",'
        '                     "speedrange": [100, 1000],'
        '                     "PoE": "no"}}}',
    ],
    'SummitX460-48t': [
        '{"ports": {"label": {"start": 1, "end": 48},'
        '            "name": {"prefix": "", "start": 1, "end": 48},'
        '            "data": {"type": "rj45",'
        '                     "speedrange": [10, 100, 1000],'
        '                     "PoE": "no"}}}',
        '{"ports": {"label": {"start": 49, "end": 52},'
        '            "name": {"prefix": "", "start": 49, "end": 52},'
        '            "data": {"type": "sfp",'
        '                     "speedrange": [100, 1000],'
        '                     "PoE": "no"}}}',
    ],
    'SummitX460-48x': [
        '{"ports": {"label": {"start": 1, "end": 48},'
        '            "name": {"prefix": "", "start": 1, "end": 48},'
        '            "data": {"type": "sfp",'
        '                     "speedrange": [100, 1000],'
        '                     "PoE": "no"}}}',
    ],
    'SummitX460-24t': [
        '{"ports": {"label": {"start": 1, "end": 20},'
        '            "name": {"prefix": "", "start": 1, "end": 20},'
        '            "data": {"type": "rj45",'
        '                     "speedrange": [10, 100, 1000],'
        '                     "PoE": "no"}}}',
        '{"ports": {"label": {"start": 21, "end": 24},'
        '            "name": {"prefix": "", "start": 21, "end": 24},'
        '            "data": {"type": "combo",'
        '                     "speedrange": [10, 100, 1000],'
        '                     "PoE": "no"}}}',
        '{"ports": {"label": {"start": 25, "end": 28},'
        '            "name": {"prefix": "", "start": 25, "end": 28},'
        '            "data": {"type": "sfp",'
        '                     "speedrange": [100, 1000],'
        '                     "PoE": "no"}}}',
    ],
    'SummitX460-24p': [
        '{"ports": {"label": {"start": 1, "end": 20},'
        '            "name": {"prefix": "", "start": 1, "end": 20},'
        '            "data": {"type": "rj45",'
        '                     "speedrange": [10, 100, 1000],'
        '                     "PoE": "yes"}}}',
        '{"ports": {"label": {"start": 21, "end": 24},'
        '            "name": {"prefix": "", "start": 21, "end": 24},'
        '            "data": {"type": "combo",'
        '                     "speedrange": [10, 100, 1000],'
        '                     "PoE": "yes"}}}',
        '{"ports": {"label": {"start": 25, "end": 28},'
        '            "name": {"prefix": "", "start": 25, "end": 28},'
        '            "data": {"type": "sfp",'
        '                     "speedrange": [100, 1000],'
        '                     "PoE": "no"}}}',
    ],
    'SummitX460-24x': [
        '{"ports": {"label": {"start": 1, "end": 20},'
        '            "name": {"prefix": "", "start": 1, "end": 20},'
        '            "data": {"type": "sfp",'
        '                     "speedrange": [100, 1000],'
        '                     "PoE": "no"}}}',
        '{"ports": {"label": {"start": 21, "end": 24},'
        '            "name": {"prefix": "", "start": 21, "end": 24},'
        '            "data": {"type": "combo",'
        '                     "speedrange": [10, 100, 1000],'
        '                     "PoE": "no"}}}',
        '{"ports": {"label": {"start": 25, "end": 28},'
        '            "name": {"prefix": "", "start": 25, "end": 28},'
        '            "data": {"type": "rj45",'
        '                     "speedrange": [10, 100, 1000],'
        '                     "PoE": "no"}}}',
    ],
    '2xf': [
        '{"ports": {"label": {"start": 1, "end": 2},'
        '            "name": {"prefix": "", "start": 1, "end": 2},'
        '            "data": {"type": "sfp",'
        '                     "speedrange": [10000],'
        '                     "PoE": "no"}}}',
    ],
    '2sf': [
        '{"ports": {"label": {"start": 1, "end": 2},'
        '            "name": {"prefix": "", "start": 1, "end": 2},'
        '            "data": {"type": "sfp",'
        '                     "speedrange": [1000, 10000],'
        '                     "PoE": "no"}}}',
    ],
    '4sf': [
        '{"ports": {"label": {"start": 1, "end": 4},'
        '            "name": {"prefix": "", "start": 1, "end": 4},'
        '            "data": {"type": "sfp",'
        '                     "speedrange": [1000, 10000],'
        '                     "PoE": "no"}}}',
    ],
}


class XosSwitchHardware(XosSwitch):

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
            sw_hw = []
            last_port = 0
            for part in s.split('+'):
                hw_desc = hardware_descriptions[part]
                if sw_hw:
                    highest_ports = json.loads(sw_hw[-1])
                    highest_port = max(
                        [json.loads(port_desc)['ports']['name']['end']
                         for port_desc in sw_hw])
                    last_port = highest_ports['ports']['name']['end']
                    last_port = highest_port
                if part in {'2xf', '2sf', '4sf', }:
                    offset = 2 if (part == '4sf' and ('2xf' not in s and
                                   '2sf' not in s)) else 0
                    # module must have exactly one port list entry
                    mod_ports = json.loads(hw_desc[0])
                    mod_ports['ports']['name']['start'] += last_port + offset
                    mod_ports['ports']['name']['end'] += last_port + offset
                    hw_desc = [json.dumps(mod_ports)]
                sw_hw += hw_desc
            self._hw_desc.append(sw_hw)
        self._setup_hw()

devices = {
    'SummitX460-48t': {'use_as': 'target', 'os': 'XOS'},
    'SummitX460-48t+2xf': {'use_as': 'target', 'os': 'XOS'},
    'SummitX460-48t+2sf': {'use_as': 'target', 'os': 'XOS'},
    'SummitX460-48t+4sf': {'use_as': 'target', 'os': 'XOS'},
    'SummitX460-48t+2xf+4sf': {'use_as': 'target', 'os': 'XOS'},
    'SummitX460-48t+2sf+4sf': {'use_as': 'target', 'os': 'XOS'},
    'SummitX460-48p': {'use_as': 'target', 'os': 'XOS'},
    'SummitX460-48p+2xf': {'use_as': 'target', 'os': 'XOS'},
    'SummitX460-48p+2sf': {'use_as': 'target', 'os': 'XOS'},
    'SummitX460-48p+4sf': {'use_as': 'target', 'os': 'XOS'},
    'SummitX460-48p+2xf+4sf': {'use_as': 'target', 'os': 'XOS'},
    'SummitX460-48p+2sf+4sf': {'use_as': 'target', 'os': 'XOS'},
    'SummitX460-24t': {'use_as': 'target', 'os': 'XOS'},
    'SummitX460-24t+2xf': {'use_as': 'target', 'os': 'XOS'},
    'SummitX460-24t+2sf': {'use_as': 'target', 'os': 'XOS'},
    'SummitX460-24t+4sf': {'use_as': 'target', 'os': 'XOS'},
    'SummitX460-24t+2xf+4sf': {'use_as': 'target', 'os': 'XOS'},
    'SummitX460-24t+2sf+4sf': {'use_as': 'target', 'os': 'XOS'},
    'SummitX460-24p': {'use_as': 'target', 'os': 'XOS'},
    'SummitX460-24p+2xf': {'use_as': 'target', 'os': 'XOS'},
    'SummitX460-24p+2sf': {'use_as': 'target', 'os': 'XOS'},
    'SummitX460-24p+4sf': {'use_as': 'target', 'os': 'XOS'},
    'SummitX460-24p+2xf+4sf': {'use_as': 'target', 'os': 'XOS'},
    'SummitX460-24p+2sf+4sf': {'use_as': 'target', 'os': 'XOS'},
    'SummitX460-24x': {'use_as': 'target', 'os': 'XOS'},
    'SummitX460-24x+2xf': {'use_as': 'target', 'os': 'XOS'},
    'SummitX460-24x+2sf': {'use_as': 'target', 'os': 'XOS'},
    'SummitX460-24x+4sf': {'use_as': 'target', 'os': 'XOS'},
    'SummitX460-24x+2xf+4sf': {'use_as': 'target', 'os': 'XOS'},
    'SummitX460-24x+2sf+4sf': {'use_as': 'target', 'os': 'XOS'},
    'SummitX460-48x': {'use_as': 'target', 'os': 'XOS'},
    'SummitX460-48x+2xf': {'use_as': 'target', 'os': 'XOS'},
    'SummitX460-48x+2sf': {'use_as': 'target', 'os': 'XOS'},
    'SummitX460-48x+4sf': {'use_as': 'target', 'os': 'XOS'},
    'SummitX460-48x+2xf+4sf': {'use_as': 'target', 'os': 'XOS'},
    'SummitX460-48x+2sf+4sf': {'use_as': 'target', 'os': 'XOS'},
    }

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
