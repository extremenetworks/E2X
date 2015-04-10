# Release Notes for E2X Version 0.6.x

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

    set spantree
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

    access-list NUMBER {permit|deny} SOURCE [WILDCARD] [*]
    access-list NUMBER {permit|deny} {NUMBER|ip|udp|tcp|icmp} SOURCE [WILDCARD] [eq PORT] DEST [WILDCARD] [eq PORT] [*]
    ip access-group NUMBER in [*]
    access-list interface NUMBER [in] PORT [*]

Note that neither MAC nor IPv6 access control lists are support. Quality
of service (QoS) modifiers and ACL sequence specifiers are not supported
either.

## Function Module Stacking

The FM Stacking does not comprise any configuration commands, it provides
support for port mapping from standalone or stacked EOS switches to standalone
or stackes EXOS switches. This pertains to any supported commands with
port string arguments.
