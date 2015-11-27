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

"""EOS_read interprets EOS configuration commands.

The configuration commands are applied to the (usually source) EOS switch.
This implements the translation port of interpreting the input configuration.
This functionality is heavily based on the 'cmd' Python module.

Classes:
EosCommand reads the first token, implementing comments, 'set', and 'clear'.
EosSetCommand reads the second token of 'set' commands.
EosClearCommand reads the second token of 'clear' commands.
EosSetLacpCommand implements 'set lacp'.
EosIpCommand implements commands in router mode starting with 'ip'.
EosNoCommand implements commands in router mode starting with 'no'.
EosNoIpCommand implements commands in router mode starting with 'no ip'.
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
EosSetSystemCommand implements 'set system'.
EosSetBannerCommand implements 'set banner'.
EosSetTelnetCommand implements 'set telnet'.
EosSetSshCommand implements 'set ssh'.
EosSetWebviewCommand implements 'set webview'.
EosSetSslCommand implements 'set ssl'.
EosSetIpCommand implements 'set ip'.
EosSetIpProtocolCommand implements 'set ip protocol'.
EosSetHostCommand implements 'set host'.
EosSetLoggingCommand implements 'set logging'.
EosSetSntpCommand implements 'set sntp'.
EosSetSummertimeCommand implements 'set summertime'.
EosSetRadiusCommand implements 'set radius'.
EosSetRadiusInterfaceCommand implements 'set radius interface'.
EosSetTacacsCommand implements 'set tacacs'.
EosSetTacacsInterfaceCommand implements 'set tacacs interface'.
EosSetSnmpCommand implements 'set snmp'.
EosClearSystemCommand implements 'clear system'.

All of the above classes should be considered private, used via calling
Switch.configure().
"""

import ipaddress
import re

import STP
import Switch
import Utils
import VLAN

from ACL import ACL, ACE, Standard_ACE
from Tokenizer import Tokenizer


def _parse_interface(interface):
    """Parse interface name into type and number."""
    if (not isinstance(interface, str) or
            not interface.startswith('interface ')):
        return None
    token_lst = interface.split()
    if len(token_lst) < 3:
        return None
    iftype, ifnumber = token_lst[1:3]
    if iftype not in {'vlan', 'loopback'}:
        return None
    try:
        ifnumber = int(ifnumber)
    except:
        return None
    return (iftype, ifnumber)


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
        return 'NOTICE: Ignoring unknown command "clear vlan ' + line + '"'

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
        return 'NOTICE: Ignoring unknown command "set vlan ' + line + '"'

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
                return ('ERROR: VLAN tag must be an integer (set vlan name ' +
                        arg + ')')
            name = arg[space + 1:].strip('"')
        else:
            try:
                tag = int(arg.rstrip())
            except:
                return ('ERROR: VLAN tag must be an integer (set vlan name ' +
                        arg + ')')
            name = ''
        v = self._switch.get_vlan(tag=tag)
        if not v:
            return ('ERROR: VLAN ' + str(tag) + ' not found (set vlan name ' +
                    arg + ')')
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
        return 'NOTICE: Ignoring unknown command "clear port ' + line + '"'

    def do_lacp(self, arg):
        return self._clear_port_lacp.onecmd(arg)


class EosClearPortLacpCommand(Switch.CmdInterpreter):

    """Commands starting with 'clear port lacp'."""

    def __init__(self, switch):
        super().__init__()
        self._switch = switch

    def default(self, line):
        return ('NOTICE: Ignoring unknown command "clear port lacp ' +
                line + '"')

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


class EosClearSystemCommand(Switch.CmdInterpreter):

    """Commands starting with 'clear'."""

    def __init__(self, switch):
        super().__init__()
        self._switch = switch

    def default(self, line):
        return 'NOTICE: Ignoring unknown command "clear system ' + line + '"'

    def do_login(self, line):
        if not line:
            return 'ERROR: "clear system login" needs a login name to clear'
        if len(line.split()) != 1:
            return ('NOTICE: Ignoring unknown command "clear system login ' +
                    line + '"')
        ret = self._switch.del_user_account(line)
        if ret is None:
            return ('WARN: Could not delete non-existing user account "' +
                    line + '"')
        return ''


class EosSetPortLacpCommand(Switch.CmdInterpreter):

    """Commands starting with 'set port lacp'."""

    def __init__(self, switch):
        super().__init__()
        self._switch = switch

    def default(self, line):
        return 'NOTICE: Ignoring unknown command "set port lacp ' + line + '"'

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
        return 'NOTICE: Ignoring unknown command "set port jumbo ' + line + '"'

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
        return 'NOTICE: Ignoring unknown command "set port ' + line + '"'

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
            ret += ' not found (set port vlan ' + arg + ')'
            return ret
        v = self._switch.get_vlan(tag=int(tag))
        if not v:
            ret += ('ERROR: VLAN ' + tag + ' not found (set port vlan ' + arg +
                    ')')
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


class EosIpCommand(Switch.CmdInterpreter):

    """Commands (in router interface config mode) starting with 'ip'."""

    def __init__(self, state, switch):
        super().__init__()
        self._state = state
        self._switch = switch

    def default(self, line):
        # catch hyphenated commands
        if line.startswith('access-group'):
            return self._do_access_group(line.split()[1:])
        elif line.startswith('helper-address'):
            return self._do_helper_address(line.split()[1:])
        return 'NOTICE: Ignoring unknown command "ip ' + line + '"'

    def set_state(self, state):
        self._state = state
        return self._state

    def _do_access_group(self, token_lst):
        warn = ''
        if not token_lst:
            return 'ERROR: "ip access-group" needs an argument'
        if not self._state:
            return 'ERROR: "ip access-group" outside router interface'
        interface = self._state[-1]
        intf = _parse_interface(interface)
        if intf is None:
            return ('ERROR: "ip access-group" inside unknown interface "' +
                    str(interface) + '" [interface parse error]')
        if intf[0] == 'loopback':
            return ('ERROR: ACLs cannot be bound to a loopback interface (' +
                    interface + ').')
        # intf is a VLAN, so check it
        if not VLAN.is_valid_tag(intf[1]):
            return ('ERROR: Illegal VLAN ID "' + str(intf[1]) + '" (' +
                    interface + ')')
        vlan = self._switch.get_vlan(tag=intf[1])
        if 'sequence' in token_lst:
            warn = ('WARN: Ignoring "' + ' '.join(token_lst[-2:]) + '" in "' +
                    'ip access-group ' + ' '.join(token_lst) + '"')
        if not vlan:
            return ('ERROR: VLAN "' + str(intf[1]) + '" does not exist (' +
                    ' '.join(token_lst) + ')')
        acl_id = token_lst[0]
        try:
            acl_nr = int(acl_id)
            acl_id = acl_nr
        except:
            return ('NOTICE: Ignoring unknown command "ip access group ' +
                    ' '.join(token_lst) + '"')
        if len(token_lst) > 1:
            direction = token_lst[1]
            if direction not in {'in', 'sequence'}:
                return ('ERROR: Unsupported ACL direction "' + str(direction) +
                        '"')
        vlan.add_ipv4_acl_in(acl_id)
        return warn

    def _do_helper_address(self, token_lst):
        warn = ''
        if not token_lst:
            return 'ERROR: "ip helper-address" needs an argument'
        if len(token_lst) > 1:
            return ('NOTICE: Ignoring unknown command "ip helper-address ' +
                    ' '.join(token_lst) + '"')
        if not self._state:
            return 'ERROR: "ip helper-address" outside router interface'
        interface = self._state[-1]
        intf = _parse_interface(interface)
        if intf is None:
            return ('ERROR: "ip helper-address" inside unknown interface "' +
                    str(interface) + '" [interface parse error]')
        if intf[0] == 'loopback':
            return ('ERROR: DHCP helper addresses cannot be added to a '
                    'loopback interface (' + interface + ').')
        # interface is of type vlan, check it
        if not VLAN.is_valid_tag(intf[1]):
            return ('ERROR: Illegal VLAN ID "' + str(intf[1]) + '" (' +
                    interface + ')')
        vlan = self._switch.get_vlan(tag=intf[1])
        if not vlan:
            return ('ERROR: VLAN "' + str(intf[1]) + '" does not exist (' +
                    ' '.join(token_lst) + ')')
        helper = token_lst[0]
        if not self._is_valid_ip_address(helper):
            return ('ERROR: invalid ip helper-address "' + helper + '"')
        vlan.add_ipv4_helper_address(helper)
        return warn

    def _is_valid_ip_address(self, ip):
        try:
            tmp = ipaddress.IPv4Address(ip)
        except:
            return False
        if tmp is None:
            return False
        return True

    def do_address(self, line):
        if not line:
            return 'ERROR: "ip address" needs an argument'
        if not self._state:
            return 'ERROR: "ip address" outside router interface'
        # check IP address format
        m = re.fullmatch(r'(\d+\.\d+\.\d+\.\d+) +(\d+\.\d+\.\d+\.\d+)'
                         r'(\s+secondary)?', line.strip())
        if not m:
            return ('NOTICE: Ignoring unknown command "ip address ' + line +
                    '"')
        ip, mask, secondary = m.group(1), m.group(2), m.group(3)
        if (ip is None or mask is None or not self._is_valid_ip_address(ip) or
                not self._is_valid_ip_address(mask)):
            return ('NOTICE: Ignoring unknown command "ip address ' + line +
                    '" (invalid IPv4 address)')
        # check for valid interface
        interface = self._state[-1]
        intf = _parse_interface(interface)
        if intf is None:
            return ('ERROR: "ip address" inside unknown interface "' +
                    str(interface) + '" [interface parse error]')
        # handle supported interface types
        iftype, ifnumber = intf[0], intf[1]
        ifhandle = None
        if iftype == 'loopback':
            if not (0 <= ifnumber <= 7):
                return ('ERROR: Illegal Loopback ID "' + str(ifnumber) +
                        '" (' + interface + ')')
            ifhandle = self._switch.get_loopback(ifnumber)
        elif iftype == 'vlan':
            if not VLAN.is_valid_tag(ifnumber):
                return ('ERROR: Illegal VLAN ID "' + str(ifnumber) + '" (' +
                        interface + ')')
            ifhandle = self._switch.get_vlan(tag=ifnumber)
        if not ifhandle:
            return ('ERROR: Interface "' + str(interface) + '" not defined for'
                                                            ' switch')
        if secondary:
            ifhandle.add_ipv4_address(ip, mask)
        else:
            ret = ifhandle.change_ipv4_address(ip, mask)
            if ret is False:
                return ('ERROR: Cannot change primary interface IP for'
                        ' interface "' + str(interface) + '" with secondary'
                        ' IP address(es) (ip address ' + line + ')')
        return ''

    def do_routing(self, line):
        if line:
            return 'NOTICE: Ignoring unknown command "ip routing ' + line + '"'
        self._switch.enable_ipv4_routing()
        return ''

    def do_route(self, line):
        warn = ''
        if not line:
            return 'ERROR: "ip route" needs arguments'
        if not self._state or 'configure' not in self._state:
            warn = 'INFO: "ip route" command outside router config mode'
        _IP_PAT = r'(\d+\.\d+\.\d+\.\d+)'
        m = re.fullmatch(_IP_PAT + ' +' + _IP_PAT + ' +' + _IP_PAT,
                         line.strip())
        if not m:
            return 'NOTICE: Ignoring unknown command "ip route ' + line + '"'
        prefix, mask, gateway = m.group(1), m.group(2), m.group(3)
        if (prefix is None or mask is None or gateway is None or
                not self._is_valid_ip_address(prefix) or
                not self._is_valid_ip_address(mask) or
                not self._is_valid_ip_address(gateway)):
            return 'NOTICE: Ignoring unknown command "ip ' \
                   'route ' + line + '" (invalid IPv4 address)'

        self._switch.add_ipv4_static_route((prefix, mask, gateway))
        return warn


class EosSetSystemCommand(Switch.CmdInterpreter):

    """Commands starting with 'set system'."""

    def __init__(self, switch):
        super().__init__()
        self._switch = switch

    def default(self, line):
        return 'NOTICE: Ignoring unknown command "set system ' + line + '"'

    def do_name(self, arg):
        err = ''
        if not arg:
            self._switch.set_snmp_sys_name(None, 'config')
            return err
        err = self._check_quoting(arg)
        self._switch.set_snmp_sys_name(arg.strip('"'), 'config')
        return err

    def do_contact(self, arg):
        err = ''
        if not arg:
            self._switch.set_snmp_sys_contact(None, 'config')
            return err
        err = self._check_quoting(arg)
        self._switch.set_snmp_sys_contact(arg.strip('"'), 'config')
        return err

    def do_location(self, arg):
        err = ''
        if not arg:
            self._switch.set_snmp_sys_location(None, 'config')
            return err
        err = self._check_quoting(arg)
        self._switch.set_snmp_sys_location(arg.strip('"'), 'config')
        return err

    def do_login(self, arg):
        warn = ''
        if not arg:
            return 'ERROR: "set system login" needs arguments'
        m = re.fullmatch(r'(\S+)\s+((?:super-user)|(?:read-write)|'
                         r'(?:read-only))\s+((?:enable)|(?:disable))'
                         r'(?:\s+password\s+(\S+))?', arg)
        if not m:
            return ('NOTICE: Ignoring unknown command "set system login ' +
                    arg + '"')
        a_name = m.group(1)
        a_type = m.group(2)
        a_state = m.group(3)
        a_pass = m.group(4)
        account = self._switch.get_user_account(a_name)
        if account is None:
            return ('ERROR: Could not configure user account "' + a_name + '"'
                    ' (set system login ' + arg + ')')
        if account.get_is_default() is None:
            account.set_is_default(False)
        account.set_name(a_name)
        account.set_type(a_type)
        account.set_state(a_state)
        if a_pass:
            if re.fullmatch(r':[0123456789abcdefABCDEF]{82}:', a_pass):
                warn = ('WARN: Cannot convert encrypted password for user'
                        ' account "' + a_name + '"')
            else:
                account.set_password(a_pass)
        return warn


class EosSetBannerCommand(Switch.CmdInterpreter):

    """Commands starting with 'set banner'."""

    def __init__(self, switch):
        super().__init__()
        self._switch = switch

    def default(self, line):
        return 'NOTICE: Ignoring unknown command "set banner ' + line + '"'

    def do_login(self, arg):
        if not arg:
            return 'ERROR: "set banner login" needs an argument'
        err = self._check_quoting(arg)
        banner = arg.strip('"').replace('\\t', '\t').replace('\\n', '\n')
        self._switch.set_banner_login(banner, 'config')
        return err

    def do_motd(self, arg):
        if not arg:
            return 'ERROR: "set banner motd" needs an argument'
        err = self._check_quoting(arg)
        banner = arg.strip('"').replace('\\t', '\t').replace('\\n', '\n')
        self._switch.set_banner_motd(banner, 'config')
        return err


class EosSetTelnetCommand(Switch.CmdInterpreter):

    """Commands starting with 'set telnet'."""

    def __init__(self, switch):
        super().__init__()
        self._switch = switch

    def default(self, line):
        return 'NOTICE: Ignoring unknown command "set telnet ' + line + '"'

    def do_disable(self, line):
        if not line:
            return 'ERROR: "set telnet disable" needs an argument'
        err = ''
        if line == 'all':
            self._switch.set_telnet_inbound(False, 'config')
            self._switch.set_telnet_outbound(False, 'config')
        elif line == 'inbound':
            self._switch.set_telnet_inbound(False, 'config')
        elif line == 'outbound':
            self._switch.set_telnet_outbound(False, 'config')
        else:
            err = ('NOTICE: Ignoring unknown command "set telnet disable ' +
                   line + '"')
        return err

    def do_enable(self, line):
        if not line:
            return 'ERROR: "set telnet enable" needs an argument'
        err = ''
        if line == 'all':
            self._switch.set_telnet_inbound(True, 'config')
            self._switch.set_telnet_outbound(True, 'config')
        elif line == 'inbound':
            self._switch.set_telnet_inbound(True, 'config')
        elif line == 'outbound':
            self._switch.set_telnet_outbound(True, 'config')
        else:
            err = ('NOTICE: Ignoring unknown command "set telnet enable ' +
                   line + '"')
        return err


class EosSetSshCommand(Switch.CmdInterpreter):

    """Commands starting with 'set ssh'."""

    def __init__(self, switch):
        super().__init__()
        self._switch = switch

    def default(self, line):
        return 'NOTICE: Ignoring unknown command "set ssh ' + line + '"'

    def do_disabled(self, line):
        if line:
            return ('NOTICE: Ignoring unknown command "set ssh disabled ' +
                    line + '"')
        err = ''
        self._switch.set_ssh_inbound(False, 'config')
        return err

    def do_enabled(self, line):
        if line:
            return ('NOTICE: Ignoring unknown command "set ssh enabled ' +
                    line + '"')
        err = ''
        self._switch.set_ssh_inbound(True, 'config')
        return err


class EosSetSslCommand(Switch.CmdInterpreter):

    """Commands starting with 'set ssl'."""

    def __init__(self, switch):
        super().__init__()
        self._switch = switch

    def default(self, line):
        return 'NOTICE: Ignoring unknown command "set ssl ' + line + '"'

    def do_disabled(self, line):
        if line:
            return ('NOTICE: Ignoring unknown command "set ssl disabled ' +
                    line + '"')
        err = ''
        self._switch.set_ssl(False, 'config')
        return err

    def do_enabled(self, line):
        if line:
            return ('NOTICE: Ignoring unknown command "set ssl enabled ' +
                    line + '"')
        err = ''
        self._switch.set_ssl(True, 'config')
        return err


class EosSetWebviewCommand(Switch.CmdInterpreter):

    """Commands starting with 'set webview'."""

    def __init__(self, switch):
        super().__init__()
        self._switch = switch

    def default(self, line):
        return 'NOTICE: Ignoring unknown command "set webview ' + line + '"'

    def do_disable(self, line):
        if line:
            return ('NOTICE: Ignoring unknown command "set webview disable ' +
                    line + '"')
        self._switch.set_http(False, 'config')
        self._switch.set_http_secure(False, 'config')
        return ''

    def do_enable(self, line):
        if line and line != 'ssl-only':
            return ('NOTICE: Ignoring unknown command "set webview enable ' +
                    line + '"')
        if not line:
            self._switch.set_http(True, 'config')
        else:
            self._switch.set_http(False, 'config')
        if line and not self._switch.get_ssl():
            err = ('ERROR: Webview with SSL only enabled, but SSL disabled' +
                   ' (set webview enable ' + line + ')')
            err += ('\nERROR: Ignoring command "set webview enable ' + line +
                    '"')
            return err
        self._switch.set_http_secure(True, 'config')
        return ''


class EosSetIpCommand(Switch.CmdInterpreter):

    """Commands starting with 'set ip'."""

    def __init__(self, switch):
        super().__init__()
        self._set_ip_protocol = EosSetIpProtocolCommand(switch)
        self._switch = switch

    def default(self, line):
        return 'NOTICE: Ignoring unknown command "set ip ' + line + '"'

    def do_protocol(self, line):
        return self._set_ip_protocol.onecmd(line)

    def do_address(self, line):
        if not line:
            return 'ERROR: "set ip address" needs an IP address argument'
        err = ''
        ipre = r'(\d+\.\d+\.\d+\.\d+)'
        maskre = r'(?:\s+mask\s+' + ipre + ')?'
        gwre = r'(?:\s+gateway\s+' + ipre + ')?'
        m = re.fullmatch(ipre + maskre + gwre, line)
        if not m:
            return ('NOTICE: Ignoring unknown command "set ip address ' +
                    line + '"')
        if m.group(1):
            try:
                ip = ipaddress.IPv4Address(m.group(1))
            except:
                return ('ERROR: invalid IP address "' + m.group(1) +
                        '" in command "set ip address ' + line + '"' +
                        ', ignoring command')
        else:
            return ('NOTICE: Ignoring unknown command "set ip address ' +
                    line + '"')
        if m.group(2):
            try:
                mask = ipaddress.IPv4Address(m.group(2))
            except:
                return ('ERROR: invalid netmask "' + m.group(2) +
                        '" in command "set ip address ' + line + '"' +
                        ', ignoring command')
            try:
                iface = ipaddress.IPv4Interface(m.group(1) + '/' + m.group(2))
                mask = iface.with_netmask.split('/')[1]
            except:
                return ('ERROR: invalid IP/netmask "' + m.group(2) +
                        '" in command "set ip address ' + line + '"' +
                        ', ignoring command')
        else:
            mask = None
        if mask is None:
            if ip.packed[0] & 128 == 0:
                mask = ipaddress.IPv4Address('255.0.0.0')
            elif ip.packed[0] & 64 == 0:
                mask = ipaddress.IPv4Address('255.255.0.0')
            elif ip.packed[0] & 32 == 0:
                mask = ipaddress.IPv4Address('255.255.255.0')
            else:
                return ('ERROR: cannot determine netmask from IP address (' +
                        'set ip address ' + line + '), ignoring command')
        if m.group(3):
            try:
                gw = ipaddress.IPv4Address(m.group(3))
            except:
                return ('ERROR: invalid gateway IP "' + m.group(3) +
                        '" in command "set ip address ' + line + '"' +
                        ', ignoring command')
        else:
            gw = None
        if m.group(3) and not m.group(2):
            err = ('WARN: EOS does not support setting gateway without '
                   'specifying netmask (set ip address ' + line + ')')
        ret = self._switch.set_mgmt_ip(str(ip), 'config')
        if not ret:
            if err:
                err += '\n'
            err += ('ERROR: could not set management IP address "' + str(ip) +
                    '"')
        ret = self._switch.set_mgmt_mask(str(mask), 'config')
        if not ret:
            if err:
                err += '\n'
            err += ('ERROR: could not set management IP netmask "' +
                    str(mask) + '"')
        if gw:
            ret = self._switch.set_mgmt_gw(str(gw), 'config')
            if not ret:
                if err:
                    err += '\n'
                err += ('ERROR: could not set management gateway IP "' +
                        str(mask) + '"')
        return err


class EosSetIpProtocolCommand(Switch.CmdInterpreter):

    """Commands starting with 'set ip protocol'."""

    def __init__(self, switch):
        super().__init__()
        self._switch = switch

    def default(self, line):
        return ('NOTICE: Ignoring unknown command "set ip protocol ' + line +
                '"')

    def do_bootp(self, line):
        if line:
            return ('NOTICE: Ignoring unknown command "set ip protocol ' +
                    'bootp ' + line + '"')
        self._switch.set_mgmt_protocol('bootp', 'config')
        return ''

    def do_dhcp(self, line):
        if line:
            return ('NOTICE: Ignoring unknown command "set ip protocol dhcp ' +
                    line + '"')
        self._switch.set_mgmt_protocol('dhcp', 'config')
        return ''

    def do_none(self, line):
        if line:
            return ('NOTICE: Ignoring unknown command "set ip protocol none ' +
                    line + '"')
        self._switch.set_mgmt_protocol('none', 'config')
        return ''


class EosSetHostCommand(Switch.CmdInterpreter):

    """Commands starting with 'set host'."""

    def __init__(self, switch):
        super().__init__()
        self._switch = switch

    def default(self, line):
        return ('NOTICE: Ignoring unknown command "set host ' + line +
                '"')

    def do_vlan(self, line):
        if not line:
            return ('ERROR: "set host vlan" needs a VLAN number')
        try:
            vlan = int(line)
        except:
            return ('NOTICE: Ignoring unknown command "set host vlan ' + line +
                    '"')
        if not (0 < vlan < 4096):
            return ('ERROR: VLAN numbers must be in [1..4095] (set host ' +
                    'vlan ' + line + '), ignoring command')
        self._switch.set_mgmt_vlan(vlan, 'config')
        return ''


class EosSetLoggingCommand(Switch.CmdInterpreter):

    """Commands starting with 'set logging'."""

    def __init__(self, switch):
        super().__init__()
        self._switch = switch

    def default(self, line):
        return ('NOTICE: Ignoring unknown command "set logging ' + line +
                '"')

    def do_server(self, arg):
        # parse arg
        err = 'ERROR parsing "set logging server ' + arg + '"'
        token_types = [
            ('KEY_DESCR', 'descr'),
            ('KEY_FACILITY', 'facility'),
            ('KEY_IP', 'ip-addr'),
            ('KEY_PORT', 'port'),
            ('KEY_SEVERITY', 'severity'),
            ('KEY_STATE', 'state'),
            ('KEY_ENABLE', 'enable'),
            ('KEY_DISABLE', 'disable'),
            ('IP', r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'),
            ('PORT', r'\d{2,5}'),
            ('IDX_OR_SEV', '[1-8]'),
            ('FACILITY', 'local[0-7]'),
            ('DESCR', '["\'][^"\']*["\']'),
            ('WORD', r'\S+'),
            ('SPACE', r'\s+'),
        ]
        T = Tokenizer(token_types)
        idx = None
        attributes = {}
        pstate = 'read_index'
        expected = None
        for token in T.generate_tokens(arg):
            if token.t == 'SPACE':
                continue
            if ((pstate == 'read_index' and token.t != 'IDX_OR_SEV') or
                    pstate == 'read_key' and not token.t.startswith('KEY_') or
                    pstate == 'read_val' and token.t.startswith('KEY_')):
                return err
            if pstate == 'read_index' and token.t == 'IDX_OR_SEV':
                idx = token.v
                pstate = 'read_key'
            elif pstate == 'read_key':
                if token.t == 'KEY_DESCR':
                    pstate, expected = 'read_val', 'DESCR'
                elif token.t == 'KEY_FACILITY':
                    pstate, expected = 'read_val', 'FACILITY'
                elif token.t == 'KEY_IP':
                    pstate, expected = 'read_val', 'IP'
                elif token.t == 'KEY_PORT':
                    pstate, expected = 'read_val', 'PORT'
                elif token.t == 'KEY_SEVERITY':
                    pstate, expected = 'read_val', 'IDX_OR_SEV'
                elif token.t == 'KEY_STATE':
                    pstate, expected = 'read_key', 'EN_OR_DISABLE'
                elif token.t == 'KEY_ENABLE' or token.t == 'KEY_DISABLE':
                    attributes['state'] = token.v
                    pstate, expected = 'read_key', None
                else:
                    return err
            elif pstate == 'read_val':
                if (token.t != expected and not
                        ((expected == 'PORT' and token.t == 'IDX_OR_SEV') or
                         (expected == 'DESCR' and token.t == 'WORD'))):
                    return err
                if token.t == 'IP':
                    attributes['ip'] = token.v
                elif token.t == 'PORT':
                    attributes['port'] = token.v
                elif token.t == 'IDX_OR_SEV' and expected == 'PORT':
                    attributes['port'] = token.v
                elif token.t == 'FACILITY':
                    attributes['facility'] = token.v
                elif token.t == 'IDX_OR_SEV' and token.t == expected:
                    attributes['severity'] = token.v
                elif token.t == 'DESCR':
                    attributes['descr'] = token.v.strip('"\'')
                elif token.t == 'WORD' and expected == 'DESCR':
                    attributes['descr'] = token.v
                else:
                    return err
                pstate, expected = 'read_key', None
            else:
                return err
        if idx is not None:
            syslog_server = self._switch.get_syslog_server(idx)
            if not syslog_server:
                return ('ERROR: cannot configure syslog server "' + str(idx) +
                        '" (set logging server ' + arg + ')')
            syslog_server.update_attributes(attributes)
            syslog_server.set_is_configured(True)
        else:
            return err
        return ''


class EosSetSntpCommand(Switch.CmdInterpreter):

    """Commands starting with 'set sntp'."""

    def __init__(self, switch):
        super().__init__()
        self._switch = switch

    def default(self, line):
        return ('NOTICE: Ignoring unknown command "set sntp ' + line +
                '"')

    def do_server(self, line):
        if not line:
            return 'NOTICE: Ignoring unknown command "set sntp server"'
        attributes = {}
        keywords = {'key', 'precedence'}
        tok_lst = line.split()
        try:
            tok = tok_lst.pop(0)
            ipaddress.IPv4Address(tok)
        except:
            return ('NOTICE: Ignoring unknown command "set sntp server ' +
                    line + '"')
        attributes['ip'] = tok
        state = 'expect_keyword'
        val_type = None
        warn = ''
        for tok in tok_lst:
            if state == 'expect_keyword' and tok in keywords:
                state = 'expect_value'
                val_type = tok
            elif state == 'expect_value' and val_type is not None:
                if val_type == 'precedence':
                    try:
                        p = int(tok)
                    except:
                        return ('ERROR: SNTP server precedence must be an '
                                'integer (set sntp server ' + line + ')')
                    if not (1 <= p <= 10):
                        return ('ERROR: SNTP server precedence must be in '
                                '[1..10] (set sntp server ' + line + ')')
                    attributes[val_type] = p
                elif val_type == 'key':
                    warn = ('WARN: Ignoring SNTP server key (set sntp server' +
                            ' ' + line + ')')
                state = 'expect_keyword'
            else:
                return 'ERROR: Error parsing "set sntp server ' + line + '"'
        sntp_servers = self._switch.get_all_sntp_servers()
        found = False
        for sntp_srv in sntp_servers:
            if sntp_srv.get_ip() == attributes['ip']:
                found = True
                break
        if not found:
            sntp_srv = self._switch.get_sntp_server(len(sntp_servers))
        sntp_srv.update_attributes(attributes)
        sntp_srv.set_is_configured(True)
        return warn

    def do_client(self, line):
        if not line:
            return 'NOTICE: Ignoring unknown command "set sntp client"'
        if line in ('broadcast', 'disable', 'unicast'):
            self._switch.set_sntp_client(line, 'config')
        else:
            return ('NOTICE: Ignoring unknown command "set sntp client ' +
                    line + '"')
        return ''


class EosSetSummertimeCommand(Switch.CmdInterpreter):

    """Commands starting with 'set summertime'."""

    def __init__(self, switch):
        super().__init__()
        self._switch = switch

    def default(self, line):
        return ('NOTICE: Ignoring unknown command "set summertime ' + line +
                '"')

    def do_enable(self, line):
        if line:
            self._switch.set_tz_dst_name(line.strip("'"), 'config')
        self._switch.enable_tz_dst('config')
        return ''

    def do_disable(self, line):
        if line:
            self._switch.set_tz_dst_name(line.strip("'"), 'config')
        self._switch.disable_tz_dst('config')
        return ''

    def do_recurring(self, line):
        if not line:
            return 'ERROR: "set summertime recurring" needs arguments'
        date_re = (r'(first|second|third|fourth|last)\s+'
                   '(monday|tuesday|wednesday|thursday|friday|saturday|sunday)'
                   r'\s+(january|february|march|april|may|june|july|august|'
                   r'september|october|november|december)\s+(\d+):(\d+)')
        m = re.fullmatch(date_re + r'\s+' + date_re + r'\s+(\d+)', line,
                         re.IGNORECASE)
        if not m:
            return ('NOTICE: Ignoring unknown command "set summertime ' +
                    line + '"')
        self._switch.set_tz_dst_start(m.group(1), m.group(2), m.group(3),
                                      m.group(4), m.group(5), 'config')
        self._switch.set_tz_dst_end(m.group(6), m.group(7), m.group(8),
                                    m.group(9), m.group(10), 'config')
        self._switch.set_tz_dst_off_min(m.group(11), 'config')
        return ''


class EosSetRadiusCommand(Switch.CmdInterpreter):

    """Commands starting with 'set radius'."""

    def __init__(self, switch):
        super().__init__()
        self._switch = switch
        self._set_radius_interface = EosSetRadiusInterfaceCommand(switch)

    def default(self, line):
        return ('NOTICE: Ignoring unknown command "set radius ' + line +
                '"')

    def do_server(self, line):
        warn = ''
        if not line:
            return 'ERROR: "set radius server" needs additional arguments'
        RE = (r'(\d+)\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+)(?:\s+(\S+))?'
              r'(?:\s+realm\s+(management-access))')
        m = re.fullmatch(RE, line)
        if not m:
            return ('NOTICE: Ignoring unknown command "set radius server ' +
                    line + '"')
        index = m.group(1)
        ip = m.group(2)
        port = m.group(3)
        secret = m.group(4)
        realm = m.group(5)
        r = self._switch.get_radius_server(index)
        r.set_ip(ip)
        r.set_port(port)
        if secret:
            enc_secret = False
            if len(secret) == 84 and secret[0] == secret[83] == ':':
                is_hex = True
                for c in secret[1:-1]:
                    if c not in '0123456789ABCDEFabcdef':
                        is_hex = False
                        break
                if is_hex:
                    warn = ('WARN: Ignoring encrypted RADIUS secret (set'
                            ' radius server ' + line + ')')
                    enc_secret = True
            if not enc_secret:
                r.set_secret(secret)
        r.set_realm(realm)
        r.set_is_configured(True)
        return warn

    def do_disable(self, line):
        if line:
            return ('NOTICE: Ignoring unknown command "set radius disable' +
                    line + '"')
        self._switch.set_radius_mgmt_acc_enabled(False, 'config')
        return ''

    def do_enable(self, line):
        if line:
            return ('NOTICE: Ignoring unknown command "set radius enable' +
                    line + '"')
        self._switch.set_radius_mgmt_acc_enabled(True, 'config')
        return ''

    def do_interface(self, line):
        return self._set_radius_interface.onecmd(line)


class EosSetRadiusInterfaceCommand(Switch.CmdInterpreter):

    """Commands starting with 'set radius interface'."""

    def __init__(self, switch):
        super().__init__()
        self._switch = switch

    def default(self, line):
        return ('NOTICE: Ignoring unknown command "set radius interface ' +
                line + '"')

    def do_vlan(self, line):
        if not line:
            return 'ERROR: "set radius interface vlan" needs an argument'
        if len(line.split()) > 1:
            return ('NOTICE: Ignoring unknown command "set radius interface'
                    ' vlan' + line + '"')
        try:
            number = int(line)
        except:
            return ('ERROR: interface number must be an integer (set radius'
                    ' interface vlan ' + line + ')')
        if not (0 < number < 4096):
            return ('ERROR: interface number is no valid VLAN tag (set radius'
                    ' interface vlan ' + line + ')')
        self._switch.set_radius_interface(('vlan', number), 'config')
        return ''

    def do_loopback(self, line):
        if not line:
            return 'ERROR: "set radius interface loopback" needs an argument'
        if len(line.split()) > 1:
            return ('NOTICE: Ignoring unknown command "set radius interface'
                    ' vlan' + line + '"')
        try:
            number = int(line)
        except:
            return ('ERROR: interface number must be an integer (set radius'
                    ' interface loopback ' + line + ')')
        w = ''
        if not (0 <= number <= 8):
            w = ('WARN: interface number "' + line + '" is not valid for'
                 ' Loopback on C-Series (set radius interface loopback ' +
                 line + ')')
        self._switch.set_radius_interface(('loopback', number), 'config')
        return w


class EosSetTacacsCommand(Switch.CmdInterpreter):

    """Commands starting with 'set tacacs'."""

    def __init__(self, switch):
        super().__init__()
        self._switch = switch
        self._set_tacacs_interface = EosSetTacacsInterfaceCommand(switch)

    def default(self, line):
        return ('NOTICE: Ignoring unknown command "set tacacs ' + line +
                '"')

    def do_server(self, line):
        warn = ''
        if not line:
            return 'ERROR: "set tacacs server" needs additional arguments'
        RE = r'(\d+)\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+)(?:\s+(\S+))'
        m = re.fullmatch(RE, line)
        if not m:
            return ('NOTICE: Ignoring unknown command "set tacacs server ' +
                    line + '"')
        index = m.group(1)
        ip = m.group(2)
        port = m.group(3)
        secret = m.group(4)
        t = self._switch.get_tacacs_server(index)
        t.set_ip(ip)
        t.set_port(port)
        enc_secret = False
        if (len(secret) == 84 and secret[0] == secret[83] == ':' or
                len(secret) == 83 and secret[0] == ':'):
            is_hex = True
            for c in secret[1:84]:
                if c not in '0123456789ABCDEFabcdef':
                    is_hex = False
                    break
            if is_hex:
                warn = ('WARN: Ignoring encrypted TACACS+ secret (set'
                        ' tacacs server ' + line + ')')
                enc_secret = True
        if not enc_secret:
            t.set_secret(secret)
        t.set_is_configured(True)
        return warn

    def do_disable(self, line):
        if line:
            return ('NOTICE: Ignoring unknown command "set tacacs disable' +
                    line + '"')
        self._switch.set_tacacs_enabled(False, 'config')
        return ''

    def do_enable(self, line):
        if line:
            return ('NOTICE: Ignoring unknown command "set tacacs enable' +
                    line + '"')
        self._switch.set_tacacs_enabled(True, 'config')
        return ''

    def do_interface(self, line):
        return self._set_tacacs_interface.onecmd(line)


class EosSetTacacsInterfaceCommand(Switch.CmdInterpreter):

    """Commands starting with 'set tacacs interface'."""

    def __init__(self, switch):
        super().__init__()
        self._switch = switch

    def default(self, line):
        return ('NOTICE: Ignoring unknown command "set tacacs interface' +
                line + '"')

    def do_vlan(self, line):
        if not line:
            return 'ERROR: "set tacacs interface vlan" needs an argument'
        if len(line.split()) > 1:
            return ('NOTICE: Ignoring unknown command "set tacacs interface'
                    ' vlan' + line + '"')
        try:
            number = int(line)
        except:
            return ('ERROR: interface number must be an integer (set tacacs'
                    ' interface vlan ' + line + ')')
        if not (0 < number < 4096):
            return ('ERROR: interface number is no valid VLAN tag (set tacacs'
                    ' interface vlan ' + line + ')')
        self._switch.set_tacacs_interface(('vlan', number), 'config')
        return ''

    def do_loopback(self, line):
        if not line:
            return 'ERROR: "set tacacs interface loopback" needs an argument'
        if len(line.split()) > 1:
            return ('NOTICE: Ignoring unknown command "set tacacs interface'
                    ' vlan' + line + '"')
        try:
            number = int(line)
        except:
            return ('ERROR: interface number must be an integer (set tacacs'
                    ' interface loopback ' + line + ')')
        w = ''
        if not (0 <= number <= 8):
            w = ('WARN: interface number "' + line + '" is not valid for'
                 ' Loopback on C-Series (set tacacs interface loopback ' +
                 line + ')')
        self._switch.set_tacacs_interface(('loopback', number), 'config')
        return w


class EosSetSnmpCommand(Switch.CmdInterpreter):

    """Commands starting with 'set snmp'."""

    def __init__(self, switch):
        super().__init__()
        self._switch = switch

    def default(self, line):
        return ('NOTICE: Ignoring unknown command "set snmp ' + line + '"')

    def do_targetparams(self, line):
        if not line:
            return 'ERROR: "set snmp targetparams" needs arguments'
        m = re.fullmatch(r'"?(\S+)"?\s+user\s+(\S+)\s+security-model\s+'
                         r'((?:v1)|(?:v2c))\s+message-processing\s+'
                         r'((?:v1)|(?:v2c))',
                         line)
        if not m:
            return ('NOTICE: Ignoring unknown command "set snmp'
                    ' targetparams ' + line + '"')
        p_name = m.group(1)
        p_user = m.group(2)
        p_sec = m.group(3)
        p_msg = m.group(4)
        target_params = self._switch.get_snmp_target_params(p_name)
        if target_params is None:
            return ('ERROR: could not configure SNMP target parameters "' +
                    p_name + '" (set snmp targetparams ' + line + ')')
        target_params.set_user(p_user)
        target_params.set_security_model(p_sec)
        target_params.set_message_processing(p_msg)
        return ''

    def do_targetaddr(self, line):
        if not line:
            return 'ERROR: "set snmp targetaddr" needs arguments'
        m = re.fullmatch(r'"?(\S+)"?\s+(\d+\.\d+\.\d+\.\d+)\s+param\s+(\S+)',
                         line)
        if not m:
            return ('NOTICE: Ignoring unknown command "set snmp'
                    ' targetaddr ' + line + '"')
        t_name = m.group(1)
        t_ip = m.group(2)
        t_param = m.group(3)
        target_addr = self._switch.get_snmp_target_addr(t_name)
        if target_addr is None:
            return ('ERROR: could not configure SNMP target address "' +
                    t_name + '" (set snmp targetaddr ' + line + ')')
        target_addr.set_ip(t_ip)
        target_addr.set_params(t_param)
        return ''


class EosClearCommand(Switch.CmdInterpreter):

    """Commands starting with 'clear'."""

    def __init__(self, switch):
        super().__init__()
        self._clear_vlan = EosClearVlanCommand(switch)
        self._clear_port = EosClearPortCommand(switch)
        self._clear_system = EosClearSystemCommand(switch)

    def default(self, line):
        return 'NOTICE: Ignoring unknown command "clear ' + line + '"'

    def do_vlan(self, arg):
        return self._clear_vlan.onecmd(arg)

    def do_port(self, arg):
        return self._clear_port.onecmd(arg)

    def do_system(self, arg):
        return self._clear_system.onecmd(arg)


class EosSetCommand(Switch.CmdInterpreter):

    """Commands starting with 'set'."""

    def __init__(self, switch):
        super().__init__()
        self._set_port = EosSetPortCommand(switch)
        self._set_vlan = EosSetVlanCommand(switch)
        self._set_lacp = EosSetLacpCommand(switch)
        self._set_spantree = EosSetSpantreeCommand(switch)
        self._set_system = EosSetSystemCommand(switch)
        self._set_banner = EosSetBannerCommand(switch)
        self._set_telnet = EosSetTelnetCommand(switch)
        self._set_ssh = EosSetSshCommand(switch)
        self._set_webview = EosSetWebviewCommand(switch)
        self._set_ssl = EosSetSslCommand(switch)
        self._set_ip = EosSetIpCommand(switch)
        self._set_host = EosSetHostCommand(switch)
        self._set_logging = EosSetLoggingCommand(switch)
        self._set_sntp = EosSetSntpCommand(switch)
        self._set_summertime = EosSetSummertimeCommand(switch)
        self._set_radius = EosSetRadiusCommand(switch)
        self._set_tacacs = EosSetTacacsCommand(switch)
        self._set_snmp = EosSetSnmpCommand(switch)
        self._switch = switch

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

    def do_prompt(self, arg):
        err = ''
        if not arg:
            self._switch.set_prompt(None, 'config')
            return err
        if (len(arg.split()) != 1 and
                not (arg.startswith('"') and arg.rstrip().endswith('"'))):
            err += 'WARN: EOS prompts containing spaces must be enclosed in'
            err += ' double quotes'
        self._switch.set_prompt(arg.strip('"'), 'config')
        return err

    def do_system(self, arg):
        return self._set_system.onecmd(arg)

    def do_banner(self, arg):
        return self._set_banner.onecmd(arg)

    def do_telnet(self, arg):
        return self._set_telnet.onecmd(arg)

    def do_ssh(self, arg):
        return self._set_ssh.onecmd(arg)

    def do_webview(self, arg):
        return self._set_webview.onecmd(arg)

    def do_ssl(self, arg):
        return self._set_ssl.onecmd(arg)

    def do_ip(self, arg):
        return self._set_ip.onecmd(arg)

    def do_host(self, arg):
        return self._set_host.onecmd(arg)

    def do_logout(self, arg):
        if not arg:
            return 'ERROR: "set logout" command needs a TIMEOUT argument'
        try:
            timeout = int(arg)
        except:
            return 'NOTICE: Ignoring unknown command "set logout ' + arg + '"'
        if not (0 <= timeout <= 160):
            return ('ERROR: Ignoring invalid idle timeout "' + str(timeout) +
                    '" from command "set logout ' + arg + '"')
        self._switch.set_idle_timer(timeout, 'config')
        return ''

    def do_logging(self, arg):
        return self._set_logging.onecmd(arg)

    def do_sntp(self, arg):
        return self._set_sntp.onecmd(arg)

    def do_timezone(self, arg):
        if not arg:
            return 'ERROR: "set timezone" command needs a NAME argument'
        m = re.fullmatch(r'(\S+)\s*([+-]?\d+)?\s*(\d+)?', arg)
        if not m:
            return ('NOTICE: Ignoring unknown command "set timezone ' + arg +
                    '"')
        tz_name, tz_off_h, tz_off_min = m.group(1), m.group(2), m.group(3)
        tz_name = tz_name.strip("'")
        if tz_off_h is not None:
            try:
                tz_off_h = int(tz_off_h)
            except:
                return ('ERROR: Timezone offset hours must be an integer (' +
                        arg + ')')
        else:
            tz_off_h = 0
        if tz_off_min is not None:
            try:
                tz_off_min = int(tz_off_min)
            except:
                return ('ERROR: Timezone offset minutes must be an integer (' +
                        arg + ')')
        else:
            tz_off_min = 0
        self._switch.set_tz_name(tz_name, 'config')
        self._switch.set_tz_off_min(tz_off_h * 60 + tz_off_min, 'config')
        return ''

    def do_summertime(self, arg):
        return self._set_summertime.onecmd(arg)

    def do_radius(self, arg):
        return self._set_radius.onecmd(arg)

    def do_tacacs(self, arg):
        return self._set_tacacs.onecmd(arg)

    def do_snmp(self, arg):
        return self._set_snmp.onecmd(arg)


class EosCommand(Switch.CmdInterpreter):

    """Interpret first token of all supported EOS commands."""

    def __init__(self, switch):
        super().__init__()
        self._comments = ['#', '!']
        self._set = EosSetCommand(switch)
        self._clear = EosClearCommand(switch)
        self._ip = EosIpCommand(self._state, switch)
        self._no = EosNoCommand(self._state, switch)
        self._switch = switch

    def default(self, line):
        # Hyphenated commands need to be caught here.
        if line.startswith('access-list'):
            result = self._do_access_list(line.split()[1:])
            if result:
                result += ' "' + line + '"'
            return result
        # Comments.
        if self._is_comment(line):
            return 'INFO: Ignoring comment "' + line + '"'
        # Unknown lines.
        return 'NOTICE: Ignoring unknown command "' + line + '"'

    def do_begin(self, arg):
        return self._ignore_word('begin', arg)

    def do_end(self, arg):
        return self._ignore_word('end', arg)

    def _ignore_word(self, word, arg):
        if arg:
            return ('NOTICE: Ignoring unknown command "' + word + ' ' +
                    arg + '"')
        return ''

    def do_set(self, arg):
        return self._set.onecmd(arg)

    def do_clear(self, arg):
        return self._clear.onecmd(arg)

    def do_router(self, arg):
        if arg:
            return 'NOTICE: Ignoring unknown command "router ' + arg + '"'
        if self._state:
            return 'INFO: "router" command inside router mode'
        self._state.append('router')
        return ''

    def do_exit(self, arg):
        if arg:
            return 'ERROR: exit takes no arguments ("exit ' + arg + '")'
        if not self._state:
            return 'INFO: "exit" command outside of router mode'
        self._state.pop()
        return ''

    def do_enable(self, arg):
        if arg:
            return 'NOTICE: Ignoring unknown command "enable ' + arg + '"'
        if not self._state or 'router' not in self._state:
            return 'INFO: "enable" command outside of router mode'
        self._state.append('enable')
        return ''

    def do_configure(self, arg):
        # unknown commands if arguments different from terminal given
        if arg and arg != 'terminal':
            return 'NOTICE: Ignoring unknown command "configure ' + arg + '"'
        if not self._state or 'enable' not in self._state:
            return 'INFO: "configure" command outside of router enable mode'
        self._state.append('configure')
        return ''

    def _do_access_list(self, token_list):
        if not token_list:
            return 'ERROR: "access-list" command without arguments'
        acl_type = token_list[0]
        """Numbered ACLs only, or "access-list interface" command."""
        if acl_type == 'interface':
            token_list.pop(0)
            return self._do_access_list_interface(token_list)
        if not ACL.is_supported_type(acl_type):
            return 'NOTICE: Ignoring unknown command'

        warn = ''
        if not self._state or 'configure' not in self._state:
            warn = ('INFO: "access-list" command outside router configuration'
                    ' mode')
        try:
            new_acl = EosNumberedAclLineParser.create_acl(token_list)
        except EosAclParseError as parse_err:
            return str(parse_err)
        surplus_params = new_acl.get_surplus_params()
        if surplus_params:
            if warn:
                warn += '\n'
            warn += 'WARN: Ignoring "' + surplus_params + '" in'
        number = new_acl.get_number()

        acl = self._switch.get_acl_by_number(number)
        if acl is None:
            err = self._switch.add_complete_acl(new_acl)
            acl = self._switch.get_acl_by_number(number)
            if not acl:
                return ('ERROR: Could not create ACL "' + str(number) + '"' +
                        ' (reason: "' + err + '")')
        else:
            acl.add_ace(new_acl.get_entries()[0])
        self._leave_interface_mode()
        return warn

    def _do_access_list_interface(self, token_list):
        warn = ''
        if not token_list:
            return 'ERROR: "access-list interface" needs arguments'
        if not self._state or 'configure' not in self._state:
            warn = ('INFO: "access-list interface" outside router '
                    'configuration mode')
        token_count = len(token_list)
        if not (1 < token_count <= 5):
            return ('ERROR: Illegal "access-list interface" command (' +
                    'access-list interface ' + ' '.join(token_list) + ')')
        acl_id = port_string = direction = sequence = sequence_nr = None
        acl_id, port_string = token_list[0], token_list[1]
        if token_count == 3:
            direction = token_list[2]
        elif token_count == 4:
            sequence, sequence_nr = token_list[2], token_list[3]
        elif token_count == 5:
            direction = token_list[2]
            sequence, sequence_nr = token_list[3], token_list[4]
        if direction and direction != 'in':
            return ('ERROR: ACL must be applied inbound, not "' +
                    str(direction) + '"')
        if sequence and sequence != 'sequence':
            return ('ERROR: Expected keyword "sequence", but got "' +
                    str(sequence) + '"')
        if sequence_nr:
            try:
                sequence_nr = int(sequence_nr)
            except:
                return ('ERROR: Sequence number must be an integer '
                        '(access-list interface)')
            warn += '\nWARN: Ignoring ACL sequence number' \
                    ' (access-list interface)'
        try:
            acl_nr = int(acl_id)
            acl_id = acl_nr
        except:
            pass
        port_list = self._switch.get_ports_by_name(port_string)
        if not port_list:
            return ('ERROR: Port ' + port_string + ' not found '
                    '(access-list interface ' + str(acl_id) +
                    str(port_string) + ')')
        for p in port_list:
            p.add_ipv4_acl_in(acl_id, 'config')
        self._leave_interface_mode()
        return warn

    def _split_int_name(self, name):
        prefix, number = name[:4].lower(), name[4:]
        if (prefix != 'vlan' and prefix != 'loopback') or not number:
            return None
        try:
            number = int(number)
        except:
            return None
        if 0 < number < 4095:
            return [prefix, str(number)]
        return None

    def _leave_interface_mode(self):
        """Leave interface configuration mode."""
        if not self._state:
            return
        current_interface = self._state[-1]
        if (isinstance(current_interface, str) and
                current_interface.startswith('interface vlan ')):
            self._state.pop()

    def do_interface(self, arg):
        """Save interface on state stack, create VLAN if non-existent."""
        warn = ''
        if not arg:
            return ('ERROR: "interface" command needs an argument')
        if not isinstance(arg, str):
            return ('ERROR: "interface" command needs string as argument')
        if not arg.startswith('vlan') and not arg.startswith('loopback'):
            return 'NOTICE: Ignoring unknown command "interface ' + arg + '"'
        if not self._state or 'configure' not in self._state:
            warn = 'INFO: "interface" command outside router config mode'
        arg_lst = arg.split()
        if len(arg_lst) == 1:
            arg_lst = self._split_int_name(arg)
        if not arg_lst:
            return ('ERROR: Unknown interface "' + arg + '"')
        # SVI
        if arg_lst[0] == 'vlan':
            vid = arg_lst[1]
            try:
                vid = int(vid)
            except:
                return ('ERROR: VLAN ID must be an integer (interface ' +
                        arg + ')')
            if not (0 < vid < 4095):
                return ('ERROR: VLAN ID must be in [1,4095] (interface ' +
                        arg + ')')
            vlan = self._switch.get_vlan(tag=vid)
            # create VLAN if it does not exist yet
            if not vlan:
                vlan = VLAN.VLAN(tag=vid)
                self._switch.add_vlan(vlan)
            # EOS SVI are shutdown by default
            vlan.set_svi_shutdown(True)
        # Loopback
        elif arg_lst[0] == 'loopback':
            number = arg_lst[1]
            try:
                number = int(number)
            except:
                return ('ERROR: Loopback ID must be an integer (interface ' +
                        arg + ')')
            if not (0 <= number <= 7):
                return ('ERROR: Loopback ID must be in [0..7] (interface ' +
                        arg + ')')
            self._switch.add_loopback(number)
            # EOS Loopback Interfaces are shutdown by default
            lo = self._switch.get_loopback(number)
            lo.set_svi_shutdown(True)
        self._leave_interface_mode()
        self._state.append('interface ' + ' '.join(arg_lst))
        return warn

    def do_ip(self, arg):
        result = self._ip.onecmd(arg)
        return result

    def do_shutdown(self, arg):
        if arg:
            return 'NOTICE: Ignoring unknown command "shutdown ' + arg + '"'
        # shutdown needs an interface
        if not self._state:
            return 'ERROR: "shutdown" command ouside router interface'
        # check for valid interface
        interface = self._state[-1]
        intf = _parse_interface(interface)
        if intf is None:
            return ('ERROR: "shutdown" inside unknown interface "' +
                    str(interface) + '" [interface parse error]')
        iftype, ifnumber = intf
        if iftype == 'vlan':
            ifhandle = self._switch.get_vlan(tag=ifnumber)
            if not ifhandle:
                return ('ERROR: "shutdown" inside non-existing interface'
                        ' VLAN ' + str(ifnumber))
        elif iftype == 'loopback':
            ifhandle = self._switch.get_loopback(ifnumber)
            if not ifhandle:
                return ('ERROR: "shutdown" inside non-existing interface'
                        ' Loopback ' + str(ifnumber))
        else:
            return ('ERROR: "shutdown" inside unknown interface "' +
                    iftype + str(ifnumber) + '"')
        ifhandle.set_svi_shutdown(True)

    def do_no(self, arg):
        result = self._no.onecmd(arg)
        return result


class EosNoCommand(Switch.CmdInterpreter):

    """Commands (in router config mode) starting with 'no'."""

    def __init__(self, state, switch):
        super().__init__()
        self._state = state
        self._switch = switch
        self._ip = EosNoIpCommand(self._state, switch)

    def default(self, line):
        return 'NOTICE: Ignoring unknown command "no ' + line + '"'

    def do_shutdown(self, arg):
        if arg:
            return 'NOTICE: Ignoring unknown command "no shutdown ' + arg + '"'
        # shutdown needs an interface
        if not self._state:
            return 'ERROR: "no shutdown" command ouside router interface'
        # check for valid interface
        interface = self._state[-1]
        intf = _parse_interface(interface)
        if intf is None:
            return ('ERROR: "no shutdown" inside unknown interface "' +
                    str(interface) + '" [interface parse error]')
        iftype, ifnumber = intf
        if iftype == 'vlan':
            ifhandle = self._switch.get_vlan(tag=ifnumber)
            if not ifhandle:
                return ('ERROR: "no shutdown" inside non-existing interface'
                        ' VLAN ' + str(ifnumber))
        elif iftype == 'loopback':
            ifhandle = self._switch.get_loopback(ifnumber)
            if not ifhandle:
                return ('ERROR: "no shutdown" inside non-existing interface'
                        ' Loopback ' + str(ifnumber))
        else:
            return ('ERROR: "no shutdown" inside unknown interface "' +
                    iftype + str(ifnumber) + '"')
        ifhandle.set_svi_shutdown(False)

    def do_ip(self, arg):
        return self._ip.onecmd(arg)


class EosNoIpCommand(Switch.CmdInterpreter):

    """Commands (in router config mode) starting with 'no'."""

    def __init__(self, state, switch):
        super().__init__()
        self._state = state
        self._switch = switch

    def default(self, line):
        return 'NOTICE: Ignoring unknown command "no ip ' + line + '"'

    def do_routing(self, line):
        if line:
            return ('NOTICE: Ignoring unknown command "no ip routing ' +
                    line + '"')
        self._switch.disable_ipv4_routing()
        return ''


class EosNumberedAclLineParser:

    @staticmethod
    def create_acl(token_list):
        _std_acl_range = range(1, 100)
        _ext_acl_range = range(100, 400)
        acl_type = token_list.pop(0)
        try:
            acl_number = int(acl_type)
        except:
            raise(EosAclParseError('ERROR: Only numbered ACLs supported'))
        if acl_number not in _std_acl_range \
                and acl_number not in _ext_acl_range:
            raise(EosAclParseError('ERROR: ACL numbers in ' +
                                   str(_std_acl_range) + ' and ' +
                                   str(_ext_acl_range) + ' supported'))
        acl = ACL(number=acl_number)
        if not token_list:
            raise(EosAclParseError('ERROR: Empty ACE configuration line'))
        try:
            if acl_number in _std_acl_range:
                ace = EosNumberedAclLineParser._create_std_ace(token_list)
            else:
                ace = EosNumberedAclLineParser._create_ext_ace(token_list)
        except:
            raise
        if token_list:
            acl.set_surplus_params(' '.join(token_list))
        acl.add_ace(ace)
        return acl

    @staticmethod
    def _create_std_ace(token_list):
        action = token_list.pop(0)
        if action not in ACE._ALLOWED_ACTIONS:
            raise(EosAclParseError('ERROR: Invalid ACE action'))
        try:
            source = \
                EosNumberedAclLineParser._handle_address_definition(token_list)
        except:
            raise
        ace = Standard_ACE(action=action)
        ace.set_source(source['addr'])
        ace.set_source_mask(source['mask'])
        return ace

    @staticmethod
    def _create_ext_ace(token_list):
        if len(token_list) < 4:
            raise(EosAclParseError('ERROR: Extended ACEs need protocol, source'
                                   ' and destination'))
        action = token_list.pop(0)
        if action not in ACE._ALLOWED_ACTIONS:
            raise(EosAclParseError('ERROR: Invalid ACE action'))
        ace = ACE(action=action)
        protocol = token_list[0]
        if ACE.validate_protocol_desc(protocol) == -1:
            raise(EosAclParseError('ERROR: Unsupported ACE protocol'))
        ace.set_protocol(token_list.pop(0))
        try:
            source = \
                EosNumberedAclLineParser._handle_address_definition(token_list)
        except EosAclParseError as errMsg:
            raise EosAclParseError('src: ' + str(errMsg))
        ace.set_source(source['addr'])
        ace.set_source_mask(source['mask'])
        if 'op' in source:
            ace.set_source_op(source['op'])
            ace.set_source_port(source['port'])
        try:
            dest = \
                EosNumberedAclLineParser._handle_address_definition(token_list)
        except EosAclParseError as errMsg:
            raise EosAclParseError('dest: ' + str(errMsg))
        ace.set_dest(dest['addr'])
        ace.set_dest_mask(dest['mask'])
        if 'op' in dest:
            ace.set_dest_op(dest['op'])
            ace.set_dest_port(dest['port'])
        return ace

    @staticmethod
    def _handle_address_definition(token_list):
        address_definition = {}
        if not token_list:
            raise(EosAclParseError('ERROR: Address definition missing in ACE '
                                   'config'))
        address = token_list.pop(0)
        if ACE.is_valid_ip_address(address):
            address_definition['addr'] = address
            mask = '0.0.0.0'
            if token_list:
                mask = token_list[0]
                if ACE.is_valid_ip_address(mask):
                    token_list.pop(0)
            address_definition['mask'] = mask
        elif address == 'host':
            address = None
            if token_list:
                address = token_list[0]
            if not address or not ACE.is_valid_ip_address(address):
                raise(EosAclParseError('ERROR: Missing address parameter in '
                                       'ACE config'))
            token_list.pop(0)
            address_definition['addr'] = address
            address_definition['mask'] = '0.0.0.0'
        elif address == 'any':
            address_definition['addr'] = '0.0.0.0'
            address_definition['mask'] = '255.255.255.255'
        else:
            raise(EosAclParseError('ERROR: Invalid address in ACE config'))
        if token_list:
            op = token_list[0]
            if op in ACE._ALLOWED_OPS:
                address_definition['op'] = token_list.pop(0)
                if token_list:
                    port = token_list[0]
                    if not ACE._is_port_number(port):
                        raise(EosAclParseError('ERROR: Invalid port definition'
                                               ' in ACE config'))
                    address_definition['port'] = token_list.pop(0)
                else:
                    raise(EosAclParseError('ERROR: Missing port definition'
                                           ' in ACE config'))
        return address_definition


class EosAclParseError(Exception):
    pass

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
