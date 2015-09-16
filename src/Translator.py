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

    PATTERN_IPV4 = '\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}'

    def __init__(self, pattern_replacements=None):
        if pattern_replacements:
            self.pattern_replacements = pattern_replacements
        else:
            self.pattern_replacements = \
                [PatternReplacement('show switch (\d+)',
                                    r'show slot \1'),
                 PatternReplacement('show switch',
                                    r'show slot'),
                 PatternReplacement('show (ip )?arp',
                                    r'show iparp'),
                 PatternReplacement('show ip arp vlan (\d+)',
                                    r'show iparp vlan '
                                    r'<NAME_OF_VLAN_WITH_TAG_\1>'),
                 PatternReplacement('show ip route connected',
                                    r'show iproute origin direct'),
                 PatternReplacement('show ip route static',
                                    r'show iproute origin static'),
                 PatternReplacement('show ip route ospf',
                                    r'show iproute origin ospf'),
                 PatternReplacement('show ip route rip',
                                    r'show iproute origin rip'),
                 PatternReplacement('show ip route summary',
                                    r'show iproute origin summary'),
                 PatternReplacement('show ip route',
                                    r'show iproute'),
                 PatternReplacement('reset',
                                    r'reboot'),
                 PatternReplacement('reset (\d+)',
                                    r'reboot slot \1'),
                 PatternReplacement('set telnet (enable|disable)'
                                    ' (all|inbound)',
                                    r'\1 telnet'),
                 PatternReplacement('set telnet (enable|disable) outbound',
                                    r'% Outbound telnet cannot be disabled'
                                    ' on EXOS (always enabled)'),
                 PatternReplacement('show telnet',
                                    r'show management | include Telnet'),
                 PatternReplacement('set ssh (enable|disable)d',
                                    r'\1 ssh2'),
                 PatternReplacement('show ssh',
                                    r'show management | include SSH'),
                 PatternReplacement('show webview',
                                    r'show management | include Web\n'
                                    'show ssl'),
                 PatternReplacement('show ssl',
                                    r'show ssl'),
                 PatternReplacement('set ip address '
                                    '(' + Translator.PATTERN_IPV4 +
                                    ') mask (' + Translator.PATTERN_IPV4 +
                                    ') gateway (' + Translator.PATTERN_IPV4 +
                                    ')',
                                    r'configure vlan Default ipaddress \1 \2\n'
                                    r'configure iproute add default \3'),
                 PatternReplacement('set ip address '
                                    '(' + Translator.PATTERN_IPV4 +
                                    ') mask (' + Translator.PATTERN_IPV4 +
                                    ')',
                                    r'configure vlan Default ipaddress \1 \2'),
                 PatternReplacement('set ip address '
                                    '(' + Translator.PATTERN_IPV4 + ')',
                                    r'configure vlan Default ipaddress \1'),
                 PatternReplacement('show ip address',
                                    r'show vlan'),
                 PatternReplacement('show config',
                                    r'show configuration'),
                 PatternReplacement('show config (\S+)',
                                    r'show configuration \1',
                                    'Section names may differ'),
                 PatternReplacement('save config',
                                    r'save configuration'),
                 PatternReplacement('set logging server 1 ip-addr (' +
                                    Translator.PATTERN_IPV4 +
                                    ') severity 6 state enable',
                                    r'configure log target syslog \1 severity '
                                    r'notice only'),
                 PatternReplacement('show logging server',
                                    r'show log configuration target syslog'),
                 PatternReplacement('set port vlan \S+ (\d+) modify-egress',
                                    r'configure vlan <VLAN_WITH_TAG_\1> add'
                                    ' ports <PORTSTRING>',
                                    'Untagged ingress and egress are always '
                                    'the same on EXOS'),
                 PatternReplacement('show port vlan( \S+)?',
                                    r'show ports [<PORTSTRING>] information'
                                    ' detail | include "(^Port|'
                                    '(Internal|802.1Q) Tag)"'),
                 PatternReplacement('show vlan (static )?(\d+)',
                                    r'show vlan tag \2'),
                 PatternReplacement('show vlan( static)?',
                                    r'show vlan detail'),
                 PatternReplacement('show port status( \S+)?',
                                    r'show ports [<PORTSTRING>] no-refresh'),
                 PatternReplacement('show port negotiation( \S+)?',
                                    r'show ports [<PORTSTRING>] configuration'
                                    ' no-refresh'),
                 PatternReplacement('set port broadcast \S+ (\d+)',
                                    r'configure ports <PORTSTRING> rate-limit'
                                    r' flood broadcast \1'),
                 PatternReplacement('show port broadcast( \S+)?',
                                    r'show ports [<PORTSTRING>] rate-limit'
                                    ' flood no-refresh'),
                 PatternReplacement('set port trap \S+ (enable|disable)',
                                    r'\1 snmp traps port-up-down ports'
                                    ' <PORTSTRING>'),
                 PatternReplacement('show port trap( \S+)?',
                                    r'show ports [<PORTSTRING>] information'
                                    ' detail | include (^Port|Link up/down)'),
                 PatternReplacement('show radius',
                                    r'show radius'),
                 PatternReplacement('show banner motd',
                                    r'show banner after-login'),
                 PatternReplacement('show banner login',
                                    r'show banner before-login'),
                 PatternReplacement('copy tftp://(' + Translator.PATTERN_IPV4 +
                                    ')/([-\w./]+) system:image',
                                    r'download image \1 \2 vr VR-Default '
                                    r'{primary|secondary}'),
                 PatternReplacement('dir', 'show version image\nls'),
                 PatternReplacement('set boot system [-\w./]+',
                                    'use image partition {primary|secondary}'),
                 PatternReplacement('show switch',
                                    r'show switch |include "Slot|Current '
                                    r'St|System T|.* ver"'),
                 PatternReplacement('set logout ([1-9]\d*)',
                                    r'configure idletimeout \1\nenable'
                                    ' idletimeout'),
                 PatternReplacement('set logout 0',
                                    r'disable idletimeout'),
                 PatternReplacement('show logout',
                                    r'show management | include "CLI idle"'),
                 PatternReplacement('set system login (\w+) super-user enable'
                                    ' password (\w+)',
                                    r'create account admin \1 \2',
                                    'Password is set interactively'),
                 PatternReplacement('set system login (\w+) super-user enable',
                                    r'create account admin \1'),
                 PatternReplacement('set system login (\w+) super-user disable'
                                    r' password (\w+)',
                                    r'create account admin \1 \2\n'
                                    r'disable account \1',
                                    'Password is set'),
                 PatternReplacement('set system login (\w+) super-user'
                                    ' disable',
                                    r'create account admin \1\n'
                                    r'disable account \1'),
                 PatternReplacement('show system login',
                                    r'show accounts'),
                 PatternReplacement('clear config',
                                    r'unconfigure switch',
                                    'Deletes all ip-addresses except address'
                                    ' of management port'),
                 PatternReplacement('clear config all',
                                    r'unconfigure switch all',
                                    'All ip-addresses are deleted'),
                 PatternReplacement('clear ip address',
                                    r'unconfigure vlan Default ipaddress'),
                 PatternReplacement('set ip protocol dhcp',
                                    r'enable dhcp vlan Default'),
                 PatternReplacement('show sntp',
                                    'show sntp-client'),
                 PatternReplacement('show time',
                                    'show switch | include "Current Time"'),
                 PatternReplacement('show summertime',
                                    'show switch | include "Timezone"'),
                 PatternReplacement('show version',
                                    'show version\n'
                                    'show switch | include "System Type:"'),
                 PatternReplacement('show support',
                                    'show tech'),
                 PatternReplacement('set sntp server ' + '(' +
                                    Translator.PATTERN_IPV4 + ')'
                                    r'( precedence (\d\d?))?',
                                    'configure sntp-client '
                                    r'{primary|secondary} \1 vr VR-Default'),
                 PatternReplacement('set sntp client disable',
                                    'disable sntp-client'),
                 PatternReplacement('set sntp client broadcast',
                                    'enable sntp-client',
                                    'EXOS uses unicast mode if an SNTP server'
                                    ' is configured'),
                 PatternReplacement('set sntp client unicast',
                                    'enable sntp-client',
                                    'EXOS uses broadcast mode if no SNTP'
                                    ' server is configured'),
                 PatternReplacement('set port (enable|disable) \S+',
                                    r'\1 ports <PORTSTRING>'),
                 PatternReplacement('show port egress( \S+)?',
                                    'show ports [<PORTSTRING>] information '
                                    'detail | include (^Port:|Tag =)'),
                 PatternReplacement('ip route 0.0.0.0 0.0.0.0 (' +
                                    Translator.PATTERN_IPV4 + ')',
                                    r'configure iproute add default \1 '
                                    'vr VR-Default'),
                 PatternReplacement('ip route (' + Translator.PATTERN_IPV4 +
                                    ') (' + Translator.PATTERN_IPV4 + ') (' +
                                    Translator.PATTERN_IPV4 + ')',
                                    r'configure iproute add \1 \2 \3 '
                                    'vr VR-Default'),
                 ]

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
            if tl:
                transl.set_hint(pr.hint)
                transl.set_xos(tl)
                break
            transl.set_hint('Config line not supported for translation (yet)!')
        return transl

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
