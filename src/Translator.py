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

# Copyright 2014-2016 Extreme Networks, Inc.  All rights reserved.
# Use is subject to license terms.

# This file is part of e2x (translate EOS switch configuration to ExtremeXOS)

"""This file handles translation of command lines in interactive mode."""

import re


class Translation:

    def __init__(self, hint='', eos='', xos=''):
        self.hint = hint
        self.eos = eos
        self.xos = xos

    def get_hint(self):
        return self.hint

    def set_hint(self, to):
        self.hint = to

    def get_eos(self):
        return self.eos

    def get_xos(self):
        return self.xos

    def set_xos(self, to):
        self.xos = to


class PatternReplacement:
    def __init__(self, pattern, replacement, hint=''):
        self.pattern = pattern
        self.replacement = replacement
        self.hint = hint


class Translator:

    PATTERN_IPV4 = r'\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}'

    def __init__(self, pattern_replacements=None):
        if pattern_replacements:
            self.pattern_replacements = pattern_replacements
        else:
            pat_repl_lst = (
                (r'show switch (\d+)', r'show slot \1', ''),
                ('show switch', 'show stacking\nshow slot', ''),
                ('show (ip )?arp', r'show iparp', ''),
                ('show ip arp vlan (\d+)',
                 r'show iparp vlan <NAME_OF_VLAN_WITH_TAG_\1>',
                 ''),
                ('show ip route connected', 'show iproute origin direct', ''),
                ('show ip route static', 'show iproute origin static', ''),
                ('show ip route ospf', 'show iproute origin ospf', ''),
                ('show ip route rip', 'show iproute origin rip', ''),
                ('show ip route summary', 'show iproute origin summary', ''),
                ('show ip route', 'show iproute', ''),
                (r'show ip interface vlan *(\d+)',
                 r'show ipconfig vlan <VLAN_NAME_WITH_TAG_\1>',
                 ''),
                (r'show ip interface loopback *(\d+)',
                 r'show ipconfig vlan <LOOPBACK_\1_VLAN_NAME>',
                 ''),
                ('show ip interface', 'show ipconfig', ''),
                ('reset', 'reboot', ''),
                (r'reset (\d+)', r'reboot slot \1', ''),
                ('set telnet (enable|disable) (all|inbound)',
                 r'\1 telnet',
                 ''),
                ('set telnet (enable|disable) outbound',
                 '',
                 'Outbound telnet cannot be disabled on XOS'
                 ' (always enabled)'),
                ('show telnet', 'show management | include Telnet', ''),
                ('set ssh (enable|disable)d', r'\1 ssh2', ''),
                ('show ssh', r'show management | include SSH', ''),
                ('show webview',
                 'show management | include Web\nshow ssl',
                 ''),
                ('show ssl', 'show ssl', ''),
                ('set ip address (' + Translator.PATTERN_IPV4 + ') mask (' +
                 Translator.PATTERN_IPV4 + ') gateway (' +
                 Translator.PATTERN_IPV4 + ')',
                 r'configure vlan Default ipaddress \1 \2'
                 '\nconfigure iproute add default \\3',
                 ''),
                ('set ip address (' + Translator.PATTERN_IPV4 + ') mask (' +
                 Translator.PATTERN_IPV4 + ')',
                 r'configure vlan Default ipaddress \1 \2',
                 ''),
                ('set ip address (' + Translator.PATTERN_IPV4 + ')',
                 r'configure vlan Default ipaddress \1',
                 ''),
                ('show ip address', 'show vlan', ''),
                ('show config all', 'show configuration detail', ''),
                (r'show config all (\S+)',
                 r'show configuration detail \1',
                 'Section names may differ'),
                ('show config', 'show configuration', ''),
                ('show config (\S+)',
                 r'show configuration \1',
                 'Section names may differ'),
                ('save config', r'save configuration', ''),
                ('set logging server 1 ip-addr (' + Translator.PATTERN_IPV4 +
                 ') severity 6 state enable',
                 r'configure log target syslog \1 severity notice only',
                 ''),
                ('show logging server',
                 'show log configuration target syslog',
                 ''),
                (r'set port vlan \S+ (\d+)( modify-egress)?',
                 r'configure vlan <VLAN_WITH_TAG_\1> add ports <PORTSTRING>',
                 'Untagged ingress and egress are always the same on XOS'),
                ('show port vlan( \S+)?',
                 'show ports [<PORTSTRING>] information detail | include'
                 ' "(^Port|(Internal|802.1Q) Tag)"',
                 ''),
                ('show vlan portinfo( port \S+)',
                 'show ports [<PORTSTRING>] information detail | include'
                 ' "(^Port|' '(Internal|802.1Q) Tag)"',
                 ''),
                ('show vlan portinfo',
                 'show ports information detail | include'
                 ' "(^Port|(Internal|802.1Q) Tag)"',
                 ''),
                (r'show vlan (static )?(\d+)', r'show vlan tag \2', ''),
                ('show vlan( static)?', 'show vlan detail', ''),
                (r'show port status( \S+)?',
                 'show ports [<PORTSTRING>] no-refresh',
                 ''),
                (r'show port negotiation( \S+)?',
                 'show ports [<PORTSTRING>] configuration no-refresh',
                 ''),
                (r'set port broadcast \S+ (\d+)',
                 'configure ports <PORTSTRING> rate-limit flood'
                 r' broadcast \1',
                 ''),
                (r'show port broadcast( \S+)?',
                 'show ports [<PORTSTRING>] rate-limit flood no-refresh',
                 ''),
                (r'set port trap \S+ (enable|disable)',
                 r'\1 snmp traps port-up-down ports <PORTSTRING>',
                 ''),
                (r'show port trap( \S+)?',
                 'show ports [<PORTSTRING>] information detail |'
                 ' include (^Port|Link up/down)',
                 ''),
                ('show radius', 'show radius', ''),
                ('show banner motd', 'show banner after-login', ''),
                ('show banner login', 'show banner before-login', ''),
                ('copy tftp://(' + Translator.PATTERN_IPV4 + r')/([-\w./]+)'
                 ' system:image',
                 r'download image \1 \2 vr VR-Default {primary|secondary}',
                 ''),
                ('dir', 'show version image\nls', ''),
                (r'set boot system [-\w./]+',
                 'use image partition {primary|secondary}',
                 ''),
                (r'set logout ([1-9]\d*)',
                 'configure idletimeout \\1\nenable idletimeout',
                 ''),
                ('set logout 0', 'disable idletimeout', ''),
                ('show logout', 'show management | include "CLI idle"', ''),
                (r'set system login (\w+) (?:super-user|read-write) enable'
                 r' password (\w+)',
                 r'create account admin \1 \2',
                 ''),
                (r'set system login (\w+) (?:super-user|read-write) enable',
                 r'create account admin \1',
                 'Password is set interactively'),
                (r'set system login (\w+) (?:super-user|read-write) disable'
                 r' password (\w+)',
                 'create account admin \\1 \\2\ndisable account \\1',
                 ''),
                (r'set system login (\w+) (?:super-user|read-write) disable',
                 'create account admin \\1\ndisable account \\1',
                 'Password is set interactively'),
                (r'set system login (\w+) read-only enable'
                 r' password (\w+)',
                 r'create account user \1 \2',
                 ''),
                (r'set system login (\w+) read-only enable',
                 r'create account user \1',
                 'Password is set interactively'),
                (r'set system login (\w+) read-only disable'
                 r' password (\w+)',
                 'create account user \\1 \\2\ndisable account \\1',
                 ''),
                (r'set system login (\w+) read-only disable',
                 'create account user \\1\ndisable account \\1',
                 'Password is set interactively'),
                (r'clear system login (\S+)', r'delete account \1', ''),
                ('show system login', 'show accounts', ''),
                ('clear config',
                 'unconfigure switch',
                 'Deletes all ip-addresses except address of management port'),
                ('clear config all',
                 'unconfigure switch all',
                 'All ip-addresses are deleted'),
                ('clear ip address', 'unconfigure vlan Default ipaddress', ''),
                ('set ip protocol dhcp', 'enable dhcp vlan Default', ''),
                ('show sntp', 'show sntp-client', ''),
                ('show time', 'show switch | include "Current Time"', ''),
                ('show summertime', 'show switch | include "DST"', ''),
                ('show version',
                 'show version\nshow switch | include "System Type:"',
                 ''),
                ('show support', 'show tech-support', ''),
                ('set sntp server ' + '(' + Translator.PATTERN_IPV4 + ')'
                 r'( precedence (\d\d?))?',
                 'configure sntp-client {primary|secondary}'
                 r' \1 vr VR-Default',
                 ''),
                ('set sntp client disable', 'disable sntp-client', ''),
                ('set sntp client broadcast',
                 'enable sntp-client',
                 'XOS uses unicast mode if an SNTP server is configured'),
                ('set sntp client unicast',
                 'enable sntp-client',
                 'XOS uses broadcast mode if no SNTP server is configured'),
                (r'set port (enable|disable) \S+',
                 r'\1 ports <PORTSTRING>',
                 ''),
                ('show port egress( \S+)?',
                 'show ports [<PORTSTRING>] information detail |'
                 ' include (^Port:|Tag =)',
                 ''),
                ('ip route 0.0.0.0 0.0.0.0 (' + Translator.PATTERN_IPV4 + ')',
                 r'configure iproute add default \1 vr VR-Default',
                 ''),
                ('ip route (' + Translator.PATTERN_IPV4 + ') (' +
                 Translator.PATTERN_IPV4 + ') (' + Translator.PATTERN_IPV4 +
                 ')',
                 r'configure iproute add \1 \2 \3 vr VR-Default',
                 ''),
                (r'set time (\d?\d)/(\d?\d)/(\d\d\d\d) '
                 r'(\d?\d):(\d?\d):(\d?\d)',
                 r'configure time \1 \2 \3 \4 \5 \6',
                 ''),
                (r'set time (\d?\d):(\d?\d):(\d?\d)',
                 r'configure time <MONTH> <DAY> <YEAR> \1 \2 \3',
                 ''),
                ('set time (\d?\d)/(\d?\d)/(\d\d\d\d)',
                 r'configure time \1 \2 \3 <HOUR> <MINUTE> <SECOND>',
                 ''),
                ('set time',
                 'configure time <MONTH> <DAY> <YEAR> <HOUR> <MINUTE>'
                 ' <SECOND>',
                 ''),
                (r'show mac address (\S+)', r'show fdb \1', ''),
                (r'show mac port( \S+)?', 'show fdb ports <PORTSTRING>', ''),
                (r'show mac fid (\S+)',
                 r'show fdb vlan <VLAN_WITH_TAG_\1>',
                 ''),
                ('show mac', 'show fdb', ''),
                ('show spantree stats active',
                 'show stpd <STPD> ports | include " e(R|D|A|B|M)"',
                 ''),
                ('show spantree stats', 'show stpd detail', ''),
                ('show neighbors\s+\S+',
                 'show edp ports <PORTSTRING>\nshow lldp ports <PORTSTRING>'
                 ' neighbors\nshow cdp neighbor | include "Port[0-9]+"',
                 ''),
                ('show neighbors',
                 'show edp ports all\nshow lldp neighbors\nshow cdp neighbor',
                 ''),
                (r'set\s+password\s+(\S+)', r'configure account \1', ''),
                (r'no access-list \S+', r'rm <ACL_NAME>.pol',
                 'ACLs are stored as .pol files on XOS'),
                (r'set port mirroring create \S+ \S+',
                 'create mirror <MIRROR_NAME>\n'
                 'enable mirror <MIRROR_NAME> to port <DESTINATION_PORT>\n'
                 'configure mirror <MIRROR_NAME> add port <SOURCE_PORT>'
                 ' ingress-and-egress', ''),
                (r'show port alias( \S+)?',
                 'show ports [<PORTSTRING>] description', ''),
                (r'show port inlinepower( \S+)?',
                 'show inline-power info ports <PORTSTRING>', ''),
                (r'set port alias \S+\s+(\S+)?',
                 'configure ports <PORTSTRING> display-string \\1\n'
                 r'configure ports <PORTSTRING> description-string \1', ''),
                (r'set vlan egress (\d+) \S+ tagged',
                 r'configure vlan <VLAN_WITH_TAG_\1> add ports <PORTSTRING>'
                 ' tagged', ''),
                (r'set port inlinepower (\S+) admin off',
                 'disable inline-power ports <PORTSTRING>', ''),
                (r'set port inlinepower (\S+) admin auto',
                 'enable inline-power ports <PORTSTRING>', ''),
                (r'clear port vlan \S+',
                 r'configure vlan <VLAN_NAME> delete ports <PORTSTRING>'
                 '\nconfigure vlan Default add ports <PORTSTRING> untagged',
                 'You need one command per untagged VLAN. XOS always changes'
                 ' VLAN egress, too'),
                (r'clear vlan egress (\d+) \S+',
                 r'configure vlan <VLAN_WITH_TAG_\1> delete ports'
                 ' <PORTSTRING>',
                 'You need one command per VLAN.'
                 ' XOS deletes VLAN ingress from the port as well.'),
                (r'show port transceiver(\s+\S+)?(\s+all)?',
                 'show ports [<PORTSTRING>] transceiver information detail\n'
                 'debug hal show optic-info [ddmi|eeprom] port <PORT>', ''),
                )
            self.pattern_replacements = list(PatternReplacement(p, r, h) for
                                             p, r, h in pat_repl_lst)

    def convert_line(self, pattern, replacement, line):
        t, n = re.subn(pattern + '\s*$', replacement, line,
                       flags=re.IGNORECASE)
        if n:
            return t
        return None

    def translate(self, configline):
        configline_list = configline.strip().split()
        configline = ' '.join(configline_list)
        transl = Translation(eos=configline)
        if len(configline) == 0:
            return transl
        if configline.startswith('#') or configline.startswith('!'):
            return transl
        for pr in self.pattern_replacements:
            tl = self.convert_line(pr.pattern, pr.replacement, configline)
            if tl is not None:
                transl.set_hint(pr.hint)
                transl.set_xos(tl)
                break
            transl.set_hint('Config line not supported for translation (yet)!')
        return transl

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
