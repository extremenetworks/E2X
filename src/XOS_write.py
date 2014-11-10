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

""" XOS_write implements writing of EXOS configuration commands.

Classes:
XosConfigWriter, a specialization (subclass) of ConfigWriter, implements
EXOS specific methods for feature modules.
"""

import Switch
import Utils


class XosConfigWriter(Switch.ConfigWriter):

    """ConfigWriter specialization (subclass) for EXOS.

    XosConfigWriter implements writing of EXOS configuration commands
    according to the configuration of the (target) switch model. Writing
    is separated in feature models, called from the generic ConfigWriter
    class. There is one method per feature module.

    Methods:
    port() implements port specific configuration (feature module "port").
    vlan() implements VLAN specific configuration (feature module "VLAN").
    lag() implements LAG specific configuration (feature module "LAG").
    stp() implements spanning tree configuration (feature module "STP").
    """

    def __init__(self, switch):
        super().__init__(switch)

    def _replace_special_characters(self, name):
        trans_dict = str.maketrans('"<>: &', '______')
        return name.translate(trans_dict)

    def port(self):
        conf, err = [], []
        reason = 'written'
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
        return err

    def _normalize_vlan(self, vlan):
        err = []
        v_name = vlan.get_name()
        if v_name and v_name.lower() == 'mgmt':
            err.append('ERROR: Cannot use name "Mgmt" for regular VLAN')
            v_name = None
            vlan.set_name(v_name)
        if v_name and ' ' in v_name:
            err.append('WARN: Replacing " " with "_" in VLAN name "' +
                       v_name + '"')
            v_name = v_name.replace(' ', '_')
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
            for p_name in untagged_egress:
                if p_name in tagged_egress:
                    err.append('ERROR: Port "' + p_name + '" both untagged ' +
                               'and tagged in VLAN "' + str(v_name) +
                               '" (tag ' + str(v_tag) + ')')
                    err.append('ERROR: Removing tagged egress of "' +
                               str(v_name) + '" VLAN from port "' + p_name +
                               '"')
                    vlan.del_egress_port(p_name, 'tagged')
                if p_name not in untagged_ingress:
                    err.append('ERROR: Port "' + str(p_name) + '" in untagged '
                               'egress list of VLAN "' + str(v_name) +
                               '" missing in untagged ingress list: adding '
                               'to ingress')
                    vlan.add_ingress_port(p_name, 'untagged')
            # refresh vlan list copies
            untagged_egress = vlan.get_egress_ports('untagged')
            tagged_egress = vlan.get_egress_ports('tagged')
            untagged_ingress = vlan.get_ingress_ports('untagged')
            tagged_ingress = vlan.get_ingress_ports('tagged')
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
                if p_name in tagged_ingress:
                    err.append('ERROR: Port "' + p_name + '" both untagged '
                               'and tagged in VLAN "' + str(v_name) +
                               '" (tag ' + str(v_tag) + ')')
                    err.append('ERROR: Removing tagged ingress of "' +
                               str(v_name) + '" VLAN from port "' + p_name +
                               '"')
                    vlan.del_ingress_port(p_name, 'tagged')
                if p_name not in untagged_egress:
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
        v_name, v_tag = vlan.get_name(), vlan.get_tag()
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
            conf.append('configure vlan ' + v_name + ' delete ports '
                        + del_seq)
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
                v_name = 'SYS_NLD_' + '{:04d}'.format(v_tag)
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
                if p.get_lacp_aadminkey() == key:
                    l.add_member_port(p.get_name())
                    p.set_lacp_aadminkey(key, reason)
                    if p.get_lacp_enabled() != lacp:
                        err.append('ERROR: LAG "' + l.get_name() +
                                   '" configured with LACP ' +
                                   ('enabled' if lacp else 'disabled') +
                                   ', but member port "' + p.get_name() +
                                   '" has LACP ' +
                                   ('enabled' if p.get_lacp_enabled()
                                    else 'disabled'))
                    else:
                        p.set_lacp_enabled(lacp, reason)
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
        reason = 'written'
        if not self._switch.get_single_port_lag():
            if self._switch.get_single_port_lag_reason() == 'transfer_conf':
                err.append('ERROR: XOS always allows single port LAGs')
            else:
                if self._switch.defaults_were_applied():
                    err.append('NOTICE: XOS always allows single port LAGs')
            self._switch.set_single_port_lag(False, 'warned')
        if self._switch.get_max_lag_reason() == 'transfer_conf':
            # TODO: verify if this is correct
            err.append('WARN: Maximum number of LAGs cannot be configured'
                       ' on XOS')
            self._switch.set_max_lag(None, 'not supported')
        if self._switch.get_lacp_support_reason() == 'transfer_conf':
            # TODO: verify if this is correct
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
                    if stp.get_version() == 'mstp' and stp.get_mst_instance():
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

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
