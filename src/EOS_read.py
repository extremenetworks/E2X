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

"""EOS_read interprets EOS configuration commands.

The configuration commands are applied to the (usually source) EOS switch.
This implements the translation port of interpreting the input configuration.
This functionality is heavily based on the 'cmd' Python module.

Classes:
EosCommand reads the first token, implementing comments, 'set', and 'clear'.
EosSetCommand reads the second token of 'set' commands.
EosClearCommand reads the second token of 'clear' commands.
EosSetLacpCommand implements 'set lacp'.
EosSetLacpSingleportlagCommand implements 'set lacp singleportlag'.
EosSetPortCommand implements 'set port'.
EosSetPortJumboCommand implements 'set port jumbo'.
EosSetPortLacpCommand implements 'set port lacp'.
EosClearPortCommand implements 'clear port'
EosClearPortLacpCommand implements 'clear port lacp'.
EosSetVlanCommand implements 'set vlan'.
EosClearVlanCommand implements 'clear vlan'.
EosSetSpantreeCommand implements 'set spantree'.
EosSetSpantreeVersionCommand implements 'set spantree version'.
EosSetSpantreeMstiCommand implements 'set spantree msti'.
EosSetSpantreeMstcfgidCommand implements 'set spantree mstcfgid'.
EosSetSpantreeSpanguardCommand implements 'set spantree spanguard'.
EosSetSpantreeAutoedgeCommand implements 'set spantree autoedge'.

All of the above classes should be considered private, used via calling
Switch.configure().
"""

import cmd

import STP
import Switch
import Utils
import VLAN


class EosSetSpantreeAutoedgeCommand(Switch.CmdInterpreter):

    """Commands starting with 'set spantree autoedge'."""

    def __init__(self, switch):
        super().__init__()
        self._switch = switch

    def default(self, line):
        return ('NOTICE: Ignoring unknown command "set spantree autoedge ' +
                line + '"')

    def _change_autoedge(self, cmd, arg):
        if cmd != 'enable' and cmd != 'disable':
            return ('ERROR: Wrong command "' + cmd + '" to _change_autoedge()')
        if arg:
            return ('ERROR: Unknown argument "' + arg + '" to command '
                    '"set spantree autoedge ' + cmd + '"')
        port_list = self._switch.get_ports() + self._switch.get_lags()
        if not port_list:
            return 'ERROR: Cannot configure Auto Edge on switch without ports'
        new_state = True if cmd == 'enable' else False
        for p in port_list:
            p.set_stp_auto_edge(new_state, 'config')
        return ''

    def do_enable(self, arg):
        return self._change_autoedge('enable', arg)

    def do_disable(self, arg):
        return self._change_autoedge('disable', arg)


class EosSetSpantreeSpanguardCommand(Switch.CmdInterpreter):

    """Commands starting with 'set spantree spanguard'."""

    def __init__(self, switch):
        super().__init__()
        self._switch = switch

    def default(self, line):
        return ('NOTICE: Ignoring unknown command "set spantree spanguard ' +
                line + '"')

    def _change_spanguard(self, cmd, arg):
        if cmd != 'enable' and cmd != 'disable':
            return ('ERROR: Wrong command "' + cmd +
                    '" to _change_spanguard()')
        if arg:
            return ('ERROR: Unknown argument "' + arg + '" to command '
                    '"set spantree spanguard ' + cmd + '"')
        port_list = self._switch.get_ports() + self._switch.get_lags()
        if not port_list:
            return 'ERROR: Cannot configure SpanGuard on switch without ports'
        new_state = True if cmd == 'enable' else False
        for p in port_list:
            p.set_stp_bpdu_guard(new_state, 'config')
        return ''

    def do_enable(self, arg):
        return self._change_spanguard('enable', arg)

    def do_disable(self, arg):
        return self._change_spanguard('disable', arg)


class EosSetSpantreeMstcfgidCommand(Switch.CmdInterpreter):

    """Commands starting with 'set spantree mstcfgid'."""

    def __init__(self, switch):
        super().__init__()
        self._switch = switch

    def default(self, line):
        return ('NOTICE: Ignoring unknown command "set spantree mstcfgid ' +
                line + '"')

    def do_cfgname(self, arg):
        if not arg:
            return 'ERROR: "set spantree mstcfgid cfgname" needs a name'
        arg_list = arg.rstrip().split()
        if len(arg_list) != 1 and len(arg_list) != 3:
            return ('ERROR: Wrong number of arguments to'
                    ' "set spantree mstcfgid cfgname" (' + arg + ')')
        name = arg_list[0]
        stp = self._switch.get_stp_by_mst_instance(0)
        if not stp:
            return ('ERROR: MST instance 0 missing '
                    '(set spantree mstcfgid cfgname)')
        stp.set_mst_cfgname(name, 'config')
        if len(arg_list) == 3:
            unhandled_arg = ' '.join(arg_list[1:])
            return self.onecmd(unhandled_arg)
        return ''

    def do_rev(self, arg):
        if not arg:
            return 'ERROR: "set spantree mstcfgid rev" needs a revision number'
        arg_list = arg.rstrip().split()
        if len(arg_list) != 1 and len(arg_list) != 3:
            return ('ERROR: Wrong number of arguments to'
                    ' "set spantree mstcfgid rev" (' + arg + ')')
        try:
            rev = int(arg_list[0])
        except:
            return ('ERROR: Revision number must be an integer '
                    '(set spantree mstcfgid rev ' + arg_list[0] + ')')
        if rev < 0 or rev > 65535:
            return ('ERROR: Revision number must be in [0,65535] '
                    '(set spantree mstcfgid rev ' + arg_list[0] + ')')
        stp = self._switch.get_stp_by_mst_instance(0)
        if not stp:
            return ('ERROR: MST instance 0 missing '
                    '(set spantree mstcfgid rev)')
        stp.set_mst_rev(rev, 'config')
        if len(arg_list) == 3:
            unhandled_arg = ' '.join(arg_list[1:])
            return self.onecmd(unhandled_arg)
        return ''


class EosSetSpantreeMstiCommand(Switch.CmdInterpreter):

    """Commands starting with 'set spantree msti'."""

    def __init__(self, switch):
        super().__init__()
        self._switch = switch

    def default(self, line):
        return ('NOTICE: Ignoring unknown command "set spantree msti ' +
                line + '"')

    def do_sid(self, arg):
        arg_list = arg.rstrip().split()
        if len(arg_list) != 2:
            return ('ERROR: Incorrect command "set spantree msti sid ' +
                    arg + '"')
        try:
            sid = int(arg_list[0])
        except:
            return ('ERROR: SID must be an integer (set spantree msti sid ' +
                    arg + ')')
        if sid < 1 or sid > 4094:
            return ('ERROR: SID must be in [1,4094] (set spantree msti sid ' +
                    arg + ')')
        action = arg_list[1]
        if action == 'create':
            new_stp = STP.STP()
            new_stp.enable('config')
            new_stp.set_version('mstp', 'config')
            new_stp.set_priority(32768, 'default')
            new_stp.set_mst_instance(sid, 'config')
            self._switch.add_stp(new_stp)
            return ''
        elif action == 'delete':
            return self._switch.delete_stp_by_instance_id(sid)
        else:
            return 'ERROR: Wrong number of arguments to "set spantree msti"'


class EosSetSpantreeVersionCommand(Switch.CmdInterpreter):

    """Commands starting with 'set spantree version'."""

    def __init__(self, switch):
        super().__init__()
        self._switch = switch

    def _set_version(self, version):
        stp_list = self._switch.get_stps()
        if not stp_list:
            return 'ERROR: Cannot configure version of non-existing STP'
        for stp in stp_list:
            ret = stp.set_version(version, 'config')
            if ret != version:
                return ('ERROR: Could not apply "set spantree version ' +
                        version + '"')
        return ''

    def default(self, line):
        return ('NOTICE: Ignoring unknown command "set spantree version' +
                line + '"')

    def do_mstp(self, arg):
        return self._set_version('mstp')

    def do_rstp(self, arg):
        return self._set_version('rstp')

    def do_stpcompatible(self, arg):
        return self._set_version('stp')


class EosSetSpantreeCommand(Switch.CmdInterpreter):

    """Commands starting with 'set spantree'."""

    def __init__(self, switch):
        super().__init__()
        self._switch = switch
        self._set_spantree_version = EosSetSpantreeVersionCommand(switch)
        self._set_spantree_msti = EosSetSpantreeMstiCommand(switch)
        self._set_spantree_mstcfgid = EosSetSpantreeMstcfgidCommand(switch)
        self._set_spantree_spanguard = EosSetSpantreeSpanguardCommand(switch)
        self._set_spantree_autoedge = EosSetSpantreeAutoedgeCommand(switch)

    def default(self, line):
        return ('NOTICE: Ignoring unknown command "set spantree ' +
                line + '"')

    def do_disable(self, arg):
        if arg:
            return 'ERROR: "set spantree disable" takes no argument'
        stp_list = self._switch.get_stps()
        if not stp_list:
            return 'WARN: Cannot disable non-existing STP'
        for stp in stp_list:
            stp.disable('config')
        return ''

    def do_enable(self, arg):
        if arg:
            return 'ERROR: "set spantree enable" takes no argument'
        stp_list = self._switch.get_stps()
        if not stp_list:
            return 'ERROR: Cannot enable non-existing STP'
        for stp in stp_list:
            stp.enable('config')
        return ''

    def do_version(self, arg):
        return self._set_spantree_version.onecmd(arg)

    def do_msti(self, arg):
        return self._set_spantree_msti.onecmd(arg)

    def do_mstmap(self, arg):
        if not arg:
            return 'ERROR: "set spantree mstmap" needs a FID argument'
        arg_list = arg.rstrip().split()
        if len(arg_list) != 1 and len(arg_list) != 3:
            return 'ERROR: Wrong number of arguments to "set spantree mstmap"'
        if len(arg_list) == 3 and arg_list[1].lower() != 'sid':
            return ('ERROR: Second argument to "set spantree mstmap" must be'
                    ' "sid"')
        fid_sequence = arg_list[0]
        fid_list = Utils.expand_sequence_to_int_list(fid_sequence)
        if not fid_list or min(fid_list) < 1 or max(fid_list) > 4094:
            return 'ERROR: Illegal FID "' + fid_sequence + '"'
        sid = arg_list[2] if len(arg_list) == 3 else 0
        try:
            sid = int(sid)
        except:
            return 'ERROR: MST instance ID must be an integer'
        stp_list = self._switch.get_stps()
        for stp in stp_list:
            stp.del_vlans(fid_list, 'config')
        stp = self._switch.get_stp_by_mst_instance(sid)
        stp.add_vlans(fid_list, 'config')
        return ''

    def do_mstcfgid(self, arg):
        return self._set_spantree_mstcfgid.onecmd(arg)

    def do_priority(self, arg):
        if not arg:
            return 'ERROR: "set spantree priority" needs a priority'
        arg_list = arg.rstrip().split()
        if len(arg_list) != 1 and len(arg_list) != 2:
            return ('ERROR: Wrong number of arguments to '
                    '"set spantree priority"')
        try:
            priority = int(arg_list[0])
        except:
            return 'ERROR: Priority must be an integer (set spantree priority)'
        if priority < 0 or priority > 61440:
            return ('ERROR: Priority must be in [0,61440] '
                    '(set spantree priority)')
        sid = 0
        if len(arg_list) == 2:
            try:
                sid = int(arg_list[1])
            except:
                return ('ERROR: MST instance ID must be an integer'
                        ' (set spantree priority)')
        stp = self._switch.get_stp_by_mst_instance(sid)
        if not stp:
            return ('ERROR: MST instance with ID "' + str(sid) + '" not found'
                    ' (set spantree priority)')
        ret = stp.set_priority(priority, 'config')
        if ret != priority:
            return ('ERROR: Could not set priority "' + str(priority) + '"'
                    ' (set spantree priority)')
        return ''

    def do_spanguard(self, arg):
        return self._set_spantree_spanguard.onecmd(arg)

    def do_autoedge(self, arg):
        return self._set_spantree_autoedge.onecmd(arg)

    def do_portadmin(self, arg):
        arg_list = arg.rstrip().split()
        if len(arg_list) != 2:
            return ('ERROR: Wrong number of arguments to '
                    '"set spantree portadmin"')
        portstring = arg_list[0]
        port_list = self._switch.get_ports_by_name(portstring)
        if not port_list:
            return ('ERROR: Port ' + portstring + ' not found '
                    '(set spantree portadmin)')
        cmd = arg_list[1]
        if cmd != 'enable' and cmd != 'disable':
            return ('ERROR: Unknown argument "' + cmd + '" to "'
                    'set spantree portadmin ' + portstring + '"')
        new_state = True if cmd == 'enable' else False
        for p in port_list:
            p.set_stp_enabled(new_state, 'config')
        cmd = arg_list[1]
        return ''

    def do_adminedge(self, arg):
        arg_list = arg.rstrip().split()
        if len(arg_list) != 2:
            return ('ERROR: Wrong number of arguments to '
                    '"set spantree adminedge"')
        portstring = arg_list[0]
        port_list = self._switch.get_ports_by_name(portstring)
        if not port_list:
            return ('ERROR: Port ' + portstring + ' not found '
                    '(set spantree adminedge)')
        cmd = arg_list[1]
        if cmd != 'true' and cmd != 'false':
            return ('ERROR: Unknown argument "' + cmd + '" to "'
                    'set spantree adminedge ' + portstring + '"')
        new_state = True if cmd == 'true' else False
        for p in port_list:
            p.set_stp_edge(new_state, 'config')
        cmd = arg_list[1]
        return ''


class EosClearVlanCommand(Switch.CmdInterpreter):

    """Commands starting with 'clear vlan'."""

    def __init__(self, switch):
        super().__init__()
        self._switch = switch

    def default(self, line):
        return 'WARN: Ignoring unknown command "clear vlan ' + line + '"'

    def do_egress(self, arg):
        if not arg:
            return 'ERROR: Missing parameters for "clear vlan egress" command'
        arglst = arg.split()
        if len(arglst) != 2:
            return 'ERROR: Wrong number of arguments to "clear vlan egress"'
        vlanlist = Utils.expand_sequence(arglst[0])
        taglist = []
        for vt in vlanlist:
            try:
                tag = int(vt)
            except:
                return 'ERROR: VLAN tag must be an integer (clear vlan egress)'
            taglist.append(tag)
        for tag in taglist:
            portstring = arglst[1]
            portlist = self._switch.get_ports_by_name(portstring)
            if not portlist:
                ret = 'ERROR: Port ' + portstring
                ret += ' not found (clear vlan egress)'
                return ret
            v = self._switch.get_vlan(tag=tag)
            if not v:
                return ('ERROR: VLAN ' + str(tag) +
                        ' not found (clear vlan egress)')
            for p in portlist:
                v.del_egress_port(p.get_name(), 'all')
        return ''


class EosSetVlanCommand(Switch.CmdInterpreter):

    """Commands starting with 'set vlan'."""

    def __init__(self, switch):
        super().__init__()
        self._switch = switch

    def default(self, line):
        return 'WARN: Ignoring unknown command "set vlan ' + line + '"'

    def do_create(self, arg):
        # verify that tags are valid
        if not arg:
            return 'ERROR: Missing VLAN tag in "set vlan create" command'
        try:
            tags = [int(t) for t in Utils.expand_sequence(arg)]
        except:
            return 'ERROR: VLAN tag must be an integer (set vlan create)'
        for tag in tags:
            if tag <= 0 or tag > 4095:
                return ('ERROR: VLAN tag must be in [1,4095], but is ' +
                        str(tag))
        # create VLANs
        for tag in tags:
            new_vlan = VLAN.VLAN(tag=tag, switch=self._switch)
            self._switch.add_vlan(new_vlan)
        return ''

    def do_name(self, arg):
        space = arg.find(' ')
        if space > -1:
            try:
                tag = int(arg[:space])
            except:
                return 'ERROR: VLAN tag must be an integer (set vlan name)'
            name = arg[space + 1:].strip('"')
        else:
            try:
                tag = int(arg.rstrip())
            except:
                return 'ERROR: VLAN tag must be an integer (set vlan name)'
            name = ''
        v = self._switch.get_vlan(tag=tag)
        if not v:
            return 'ERROR: VLAN ' + str(tag) + ' not found (set vlan name)'
        v.set_name(name)
        return ''

    def do_egress(self, arg):
        if not arg:
            return 'ERROR: Missing parameters for "set vlan egress" command'
        arglst = arg.split()
        if len(arglst) == 2:
            tagged = 'tagged'
        elif len(arglst) == 3:
            tagged = arglst[2]
        else:
            return 'ERROR: Wrong number of arguments to "set vlan egress"'
        vlanlist = Utils.expand_sequence(arglst[0])
        taglist = []
        for vt in vlanlist:
            try:
                tag = int(vt)
            except:
                return 'ERROR: VLAN tag must be an integer (set vlan egress)'
            taglist.append(tag)
        for tag in taglist:
            portstring = arglst[1]
            portlist = self._switch.get_ports_by_name(portstring)
            if not portlist:
                ret = 'ERROR: Port ' + portstring
                ret += ' not found (set vlan egress)'
                return ret
            v = self._switch.get_vlan(tag=int(tag))
            if not v:
                return ('ERROR: VLAN ' + str(tag) +
                        ' not found (set vlan egress)')
            for p in portlist:
                v.add_egress_port(p.get_name(), tagged)
                if tagged == 'tagged':
                    v.add_ingress_port(p.get_name(), tagged)
        return ''


class EosClearPortCommand(Switch.CmdInterpreter):

    """Commands starting with 'clear port'."""

    def __init__(self, switch):
        super().__init__()
        self._switch = switch
        self._clear_port_lacp = EosClearPortLacpCommand(switch)

    def default(self, line):
        return 'WARN: Ignoring unknown command "clear port ' + line + '"'

    def do_lacp(self, arg):
        return self._clear_port_lacp.onecmd(arg)


class EosClearPortLacpCommand(Switch.CmdInterpreter):

    """Commands starting with 'clear port lacp'."""

    def __init__(self, switch):
        super().__init__()
        self._switch = switch

    def default(self, line):
        return 'WARN: Ignoring unknown command "clear port lacp ' + line + '"'

    def do_port(self, arg):
        arglst = arg.split()
        if not arglst:
            return 'ERROR: "clear port lacp port" needs a port string'
        portlist = self._switch.get_ports_by_name(arglst[0])
        if not portlist:
            return 'ERROR: Port ' + arg + ' not found (clear port lacp port)'
        if len(arglst) < 2:
            funcs = [('set_lacp_enabled', [False, 'config'], False),
                     ('set_lacp_aadminkey', [32768, 'config'], 32768)]
        elif len(arglst) == 2:
            subcmd = arglst[1]
            if subcmd == 'all':
                funcs = [('set_lacp_enabled', [False, 'config'], False),
                         ('set_lacp_aadminkey', [32768, 'config'], 32768)]
            elif subcmd == 'aadminkey':
                funcs = [('set_lacp_aadminkey', [32768, 'config'], 32768)]
            else:
                return ('ERROR: unknown command "clear port lacp port ' +
                        arg + '"')
        else:
            return 'ERROR: unknown command "clear port lacp port ' + arg + '"'
        for p in portlist:
            for f in funcs:
                r = getattr(p, f[0])(*f[1])
            if r != f[2]:
                return ('ERROR: could not apply "clear port lacp port ' + arg +
                        '"')
        return ''


class EosSetPortLacpCommand(Switch.CmdInterpreter):

    """Commands starting with 'set port lacp'."""

    def __init__(self, switch):
        super().__init__()
        self._switch = switch

    def default(self, line):
        return 'WARN: Ignoring unknown command "set port lacp ' + line + '"'

    def do_port(self, arg):
        arglst = arg.split()
        if not arglst:
            return 'ERROR: "set port lacp port" needs a port string'
        portlist = self._switch.get_ports_by_name(arglst[0])
        if not portlist:
            return 'ERROR: Port ' + arg + ' not found (set port lacp port)'
        if len(arglst) < 2:
            return ('ERROR: incomplete command "set port lacp port ' +
                    arglst[0] + '"')
        subcmd = arglst[1]
        if subcmd == 'enable':
            func_name = 'set_lacp_enabled'
            func_params = [True, 'config']
            func_ret = True
        elif subcmd == 'disable':
            func_name = 'set_lacp_enabled'
            func_params = [False, 'config']
            func_ret = False
        elif subcmd == 'aadminkey':
            if len(arglst) < 3:
                return ('ERROR: "set port lacp port ' + arglst[0] +
                        ' aadminkey" needs a key value')
            try:
                key = int(arglst[2])
            except:
                return 'ERROR: LACP actor key must be an integer'
            if key < 0 or key > 65535:
                return 'ERROR: LACP actor key must be in [0..65535]'
            func_name = 'set_lacp_aadminkey'
            func_params = [key, 'config']
            func_ret = key
        else:
            return 'ERROR: unknown command "set port lacp port ' + arg + '"'
        skipped_ports = []
        for p in portlist:
            if (func_name == 'set_lacp_enabled' and
               p.get_name().startswith('lag.')):
                skipped_ports.append(p.get_name())
            else:
                r = getattr(p, func_name)(*func_params)
                if r != func_ret:
                    return ('ERROR: could not apply "set port lacp port ' +
                            arg + '"')
        if skipped_ports:
            return ('INFO: LACPDUs cannot be disabled or enabled on LAG'
                    ' interfaces, skipped port(s) ' + str(skipped_ports) +
                    ' (command "set port lacp port ' + arg + '")')
        return ''


class EosSetPortJumboCommand(Switch.CmdInterpreter):

    """Commands starting with 'set port jumbo'."""

    def __init__(self, switch):
        super().__init__()
        self._switch = switch

    def default(self, line):
        return 'WARN: Ignoring unknown command "set port jumbo ' + line + '"'

    def do_enable(self, arg):
        ret = ''
        portlist = self._switch.get_ports_by_name(arg)
        if not portlist:
            ret += 'ERROR: Port ' + arg + ' not found (set port jumbo enable)'
        for p in portlist:
            r = p.set_jumbo(True, 'config')
            if not r:
                ret += 'ERROR: Could not enable jumbo frames for port '
                ret += p.get_name()
        return ret

    def do_disable(self, arg):
        ret = ''
        portlist = self._switch.get_ports_by_name(arg)
        if not portlist:
            ret += 'ERROR: Port ' + arg + ' not found (set port jumbo disable)'
        for p in portlist:
            r = p.set_jumbo(False, 'config')
            if r:
                ret += 'ERROR: Could not disable jumbo frames for port '
                ret += p.get_name()
        return ret


class EosSetPortCommand(Switch.CmdInterpreter):

    """Commands starting with 'set port'."""

    def __init__(self, switch):
        super().__init__()
        self._switch = switch
        self._set_port_jumbo = EosSetPortJumboCommand(switch)
        self._set_port_lacp = EosSetPortLacpCommand(switch)

    def default(self, line):
        return 'WARN: Ignoring unknown command "set port ' + line + '"'

    def do_alias(self, arg):
        ret = ''
        reason = 'config'
        space = arg.find(' ')
        if space > -1:
            portstring = arg[:space]
            alias = arg[space + 1:]
        else:
            portstring = arg
            alias = ''
        alias = alias.strip('"')
        short = alias[:15]
        portlist = self._switch.get_ports_by_name(portstring)
        if not portlist:
            ret += 'ERROR: Port ' + arg + ' not found (set port alias)'
        for p in portlist:
            r = p.set_description(alias, reason)
            r = r and p.set_short_description(short, reason)
            if not r:
                ret += 'ERROR: Could not set description on ' + portstring
        return ret

    def do_enable(self, arg):
        ret = ''
        portlist = self._switch.get_ports_by_name(arg)
        if not portlist:
            ret += 'ERROR: Port ' + arg + ' not found (set port enable)'
        for p in portlist:
            r = p.set_admin_state(True, 'config')
            if not r:
                ret += 'ERROR: Could not enable port ' + p.get_name()
        return ret

    def do_disable(self, arg):
        ret = ''
        portlist = self._switch.get_ports_by_name(arg)
        if not portlist:
            ret += 'ERROR: Port ' + arg + ' not found (set port disable)'
        for p in portlist:
            r = p.set_admin_state(False, 'config')
            if r:
                ret += 'ERROR: Could not disable port ' + p.get_name()
        return ret

    def do_speed(self, arg):
        ret = ''
        arg_list = arg.split()
        if len(arg_list) != 2:
            ret = 'ERROR: Too many arguments to "set port speed":'
            ret += ' set port speed ' + arg
            return ret
        portlist = self._switch.get_ports_by_name(arg_list[0])
        if not portlist:
            ret = 'ERROR: Port ' + arg_list[0] + ' not found (set port speed)'
            return ret
        for p in portlist:
            r = p.set_speed(int(arg_list[1]), 'config')
            if not r:
                ret = 'ERROR: Could not set speed of port "' + arg_list[0]
                ret += '" to "' + arg_list[1] + '"'
        return ret

    def do_duplex(self, arg):
        ret = ''
        arg_list = arg.split()
        if len(arg_list) != 2:
            ret = 'ERROR: Wrong arguments to "set port duplex":'
            ret += ' set port duplex ' + arg
            return ret
        portlist = self._switch.get_ports_by_name(arg_list[0])
        if not portlist:
            ret = 'ERROR: Port ' + arg_list[0] + ' not found (set port duplex)'
            return ret
        for p in portlist:
            duplex2Set = arg_list[1]
            r = p.set_duplex(duplex2Set, 'config')
            if r != duplex2Set:
                ret = 'ERROR: Could not set duplex of port "' + arg_list[0]
                ret += '" to "' + duplex2Set + '"'
        return ret

    def do_negotiation(self, arg):
        ret = ''
        arg_list = arg.split()
        if len(arg_list) != 2:
            ret = 'ERROR: Wrong arguments to "set port negotiation":'
            ret += ' set port negotiation ' + arg
            return ret
        if arg_list[1] == 'enable':
            auto_neg = True
        elif arg_list[1] == 'disable':
            auto_neg = False
        else:
            ret = 'ERROR: Unknown parameter "' + arg_list[1] + '" to set port '
            ret += 'negotiation'
            return ret
        portlist = self._switch.get_ports_by_name(arg_list[0])
        if not portlist:
            ret = 'ERROR: Port ' + arg_list[0]
            ret += ' not found (set port negotiation)'
            return ret
        for p in portlist:
            r = p.set_auto_neg(auto_neg, 'config')
            if r != auto_neg:
                ret = 'ERROR: Could not '
                if auto_neg:
                    ret += 'enable '
                else:
                    ret += 'disable '
                ret += 'auto-negotiation of port "' + arg_list[0] + '"'
        return ret

    def do_jumbo(self, arg):
        return self._set_port_jumbo.onecmd(arg)

    def do_vlan(self, arg):
        ret = ''
        arglst = arg.split()
        if len(arglst) == 2:
            portstring, tag, modify = arglst[0], arglst[1], False
        elif len(arglst) == 3:
            portstring, tag, modify = arglst[0], arglst[1], arglst[2]
            if modify == 'modify-egress':
                modify = True
            else:
                ret += 'ERROR: unknown argument ' + modify
                ret += ' to "set port vlan ' + portstring + ' ' + tag + '"'
                return ret
        else:
            ret += 'ERROR: Wrong number of arguments to "set port vlan": "'
            ret += arg + '"'
            return ret
        portlist = self._switch.get_ports_by_name(portstring)
        if not portlist:
            ret += 'ERROR: Port ' + portstring
            ret += ' not found (set port vlan)'
            return ret
        v = self._switch.get_vlan(tag=int(tag))
        if not v:
            ret += 'ERROR: VLAN ' + tag + ' not found (set port vlan)'
            return ret
        for p in portlist:
            for tmp_v in self._switch.get_all_vlans():
                tmp_v.del_ingress_port(p.get_name(), 'untagged')
                if modify:
                    tmp_v.del_egress_port(p.get_name(), 'all')
            v.add_ingress_port(p.get_name(), 'untagged')
            if modify:
                v.add_egress_port(p.get_name(), 'untagged')
        return ret

    def do_lacp(self, arg):
        return self._set_port_lacp.onecmd(arg)


class EosSetLacpSingleportlagCommand(Switch.CmdInterpreter):

    """Commands starting with 'set lacp singleportlag'."""

    def __init__(self, switch):
        super().__init__()
        self._switch = switch

    def default(self, line):
        return ('NOTICE: Ignoring unknown command "set lacp singleportlag ' +
                line + '"')

    def do_disable(self, arg):
        if arg:
            return 'ERROR: "set lacp singleportlag disable" takes no argument'
        r = self._switch.set_single_port_lag(False, 'config')
        if r is None or r:
            return 'ERROR: Could not disable single port lag'
        return ''

    def do_enable(self, arg):
        if arg:
            return 'ERROR: "set lacp singleportlag enable" takes no argument'
        r = self._switch.set_single_port_lag(True, 'config')
        if r is None or not r:
            return 'ERROR: Could not enable single port lag'
        return ''


class EosSetLacpCommand(Switch.CmdInterpreter):

    """Commands starting with 'set lacp'."""

    def __init__(self, switch):
        super().__init__()
        self._switch = switch
        self._set_lacp_singleportlag = EosSetLacpSingleportlagCommand(switch)

    def default(self, line):
        return 'NOTICE: Ignoring unknown command "set lacp ' + line + '"'

    def do_aadminkey(self, arg):
        arglst = arg.split()
        if len(arglst) != 2:
            return 'ERROR: "set lacp aadminkey" needs two arguments'
        try:
            key = int(arglst[1])
        except:
            return 'ERROR: LACP actor key must be an integer'
        if key < 0 or key > 65535:
            return 'ERROR: LACP actor key must be in [0..65535]'
        portstring = arglst[0]
        portlist = self._switch.get_ports_by_name(portstring)
        if not portlist:
            return ('ERROR: Port ' + portstring +
                    ' not found (set lacp aadminkey)')
        for p in portlist:
            r = p.set_lacp_aadminkey(key, 'config')
            if r != key:
                return ('ERROR: Could not apply "set lacp aadminkey ' +
                        arg + '"')
        return ''

    def do_disable(self, arg):
        if arg:
            return 'ERROR: "set lacp disable" takes no arguments'
        r = self._switch.set_lacp_support(False, 'config')
        if r is None or r:
            return 'ERROR: Could not apply "set lacp disable"'
        return ''

    def do_enable(self, arg):
        if arg:
            return 'ERROR: "set lacp enable" takes no arguments'
        r = self._switch.set_lacp_support(True, 'config')
        if not r:
            return 'ERROR: Could not apply "set lacp enable"'
        return ''

    def do_static(self, arg):
        error = False
        if len(arg.split()) != 1:
            error = True
        for c in ['*', ',', '-', ';']:
            if c in arg:
                error = True
        if error:
            return 'ERROR: Unknown argument "' + arg + '" (set lacp static)'
        laglst = self._switch.get_ports_by_name(arg)
        if not laglst:
            return 'ERROR: LAG "' + arg + '" not found (set lacp static)'
        if len(laglst) != 1:
            return 'ERROR: "set lacp static" accepts a single LAG only'
        lag = laglst[0]
        r = lag.set_lacp_enabled(False, 'config')
        if r is None or r:
            return 'ERROR: Could not configure static LAG "' + arg + '"'
        return ''

    def do_singleportlag(self, arg):
        return self._set_lacp_singleportlag.onecmd(arg)


class EosClearCommand(Switch.CmdInterpreter):

    """Commands starting with 'clear'."""

    def __init__(self, switch):
        super().__init__()
        self._clear_vlan = EosClearVlanCommand(switch)
        self._clear_port = EosClearPortCommand(switch)

    def default(self, line):
        return 'NOTICE: Ignoring unknown command "clear ' + line + '"'

    def do_vlan(self, arg):
        return self._clear_vlan.onecmd(arg)

    def do_port(self, arg):
        return self._clear_port.onecmd(arg)


class EosSetCommand(Switch.CmdInterpreter):

    """Commands starting with 'set'."""

    def __init__(self, switch):
        super().__init__()
        self._set_port = EosSetPortCommand(switch)
        self._set_vlan = EosSetVlanCommand(switch)
        self._set_lacp = EosSetLacpCommand(switch)
        self._set_spantree = EosSetSpantreeCommand(switch)

    def default(self, line):
        return 'NOTICE: Ignoring unknown command "set ' + line + '"'

    def do_port(self, arg):
        return self._set_port.onecmd(arg)

    def do_vlan(self, arg):
        return self._set_vlan.onecmd(arg)

    def do_lacp(self, arg):
        return self._set_lacp.onecmd(arg)

    def do_spantree(self, arg):
        return self._set_spantree.onecmd(arg)


class EosCommand(Switch.CmdInterpreter):

    """Interpret first token of all supported EOS commands."""

    def __init__(self, switch):
        super().__init__()
        self._comments = ['#', '!']
        self._set = EosSetCommand(switch)
        self._clear = EosClearCommand(switch)

    def do_set(self, arg):
        return self._set.onecmd(arg)

    def do_clear(self, arg):
        return self._clear.onecmd(arg)

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
