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

# Copyright 2014 Extreme Networks, Inc.  All rights reserved.
# Use is subject to license terms.

# This file is part of e2x (translate EOS switch configuration to ExtremeXOS)

"""Definition of EXOS switch attributes and models.

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

import STP
import Switch
import XOS_read
import XOS_write


class XosSwitch(Switch.Switch):

    """EXOS specific attributes for a swicht.

    Derived from the Switch class, the XosSwitch class describes a model for
    ExtremeXOS Network Operating System based switches. Subclass XosSwitch to
    describe a specific switch model.

    Methods:
    apply_default_settings() applies EXOS defaults to the switch.
    apply_default_lag_settings() applies EXOS LAG defaults to the switch.
    """

    def __init__(self):
        super().__init__()
        self._model = 'generic'
        self._os = 'XOS'
        self._cmd = XOS_read.XosCommand(self)
        self._writer = XOS_write.XosConfigWriter(self)
        self._sep = ':'

    def _build_port_name(self, index, name_dict):
        if self.is_stack_member():
            name = str(self._slot) + self._sep + str(index)
        else:
            name = str(index)
        return name

    def apply_default_settings(self):
        """Apply EXOS default settings."""
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
        super().apply_default_settings()

    def _apply_default_port_settings(self, port):
        """Apply EXOS default port settings."""
        reason = 'default'
        port.set_auto_neg(True, reason)
        port.set_admin_state(True, reason)
        port.set_jumbo(False, reason)
        port.set_lacp_enabled(False, reason)
        port.set_stp_edge(False, reason)
        port.set_stp_bpdu_guard(False, reason)
        port.set_stp_bpdu_guard_recovery_time(300, reason)

    def apply_default_lag_settings(self, lag):
        """Apply EXOS default LAG settings (same as port)."""
        self._apply_default_port_settings(lag)

    def create_lag_name(self, lag_number, lag_ports):
        """Build the name of a LAG (master port)."""
        if lag_ports:
            return lag_ports[0]
        else:
            return ''


class SummitX460_48p(XosSwitch):

    """Summit X460-48p switch definition."""

    def __init__(self):
        super().__init__()
        self._model = 'SummitX460-48p'
        self._hw_desc = [
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
        ]
        self.setup_hw()


class SummitX460_48p_2xf(SummitX460_48p):

    """Summit X460-48p switch with XGM3S-2XF module definition."""

    def __init__(self):
        super().__init__()
        self._model = 'SummitX460-48p+2xf'
        self._hw_desc.append(
            '{"ports": {"label": {"start": 53, "end": 54},'
            '            "name": {"prefix": "", "start": 53, "end": 54},'
            '            "data": {"type": "sfp",'
            '                     "speedrange": [1000, 10000],'
            '                     "PoE": "no"}}}',
        )
        self.setup_hw()


class SummitX460_48p_2sf(SummitX460_48p_2xf):

    """Summit X460-48p switch with XGM3S-2SF module definition."""

    def __init__(self):
        super().__init__()
        self._model = 'SummitX460-48p+2sf'


class SummitX460_48p_4sf(SummitX460_48p):

    """Summit X460-48p switch with XGM3S-4SF module definition."""

    def __init__(self):
        super().__init__()
        self._model = 'SummitX460-48p+4sf'
        self._hw_desc.append(
            '{"ports": {"label": {"start": 55, "end": 58},'
            '            "name": {"prefix": "", "start": 55, "end": 58},'
            '            "data": {"type": "sfp",'
            '                     "speedrange": [1000, 10000],'
            '                     "PoE": "no"}}}',
        )
        self.setup_hw()


class SummitX460_48p_2sf_4sf(SummitX460_48p_2sf):

    """Summit X460-48p switch with XGM3S-2SF and XGM3S-4SF definition."""

    def __init__(self):
        super().__init__()
        self._model = 'SummitX460-48p+2sf+4sf'
        self._hw_desc.append(
            '{"ports": {"label": {"start": 55, "end": 58},'
            '            "name": {"prefix": "", "start": 55, "end": 58},'
            '            "data": {"type": "sfp",'
            '                     "speedrange": [1000, 10000],'
            '                     "PoE": "no"}}}',
        )
        self.setup_hw()


class SummitX460_24t(XosSwitch):

    """Summit X460-24t switch definition."""

    def __init__(self):
        super().__init__()
        self._model = 'SummitX460-24t'
        self._hw_desc = [
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
        ]
        self.setup_hw()

devices = {
    'SummitX460-48p': {'use_as': 'target', 'os': 'XOS',
                       'class': SummitX460_48p},
    'SummitX460-48p+2xf': {'use_as': 'target', 'os': 'XOS',
                           'class': SummitX460_48p_2xf},
    'SummitX460-48p+2sf': {'use_as': 'target', 'os': 'XOS',
                           'class': SummitX460_48p_2sf},
    'SummitX460-48p+4sf': {'use_as': 'target', 'os': 'XOS',
                           'class': SummitX460_48p_4sf},
    'SummitX460-48p+2sf+4sf': {'use_as': 'target', 'os': 'XOS',
                               'class': SummitX460_48p_2sf_4sf},
    'SummitX460-24t': {'use_as': 'target', 'os': 'XOS',
                       'class': SummitX460_24t},
    }

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
