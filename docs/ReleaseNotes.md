# Release Notes for E2X Version 1.0.0

E2X can translate a subset of the EOS commands supported by SecureStack
switches (represented by the C5 command set). Supported commands are
grouped in *Function Modules* (FMs). This version of E2X implements the
following function modules:

* Port
* LAG
* VLAN
* STP
* ACL
* Stacking
* Management
* Basic Layer 3
* Interactive

The commands supported by each *Function Module* are listed below. Commands
that are not listed are not supported.

[*] after a command means that not all variants of the command are supported.

## Function Module Port

    set port enable
    set port disable
    set port alias
    set port speed
    set port duplex
    set port negotiation
    set port jumbo

## Function Module LAG

    set lacp {disable | enable}
    set lacp aadminkey
    set lacp static
    set port lacp [*]
    clear port lacp [*]

## Function Module VLAN

    set vlan create
    set vlan name
    set vlan egress
    clear vlan egress
    set port vlan

## Function Module STP

    set spantree [*]
    set spantree version
    set spantree msti
    set spantree mstmap
    set spantree mstcfgid
    set spantree priority
    set spantree spanguard
    set spantree autoedge
    set spantree portadmin
    set spantree adminedge

## Function Module ACL

    access-list <NUMBER> {permit|deny} <SOURCE> [<WILDCARD>] [*]
    access-list <NUMBER> {permit|deny} {<NUMBER>|ip|udp|tcp|icmp} <SOURCE> [<WILDCARD>] [eq <PORT>] <DEST> [<WILDCARD>] [eq <PORT>] [*]
    ip access-group <NUMBER> in [*]
    access-list interface <NUMBER> [in] <PORT> [*]

Note that neither MAC nor IPv6 access control lists are support. Quality
of service (QoS) modifiers and ACL sequence specifiers are not supported
either.

## Function Module Stacking

The FM Stacking does not comprise any configuration commands, it provides
support for port mapping from standalone or stacked EOS switches to standalone
or stacked EXOS switches. This pertains to any supported commands with
port string arguments.

## Function Module Management

    set prompt
    set system name
    set system contact
    set system location
    set banner
    set telnet
    set ssh {disabled|enabled}
    set webview
    set ssl {disabled|enabled}
    set ip address <IP> [mask <MASK> [gateway <GATEWAY>]]
    set ip protocol {bootp|dhcp|none}
    set host vlan
    set logout
    set logging server
    set sntp client
    set sntp server <IP> [precedence <PRECENDENCE>]
    set timezone
    set summertime {disable|enable}
    set summertime recurring
    set radius server <INDEX> <IP> <PORT> [<SECRET>] realm management-access
    set radius {disable|enable}
    set radius interface
    set tacacs server <INDEX> <IP> <PORT> <SECRET>
    set tacacs {disable|enable}
    set tacacs interface
    set snmp targetparams <NAME> user <PRINCIPAL> security-model {v1|v2c} message-processing {v1|v2c} [*]
    set snmp targetaddr <NAME> <IP> param <PARAM_NAME> [*]
    set system login <NAME> {super-user|read-write|read-only} {enable|disable} [password <PASSWORD>] [*]
    clear system login <NAME>

## Function Module Basic Layer 3

    interface {vlan|loopback} <NUMBER>
    ip address
    ip helper-address
    [no] shutdown
    [no] ip routing
    ip route

## Function Module Interactive

The FM *Interactive* interactively translates commands from EOS to EXOS.
These commands need not be configuration commands, but can be part of
e.g. the firmware update procedure. Thus it is separate from the configuration
translation part of E2X and supports a different set of commands.
In addition to translating individual command lines, how-tos can be displayed.

### How-Tos

    Upgrade firmware
    Reset switch to factory defaults
    Configure Management IP Address
    Configure Router IP Address
    Create a VLAN
    Configure a Quiet Switch
    Configure SNMPv3
    Configure SNMPv1 Trap Receiver
    Set Passwords for Default Accounts
    Clear Default Non-Admin Accounts
    Remove or Disable Default SNMP Credentials
    Create a Port Mirror

### Commands

    clear config [all]
    clear ip address
    clear port vlan <PORTSTRING>
    clear system login <NAME>
    clear vlan egress <VLAN> <PORTSTRING>
    copy tftp://<IPV4_ADDRESS>/[<PATH>/]<IMAGE_FILE> system:image
    dir
    ip route <PREFIX> <NETMASK> <GATEWAY>
    no access-list <NUMBER>
    reset [<NR>]
    save config
    set boot system <IMAGE_FILE>
    set flowcontrol disable
    set flowcontrol enable
    set ip address <IPV4-ADDRESS> [mask <NETMASK> [gateway <IPV4-ADDRESS>]]
    set ip protocol dhcp
    set logging server 1 ip-addr <IPV4-ADDRESS> severity 6 state enable
    set logout 0
    set logout <MINS>
    set password <ACCOUNT>
    set port alias <PORTSTRING> <ALIAS>
    set port broadcast <PORTSTRING> <NR>
    set port disable <PORTSTRING>
    set port enable <PORTSTRING>
    set port inlinepower <PORTSTRING> admin {auto|off}
    set port mirroring create <SOURCE_PORT> <DESTINATION_PORT>
    set port trap <PORTSTRING> {enable|disable}
    set port vlan <PORTSTRING> <NR> [modify-egress]
    set sntp client
    set sntp server <IP> [precedence <PRECEDENCE>]
    set ssh {enabled|disabled}
    set system login <NAME> {super-user|read-write|read-only} {enable|disable} [password <PASSWORD>]
    set telnet {enable|disable} {all|inbound|outbound}
    set time
    set vlan egress <VLAN> <PORTSTRING> tagged
    show banner {login|motd}
    show config [all] [<SECTION>]
    show ip address
    show [ip] arp
    show ip arp vlan <NR>
    show ip interface [{loopback|vlan} <NUMBER>]
    show ip route [connected|ospf|rip|static|summary]
    show logging server
    show logout
    show mac
    show mac address <MACADDRESS>
    show mac fid <VLAN>
    show mac port [<PORTSTRING>]
    show neighbors [<PORTSTRING>]
    show port alias [<PORTSTRING>]
    show port broadcast [<PORTSTRING>]
    show port egress [<PORTSTRING>]
    show port inlinepower [<PORTSTRING>]
    show port negotiation [<PORTSTRING>]
    show port status [<PORTSTRING>]
    show port transceiver [<PORTSTRING>] [all]
    show port trap [<PORTSTRING>]
    show port vlan [<PORTSTRING>]
    show radius
    show sntp
    show spantree stats [active]
    show ssh
    show ssl
    show summertime
    show support
    show switch
    show switch [<NR>]
    show system login
    show telnet
    show time
    show users
    show version
    show vlan [static] [<NR>]
    show vlan portinfo [port <PORTSTRING>]
    show webview
