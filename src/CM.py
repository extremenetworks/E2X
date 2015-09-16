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

"""Core Module of E2X.

The Core Module (CM) of E2X provides the translation interface to front ends,
e.g. the command line front end implemented by cli.py.

The class CoreModule provides the translation interface.
"""

import traceback

import ACL
import LAG
import STP
import VLAN

# import switch definitions
import EOS
import XOS

_devices = {}


def _register_devices(devices):
    """Register available device types in the Core Module."""
    for dev in devices:
        _devices[dev] = devices[dev]

# register network devices by OS (one module per operating system)
_register_devices(EOS.devices)
_register_devices(XOS.devices)


class CoreModule:

    """Core module providing the translation interface.

    Methods:
    enable_debug() enables generation of debugging information.
    disable_defaults() prevents setting of device specific default values.
    enable_defaults() enables setting of device specific default values.
    enable_copy_unknown() enables copying unknown input lines to the output.
    enable_comment_unknown() outputs unknown lines as comments, not verbatim.
    disable_unused_ports() generates configuration to disable unmapped ports.
    use_oob_mgmt() specifies if an OOB management port is used or not.
    get_source_switches() returns a list of supported source switches.
    get_target_switches() returns a list of supported target switches.
    set_source_switch(model) sets the source switch used for translation.
    set_target_switch(model) sets the target switch used for translation.
    transfer_config() transfers the configuration from source to target.
    translate(config) translates config from source to target switches.
    """

    def __init__(self):
        self._debug = False
        self._apply_defaults = True
        self._copy_unknown = False
        self._comment_unknown = False
        self._disable_unused_ports = False
        self._use_oob_mgmt = False
        # retrieve list of supported source switches
        self._source_switches = []
        for dev in _devices:
            if (_devices[dev]['use_as'] == 'source' or
                    _devices[dev]['use_as'] == 'both'):
                self._source_switches.append(dev)
        # retrieve list of supported target switches
        self._target_switches = []
        for dev in _devices:
            if (_devices[dev]['use_as'] == 'target' or
                    _devices[dev]['use_as'] == 'both'):
                self._target_switches.append(dev)
        self.source = None
        self.target = None
        self._port_mapping_s2t = None
        self._port_mapping_t2s = None
        self._lag_mapping_s2t = None
        self._lag_mapping_t2s = None

    def enable_debug(self):
        self._debug = True

    def disable_defaults(self):
        self._apply_defaults = False

    def enable_defaults(self):
        self._apply_defaults = True

    def enable_copy_unknown(self):
        self._copy_unknown = True

    def enable_comment_unknown(self):
        self._comment_unknown = True

    def disable_unused_ports(self):
        self._disable_unused_ports = True

    def use_oob_mgmt(self, state):
        self._use_oob_mgmt = state

    def get_source_switches(self):
        return self._source_switches

    def get_target_switches(self):
        return self._target_switches

    def _check_stack_desc(self, desc, stack_use):
        stack_os = None
        for stack_member in desc.split(','):
            if not stack_member:
                continue
            sw = stack_member.strip()
            try:
                sw_os = _devices[sw]['os']
                sw_use = _devices[sw]['use_as']
            except:
                error = 'ERROR: Unknown switch name "' + sw + '"'
                if self._debug:
                    error += '\n' + traceback.format_exc()
                return False, '', error
            if stack_os is None:
                stack_os = sw_os
            elif stack_os != sw_os:
                error = 'ERROR: All switches in a stack must use same OS'
                return False, '', error
            if stack_use != sw_use and sw_use != 'both':
                error = ('ERROR: "' + sw + '" not supported as "' +
                         stack_use + '" switch')
                return False, '', error
        return True, stack_os, ''

    def _set_switch(self, model, use_as):
        model_ok, os, errors = self._check_stack_desc(model, use_as)
        if not model_ok:
            return None, errors
        if os == 'EOS':
            return EOS.EosSwitchHardware(model), ''
        elif os == 'XOS':
            return XOS.XosSwitchHardware(model), ''
        return None, 'ERROR: Cannot determine ' + use_as + ' stack OS'

    def set_source_switch(self, model):
        self.source, errors = self._set_switch(model, 'source')
        return bool(self.source), errors

    def set_target_switch(self, model):
        self.target, errors = self._set_switch(model, 'target')
        return bool(self.target), errors

    def _check_mapping_consistency(self, name, s2t, t2s):
        ret, err = True, []
        for key in s2t:
            s_name, t_name = key, s2t[key]
            if self._debug:
                err.append('DEBUG: mapping ' + name + ' ' + s_name + ' <-> ' +
                           t_name)
            t2s_key = s2t[key]
            if t2s_key not in t2s or t2s[s2t[key]] != key:
                err.append('ERROR: ' + name + ' mapping is not reflexive')
                ret = False
            if len(self.source.get_ports_by_name(s_name)) > 1:
                err.append('DEBUG: ' + name + ' name "' + s_name +
                           '" not unique')
            if len(self.target.get_ports_by_name(t_name)) > 1:
                err.append('DEBUG: ' + name + ' name "' + t_name +
                           '" not unique')
        return ret, err

    def _create_port_mapping(self):
        """Build a mapping of source switch port names to target port names."""
        err = []
        ret = True

        self._port_mapping_s2t = {}
        self._port_mapping_t2s = {}
        tmp_target_port_list = list(self.target.get_ports())
        for sp in self.source.get_ports():
            candidate = None
            candidate_nr = None
            for i in range(len(tmp_target_port_list)):
                tmp_p = tmp_target_port_list[i]
                if tmp_p.is_equivalent(sp):
                    if candidate is None:
                        candidate, candidate_nr = tmp_p, i
                    if candidate.get_label() == sp.get_label():
                        break
                    if tmp_p.get_label() == sp.get_label():
                        candidate, candidate_nr = tmp_p, i
            if candidate:
                self._port_mapping_s2t[sp.get_name()] = candidate.get_name()
                self._port_mapping_t2s[candidate.get_name()] = sp.get_name()
                msg = ('Mapping port "' + sp.get_name() + '" to port "' +
                       candidate.get_name() + '"')
                if candidate.get_label() != sp.get_label():
                    err.append('NOTICE: ' + msg)
                else:
                    err.append('INFO: ' + msg)
                tmp_target_port_list.pop(candidate_nr)
            else:
                err.append('WARN: Could not map port %s' % (sp.get_name()))
        ret, errors = self._check_mapping_consistency('Port',
                                                      self._port_mapping_s2t,
                                                      self._port_mapping_t2s)
        err.extend(errors)
        for tp in self.target.get_ports():
            if tp.get_name() not in self._port_mapping_t2s:
                err.append('NOTICE: Port "' + tp.get_name() +
                           '" of target switch is not used')
                if self._disable_unused_ports:
                    tp.set_admin_state(False, 'transfer_option')
        return ret, err

    def _create_lag_mapping(self):
        """Build a mapping of source switch LAG names to target LAG names."""
        ret, err = True, []
        self._lag_mapping_s2t, self._lag_mapping_t2s = {}, {}
        for sl in self.source.get_lags():
            sln = sl.get_name()
            pred_conf = sl.is_configured()
            pred_ndv = self.source.is_port_in_non_default_vlan(sln)
            pred_dis = sl.is_disabled_only()
            pred_acc = sl.accidental_config_only()
            if (not (pred_conf or pred_ndv) or
                    (pred_conf and (pred_dis or pred_acc))):
                continue
            for tl in self.target.get_lags():
                if not tl.get_name() in self._lag_mapping_t2s:
                    self._lag_mapping_s2t[sl.get_name()] = tl.get_name()
                    self._lag_mapping_t2s[tl.get_name()] = sl.get_name()
                    break
            if not sl.get_name() in self._lag_mapping_s2t:
                if (self.target.get_max_lag() is None or
                   len(self.target.get_lags()) < self.target.get_max_lag()):
                    new_lag_ports = [self._port_mapping_s2t[p.get_name()]
                                     for p in self.source.get_ports()
                                     if ((p.get_lacp_aadminkey() ==
                                          sl.get_lacp_aadminkey()) and
                                         (p.get_lacp_enabled() ==
                                          sl.get_lacp_enabled()))]
                    new_lag_name = self.target.create_lag_name(sl.get_label(),
                                                               new_lag_ports)
                    if not new_lag_name:
                        err.append('WARN: LAG "' + sl.get_name() + '" '
                                   'cannot be mapped to target switch')
                    else:
                        param = [sl.get_label(), new_lag_name,
                                 sl.get_lacp_enabled(),
                                 sl.get_lacp_aadminkey()]
                        new_lag = LAG.LAG(*param)
                        if self._apply_defaults:
                            self.target.apply_default_lag_settings(new_lag)
                        new_lag.transfer_config(sl)
                        error = self.target.add_lag(new_lag)
                        if error:
                            err.append(error)
                        else:
                            self._lag_mapping_s2t[sl.get_name()] = \
                                new_lag.get_name()
                            self._lag_mapping_t2s[new_lag.get_name()] = \
                                sl.get_name()
        ret, errors = self._check_mapping_consistency('LAG',
                                                      self._lag_mapping_s2t,
                                                      self._lag_mapping_t2s)
        err.extend(errors)
        return ret, err

    def transfer_config(self):
        """Transfer the current source switch configuration to the target."""
        ret = []

        # port configuration
        for sp in self.source.get_ports():
            tp_name = self._port_mapping_s2t.get(sp.get_name())
            if tp_name:
                tp = self.target.get_physical_ports_by_name(tp_name)[0]
                tp.transfer_config(sp)
            else:
                ret.append('INFO: Port "' + sp.get_name() + '" not mapped to'
                           ' target switch, no config transferred')
                if sp.is_configured():
                    ret.append('ERROR: Port "' + sp.get_name() + '" is '
                               'configured, but not mapped to target switch')

        # VLAN configuration
        source_vlan_list = self.source.get_all_vlans()
        target_ports = self.target.get_ports()
        unmapped = [p.get_name() for p in target_ports
                    if p.get_name() not in self._port_mapping_t2s]
        for sv in source_vlan_list:
            tv = self.target.get_vlan(tag=sv.get_tag())
            if not tv:
                tv = VLAN.VLAN(name=sv.get_name(), tag=sv.get_tag(),
                               switch=self.target)
                self.target.add_vlan(tv)
            errors = tv.transfer_config(sv,
                                        self._port_mapping_s2t,
                                        self._lag_mapping_s2t,
                                        unmapped)
            ret.extend(errors)

        # Switch attributes
        self.target.transfer_config(self.source)

        # LAG configuration
        for sl in self.source.get_lags():
            sl_name = sl.get_name()
            tl_name = self._lag_mapping_s2t.get(sl_name)
            if tl_name:
                tl = self.target.get_lags_by_name(tl_name)[0]
                tl.transfer_config(sl)
            else:
                ret.append('INFO: LAG "' + sl_name + '" not mapped to'
                           ' target switch, no config transferred')
                if sl.is_configured() and not (sl.is_disabled_only() or
                                               sl.accidental_config_only()):
                    ret.append('ERROR: LAG "' + sl_name + '" is '
                               'configured, but not mapped to target switch')
                elif sl.is_configured() and sl.is_disabled_only():
                    ret.append('NOTICE: LAG "' + sl_name + '" is '
                               'disabled, but not mapped to target switch')

        # STP configuration
        source_stps = self.source.get_stps()
        target_stps = self.target.get_stps()
        nr_src_stps, nr_of_target_stps = len(source_stps), len(target_stps)
        # transfer STP instances from source to target switch
        # keep target switch defaults by transfering to existing instances
        for (s_stp, t_stp) in zip(source_stps, target_stps):
            t_stp.transfer_config(s_stp)
        # transfer remaining source STP instances
        if nr_src_stps > nr_of_target_stps:
            for s_stp in source_stps[-(nr_src_stps - nr_of_target_stps):]:
                new_stp = STP.STP()
                new_stp.transfer_config(s_stp)
                self.target.add_stp(new_stp)
        # remove extra STP instances from target switch
        if nr_of_target_stps > nr_src_stps:
            self.target.delete_last_n_stps(nr_of_target_stps - nr_src_stps)

        # ACL configuration
        for acl in self.source.get_acls():
            number, name = acl.get_number(), acl.get_name()
            new_acl = ACL.ACL(number, name)
            for ace in acl.get_entries():
                new_ace = ACL.ACE(ace.get_number(), ace.get_action(),
                                  ace.get_protocol(), ace.get_source(),
                                  ace.get_source_mask(), ace.get_source_op(),
                                  ace.get_source_port(), ace.get_dest(),
                                  ace.get_dest_mask(), ace.get_dest_op(),
                                  ace.get_dest_port())
                new_acl.add_ace(new_ace)
            self.target.add_complete_acl(new_acl)

        # Loopback interface configuration
        source_loopback_list = self.source.get_all_loopbacks()
        for s_lo in source_loopback_list:
            self.target.add_loopback(s_lo.get_number())
            t_lo = self.target.get_loopback(s_lo.get_number())
            if t_lo:
                t_lo.transfer_config(s_lo)

        return ret

    def translate(self, config):
        """Translate the provided source switch config to a target config."""
        translation, unknown, err = [], [], []
        if not self.source or not self.target:
            err.append(
                'ERROR: Source and target switch needed for translation'
            )
            return (translation, err)

        self.source.init_conf_values()
        self.target.init_conf_values()
        if self._apply_defaults:
            self.source.apply_default_settings()
            self.target.apply_default_settings()

        ret, errors = self._create_port_mapping()
        err.extend(errors)
        if not ret:
            err.append('ERROR: Could not create valid port mapping from '
                       'source to target.')
            return (translation, err)

        config, errors = self.source.normalize_config(config)
        err.extend(errors)
        config, errors = self.source.expand_macros(config)
        err.extend(errors)

        for line in config:
            ret = self.source.configure(line)
            if ret:
                err.append(ret)
                if (self._copy_unknown and 'Ignoring unknown command' in ret):
                    if self._comment_unknown:
                        comment = self.target.get_cmd().get_comment()
                        if comment:
                            unknown.append(comment + ' ' + line)
                        else:
                            err.append('ERROR: Cannot create comment line '
                                       'for unknown command')
                    else:
                        unknown.append(line)

        ret, errors = self._create_lag_mapping()
        err.extend(errors)
        if not ret:
            err.append('ERROR: Could not create valid LAG mapping from '
                       'source to target.')
            err.append('ERROR: LAG configuration missing from translation')

        transfer_errs = self.transfer_config()
        err.extend(transfer_errs)
        translation, errors = self.target.create_config(self._use_oob_mgmt)
        if unknown:
            translation.append('')
            translation.extend(unknown)
        err.extend(errors)

        return (translation, err)

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
