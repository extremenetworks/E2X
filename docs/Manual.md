# E2X Translator User Manual

## Overview

The E2X Translator (E2X) is a command line tool to translate the
configuration of an Enterasys Operating System (EOS, also known as
ExtremeEOS) switch into an equivalent ExtremeXOS Network Operating System
(EXOS) switch configuration. Main intention is to help migrating from
Enterasys Networks (now Extreme Networks) SecureStack or similar to
Extreme Networks Summit Series switches.

Translation is based on a *source* and *target* switch. Selection
of specific switch models determines the input and output configuration
format as well as available ports. The switch ports of the source
switch are mapped to equivalent ports of the target switch (if possible).

Default configuration of the source and target switches is considered. As
a result an empty configuration file is translated to a configuration
that changes target switch settings to be equivalent to the source
switch defaults.

Unknown configuration commands in the input file(s) are ignored for the
translation. E2X will never be able to translate every configuration command
from EOS to XOS. Reason is both the sheer number of EOS commands and
the fact that some features of EOS switches are not supported by EXOS,
and vice versa.

Some common EOS configurations cannot be translated verbatim. E2X tries
to create equivalent or at least compatible configurations in this case.
One important example is the default spanning tree configuration of
EOS, that can only be approximated by a compatible EXOS spanning tree
configuration.

E2X works best with configuration sections copied directly from the
switch. Using the complete switch configuration as input will often
result in many unknown commands, but using (a combination of) supported
configuration sections should result in a useful translation without
(many) warnings or even errors.

You can print a configuration section using the `show config
SECTION` command, e.g. `show config vlan` or `show config
router`.

Because E2X performs consistency checks during translation, it might help
finding problems in EOS configuration templates by printing warnings or
even error messages.

### Input Configuration Formats

E2X supports EOS text configuration files as input. All keywords must be
written completely, unique abbreviations as known from the switch
command line are *not* supported.

Partial configurations may result in warnings, e.g. a router mode command
such as `access-list 1 permit 192.0.2.0 0.0.0.255` without first entering
the router configuration mode. To translate an ACL without warnings
enclose it in entering and leaving router configuration mode:

    router
    enable
    configure
    access-list 1 permit 192.0.2.0 0.0.0.255
    exit
    exit
    exit

Most `set` commands can be translated in isolation, but some, like setting
a VLAN name, need preceding commands.

Trying to translate `set vlan name 3 Three` results in the error `ERROR:
VLAN 3 not found (set vlan name)` and no translated configuration. Before
setting the VLAN name, the VLAN needs to be created:

    set vlan create 3
    set vlan name 3 Three

will create the translation:

    create vlan Three tag 3

### Output Configuration Formats

E2X supports ExtremeXOS text configuration files, also known as EXOS script
files (extension .xsf), and policy files (extension .pol) for access lists,
as output.

### Source Switch Models

* C5G124-24
* C5G124-24P2
* C5G124-48
* C5G124-48P2
* C5K125-24
* C5K125-24P2
* C5K125-48
* C5K125-48P2
* C5K175-24

The default source switch is a C5K125-48P2.

The source switch is specified by using the `--source` option with the
switch name, e.g. `--source C5G124-24`. If no `--source` option is given,
the default model is used.

### Target Switch Models

* SummitX460-24t
* SummitX460-24p
* SummitX460-24x
* SummitX460-48t
* SummitX460-48p
* SummitX460-48x
* XGM3S-2SF module
* XGM3S-2XF module
* XGM3S-4SF module

The default target switch is a SummitX460-48p with XGM3S-2SF module.

The target switch is specified by using the `--target` option with the
switch name, e.g. `--target SummitX460-48p+2sf+4sf`. If no `--target`
option is given, the default model is used.

### Stacks

Both SecureStack and SummitStack switches can be *stacked*. A stack
comprises several switches, but it is managed as one virtual switch.

A stack can be specified by using a comma separated list of switch model
names to the `--source` and `--target` options.

    --source C5K125-48P2,C5K125-48P2 \
    --target SummitX460-48p+2sf,SummitX460-48p+2sf

The switch model name list must not contain any whitespace.

If the target switch is used standalone, but with enabled stacking,
you can append a comma to the target switch model name to create a
translation suitable for a switch in stacking mode.

### Warnings

Warnings are generated for inconsistencies in the input configuration or
features that are problematic to translate. The input line that resulted
in the warning is translated, but the translation might not be exact.

You should review all warnings carefully before using the translated
configuration. Often the warning can be avoided by slight changes of the
input configuration.

You can use the `--err-warnings` option together with `--abort-on-error`
option to avoid creating translations if the translation creates warnings.

### Errors

Errors result from input configurations that cannot be translated correctly,
because either some information is missing or the feature is not supported
on the target platform. Any input configuration line resulting in an error
is *not* translated.

You should review all error messages carefully. You should *never* use a
configuration translation with errors. Instead, you should modify the input
configuration to translate without any errors and verify that this matches
the configuration requirements.

You can use the `--abort-on-error` option to avoid creating translations
if errors are encountered.

## Usage

E2X is a command line program implemented in Python 3. To use it,
an installation of Python 3 is needed (see http://python.org). E2X is
invoked either by its name or by giving it as an argument to the Python
3 interpreter:

    e2x.py

    python e2x.py

On GNU/Linux, Python 2 is often installed using the name `python` and
Python 3 under the name `python3`, so you would use `python3 e2x.py`
instead.

### Online Help

E2X prints a short help message if it is started with the option `--help`:

    e2x.py --help

    python e2x.py --help

### Common Use Case

To convert an EOS configuration in file *switch_config* to an EXOS
configuration saved to file *switch_config.xsf* invoke E2X as follows:

    e2x.py switch_config

If the input file name has the extension *.cfg*, the extension is replaced
by *.xsf* for the output file. Otherwise, the extension *.xsf* is added
to the complete input file name (including an extension) to create the
output file name.

If the EOS configuration contains access control lists (ACLs), one policy
file is used for each ACL. The policy files are saved in a directory
with the same base name as the output configuration. The policy file
names without *.pol* extension (policy file base names) are used to
reference the access lists in the translated configuration. Copy the
policy files to the root directory of the EXOS switch to use them.

To convert several configuration files in one go, just provide all file names
as program arguments:

    e2x.py config1.cfg config2.cfg config3.cfg

This will create the output files *config1.xsf*, *config2.xsf*, and
*config3.xsf*. For each configuration containing ACLs, a directory
containing one policy file per ACL is created as well.

### Options Overview

The behavior of E2X can be controlled using command line options.
Each option has a long form, starting with two hyphens. Some options
have a short form as well, consisting of a single hyphen and a single
character.

Long options can be abbreviated with a unique prefix. For example, you
can use *--c* as an abbreviation of *--comment-unknown-lines* (as long as
no other option starting with *--c* is added to E2X).

An optional sequence of two hyphens delimits options from arguments:

    e2x.py --quiet -- switch.cfg

This is useful if the configuration file name starts with a hyphen. Without
using *--* before the file name, a file name starting with a hyphen would
be interpreted as an option instead of as a file name. To translate a switch
configuration saved in the file *-1_floor.cfg*, you can use:

    e2x.py -- -1_floor.cfg

### Arguments

Any words on the command line not starting with a hyphen (or occurring after
a double hyphen) are treated as file names containing source switch
configuration commands.

### Option List

* -h, --help
    * Print a short help message and exit
* -V, --version
    * Print version information and exit
* -q, --quiet
    * Suppress non-error messages. This is helpful if you have already read
      the notification messages pertaining to a translation, and want to
      see any errors more distinctly.
* -v, --verbose
    * Print additional, informational messages. This is helpful in understanding
      how the translation is progressing.
* -D, --debug
    * Print debugging messages. This may be needed to gather relevant
      information for fixing a bug in E2X. This prints a lot of information,
      so you probably want to capture it in a file.
* --source *source_switch_model*
    * Specify the source switch model to use. This should correspond to the
      switch configuration that shall be translated. The switch model is used
      to check e.g. the validity of port configuration commands.
      Currently the following source switch model keywords can be used:
        * C5G124-24
        * C5G124-24P2
        * C5G124-48
        * C5G124-48P2
        * C5K125-24
        * C5K125-24P2
        * C5K125-48
        * C5K125-48P2
        * C5K175-24
      A stack of switches is specified by combining the switch model keywords
      in a comma separated list. The order of switch model keywords defines
      the position in the stack. The list must not contain any spaces (or
      any other whitespace):
        * C5K125-48P2,C5G124-24,C5K125-48
* --target *target_switch_model*
    * Specify the target switch model to use. This should correspond to the
      switch model to migrate to. The switch model is used to create a mapping
      from the source switch to equivalent ports of the target switch.
      Currently the following target switch model keywords can be used:
        * SummitX460-24p
        * SummitX460-24p+2sf
        * SummitX460-24p+2sf+4sf
        * SummitX460-24p+2xf
        * SummitX460-24p+2xf+4sf
        * SummitX460-24p+4sf
        * SummitX460-24t
        * SummitX460-24t+2sf
        * SummitX460-24t+2sf+4sf
        * SummitX460-24t+2xf
        * SummitX460-24t+2xf+4sf
        * SummitX460-24t+4sf
        * SummitX460-24x
        * SummitX460-24x+2sf
        * SummitX460-24x+2sf+4sf
        * SummitX460-24x+2xf
        * SummitX460-24x+2xf+4sf
        * SummitX460-24x+4sf
        * SummitX460-48p
        * SummitX460-48p+2sf
        * SummitX460-48p+2sf+4sf
        * SummitX460-48p+2xf
        * SummitX460-48p+2xf+4sf
        * SummitX460-48p+4sf
        * SummitX460-48t
        * SummitX460-48t+2sf
        * SummitX460-48t+2sf+4sf
        * SummitX460-48t+2xf
        * SummitX460-48t+2xf+4sf
        * SummitX460-48t+4sf
        * SummitX460-48x
        * SummitX460-48x+2sf
        * SummitX460-48x+2sf+4sf
        * SummitX460-48x+2xf
        * SummitX460-48x+2xf+4sf
        * SummitX460-48x+4sf
      A stack of switches is specified by combining the switch model keywords
      in a comma separated list. The order of switch model keywords defines
      the position in the stack. The list must not contain any spaces (or
      any other whitespace):
        * SummitX460-48p+2sf,SummitX460-24t,SummitX460-48p+2sf
      To specify that the standalone target switch is configured for stacking
      (`enable stacking`), append a comma to the switch model name:
        * SummitX460-24t,
* -o *file*, --outfile *file*
    * Specify a non-default file name for writing the translated configuration.
      If this option is used and several input files are given, *all* translated
      configuration lines are written to the same file.
* -d *outdir*, --outdir *outdir*
    * Specify a directory to save all output files in. If this option is not
      used, the current directory is used.
* --sfp-list *ports*
    * Specify the ports to be used with SFPs. This is important to map e.g.
      combo ports used with SFPs to pure SFP ports.
* --ignore-defaults
    * Ignore default configuration settings of both the source and target
      switches. Use this option to ignore differing defaults, e.g. pertaining
      to jumbo frames, for the translation.
* --keep-unknown-lines
    * Keep input configuration lines not understood by E2X unchanged in the
      output configuration file. These lines will be appended to the
      successfully translated configuration commands.
* --comment-unknown-lines
    * This is very similar to the *--keep-unknown-lines* options (see above),
      but unknown input configuration commands are copied as *comments* to
      the translated configuration. Thus the created configuration translation
      can be used as-is to configure the target switch.
* --err-unknown-lines
    * Treat unknown configuration commands in the input as a translation
      error. By default, unknown lines are ignored for the translation.
* --err-warnings
    * Treat warning messages as errors. To be confident about a new
      translation, it should succeed without warning. Some common
      EOS configurations cannot be replicated exactly on EXOS, that will
      create a warning message. You should review any warnings and errors
      closely before applying a translated configuration to an EXOS switch.
* --messages-as-comments
    * Add the messages pertaining to the translation process as comment lines
      to the respective output file(s). This is helpful if E2X is used
      for batch translations, to see which messages pertain to what input
      configuration file. This might be useful if E2X is used for a
      translation service and just the translated configuration files are
      delivered to the user.
* --abort-on-error
    * Abort translation if an error occurred. A translation with errors might
      create problems if applied to a production network device. If this
      option is used, no translated configuration is created if reading
      the input configuration or translating this to the target switch
      resulted in one or more errors.
* --disable-unused-ports
    * Create commands to disable target switch ports that are not included in
      the mapping from source switch ports to the target switch. This can
      happen if the target switch has more ports than the source switch.
      Un-mapped ports cannot be affected by the translated configuration.
      To prevent unexpected results from unconfigured ports, they should
      be disabled. Thus manual intervention is needed to actually use those
      ports, and the missing configuration should be noticed.

### E2X as a Filter Program

E2X works like a filter program as know from Unix operation systems
(see https://en.wikipedia.org/wiki/Filter_(software) for info).
Thus all program input can be provided on *standard input*, the translated
configuration is written to *standard output*, and additional program
output (e.g. error messages) is written to *standard error*. The contents
of policy files is preceeded by a comment line with the name for the policy
file which is used in the translated configuration.

## Examples

See also section **Common Use Case** above.

### Empty Input Configuration

Translating an empty input configuration translates the default EOS
configuration into an equivalent ExtremeXOS configuration. As of E2X
version 0.4.x this generates configuration commands to enable Jumbo
Frames and to configure and enable Multiple Spanning Tree.

E2X prints some notices because of differences is the used default
switches C5K125-48P2 and Summit X460-48p with XGM3S-2SF:

1. The 10 Gbps ports are called ```tg.1.49``` and ```tg.1.50``` on the
   C5, but they are called ```53``` and ```54``` on the X460.
2. The Summit X460 has an additional 4 ports in respect to the C5.
3. While EOS does not build a LAG consisting of just one port by default,
   EXOS will do this if port sharing is configured.

#### Windows

    >e2x.py < NUL
    # Enter EOS configuration commands, one per line.
    # End with CTRL+Z on a line of its own (sometimes needed twice)
    enable jumbo-frame ports 1
    enable jumbo-frame ports 2
    enable jumbo-frame ports 3
    enable jumbo-frame ports 4
    enable jumbo-frame ports 5
    enable jumbo-frame ports 6
    enable jumbo-frame ports 7
    enable jumbo-frame ports 8
    enable jumbo-frame ports 9
    enable jumbo-frame ports 10
    enable jumbo-frame ports 11
    enable jumbo-frame ports 12
    enable jumbo-frame ports 13
    enable jumbo-frame ports 14
    enable jumbo-frame ports 15
    enable jumbo-frame ports 16
    enable jumbo-frame ports 17
    enable jumbo-frame ports 18
    enable jumbo-frame ports 19
    enable jumbo-frame ports 20
    enable jumbo-frame ports 21
    enable jumbo-frame ports 22
    enable jumbo-frame ports 23
    enable jumbo-frame ports 24
    enable jumbo-frame ports 25
    enable jumbo-frame ports 26
    enable jumbo-frame ports 27
    enable jumbo-frame ports 28
    enable jumbo-frame ports 29
    enable jumbo-frame ports 30
    enable jumbo-frame ports 31
    enable jumbo-frame ports 32
    enable jumbo-frame ports 33
    enable jumbo-frame ports 34
    enable jumbo-frame ports 35
    enable jumbo-frame ports 36
    enable jumbo-frame ports 37
    enable jumbo-frame ports 38
    enable jumbo-frame ports 39
    enable jumbo-frame ports 40
    enable jumbo-frame ports 41
    enable jumbo-frame ports 42
    enable jumbo-frame ports 43
    enable jumbo-frame ports 44
    enable jumbo-frame ports 45
    enable jumbo-frame ports 46
    enable jumbo-frame ports 47
    enable jumbo-frame ports 48
    enable jumbo-frame ports 53
    enable jumbo-frame ports 54
    configure stpd s0 delete vlan Default ports all
    disable stpd s0 auto-bind vlan Default
    configure stpd s0 mode mstp cist
    create stpd s1
    configure stpd s1 mode mstp msti 1
    enable stpd s1 auto-bind vlan Default
    enable stpd s0
    enable stpd s1
    NOTICE: Mapping port "tg.1.49" to port "53"
    NOTICE: Mapping port "tg.1.50" to port "54"
    NOTICE: Port "49" of target switch is not used
    NOTICE: Port "50" of target switch is not used
    NOTICE: Port "51" of target switch is not used
    NOTICE: Port "52" of target switch is not used
    NOTICE: XOS always allows single port LAGs

#### GNU/Linux or Mac OS X

    $ e2x.py < /dev/null
    enable jumbo-frame ports 1
    enable jumbo-frame ports 2
    enable jumbo-frame ports 3
    enable jumbo-frame ports 4
    enable jumbo-frame ports 5
    enable jumbo-frame ports 6
    enable jumbo-frame ports 7
    enable jumbo-frame ports 8
    enable jumbo-frame ports 9
    enable jumbo-frame ports 10
    enable jumbo-frame ports 11
    enable jumbo-frame ports 12
    enable jumbo-frame ports 13
    enable jumbo-frame ports 14
    enable jumbo-frame ports 15
    enable jumbo-frame ports 16
    enable jumbo-frame ports 17
    enable jumbo-frame ports 18
    enable jumbo-frame ports 19
    enable jumbo-frame ports 20
    enable jumbo-frame ports 21
    enable jumbo-frame ports 22
    enable jumbo-frame ports 23
    enable jumbo-frame ports 24
    enable jumbo-frame ports 25
    enable jumbo-frame ports 26
    enable jumbo-frame ports 27
    enable jumbo-frame ports 28
    enable jumbo-frame ports 29
    enable jumbo-frame ports 30
    enable jumbo-frame ports 31
    enable jumbo-frame ports 32
    enable jumbo-frame ports 33
    enable jumbo-frame ports 34
    enable jumbo-frame ports 35
    enable jumbo-frame ports 36
    enable jumbo-frame ports 37
    enable jumbo-frame ports 38
    enable jumbo-frame ports 39
    enable jumbo-frame ports 40
    enable jumbo-frame ports 41
    enable jumbo-frame ports 42
    enable jumbo-frame ports 43
    enable jumbo-frame ports 44
    enable jumbo-frame ports 45
    enable jumbo-frame ports 46
    enable jumbo-frame ports 47
    enable jumbo-frame ports 48
    enable jumbo-frame ports 53
    enable jumbo-frame ports 54
    configure stpd s0 delete vlan Default ports all
    disable stpd s0 auto-bind vlan Default
    configure stpd s0 mode mstp cist
    create stpd s1
    configure stpd s1 mode mstp msti 1
    enable stpd s1 auto-bind vlan Default
    enable stpd s0
    enable stpd s1
    NOTICE: Mapping port "tg.1.49" to port "53"
    NOTICE: Mapping port "tg.1.50" to port "54"
    NOTICE: Port "49" of target switch is not used
    NOTICE: Port "50" of target switch is not used
    NOTICE: Port "51" of target switch is not used
    NOTICE: Port "52" of target switch is not used
    NOTICE: XOS always allows single port LAGs

### Ignore Default Configuration

If you want to ignore the different default settings and translate the
given commands only, use the ```--ignore-defaults``` option. With an empty
input configuration this will just print messages pertaining to hardware
differences.

#### Windows

    >e2x.py --ignore-defaults < NUL
    # Enter EOS configuration commands, one per line.
    # End with CTRL+Z on a line of its own (sometimes needed twice)
    NOTICE: Mapping port "tg.1.49" to port "53"
    NOTICE: Mapping port "tg.1.50" to port "54"
    NOTICE: Port "49" of target switch is not used
    NOTICE: Port "50" of target switch is not used
    NOTICE: Port "51" of target switch is not used
    NOTICE: Port "52" of target switch is not used

#### GNU/Linux or Mac OS X

    $ e2x.py --ignore-defaults < /dev/null
    NOTICE: Mapping port "tg.1.49" to port "53"
    NOTICE: Mapping port "tg.1.50" to port "54"
    NOTICE: Port "49" of target switch is not used
    NOTICE: Port "50" of target switch is not used
    NOTICE: Port "51" of target switch is not used
    NOTICE: Port "52" of target switch is not used

### Suppressing Non-Error Messages

To suppress the non-error messages generated by E2X, e.g. pertaining to
differences in source- and target switches, use the ```--quiet``` option.

#### Windows

    >e2x.py --quiet < NUL
    # Enter EOS configuration commands, one per line.
    # End with CTRL+Z on a line of its own (sometimes needed twice)
    enable jumbo-frame ports 1
    enable jumbo-frame ports 2
    enable jumbo-frame ports 3
    enable jumbo-frame ports 4
    enable jumbo-frame ports 5
    enable jumbo-frame ports 6
    enable jumbo-frame ports 7
    enable jumbo-frame ports 8
    enable jumbo-frame ports 9
    enable jumbo-frame ports 10
    enable jumbo-frame ports 11
    enable jumbo-frame ports 12
    enable jumbo-frame ports 13
    enable jumbo-frame ports 14
    enable jumbo-frame ports 15
    enable jumbo-frame ports 16
    enable jumbo-frame ports 17
    enable jumbo-frame ports 18
    enable jumbo-frame ports 19
    enable jumbo-frame ports 20
    enable jumbo-frame ports 21
    enable jumbo-frame ports 22
    enable jumbo-frame ports 23
    enable jumbo-frame ports 24
    enable jumbo-frame ports 25
    enable jumbo-frame ports 26
    enable jumbo-frame ports 27
    enable jumbo-frame ports 28
    enable jumbo-frame ports 29
    enable jumbo-frame ports 30
    enable jumbo-frame ports 31
    enable jumbo-frame ports 32
    enable jumbo-frame ports 33
    enable jumbo-frame ports 34
    enable jumbo-frame ports 35
    enable jumbo-frame ports 36
    enable jumbo-frame ports 37
    enable jumbo-frame ports 38
    enable jumbo-frame ports 39
    enable jumbo-frame ports 40
    enable jumbo-frame ports 41
    enable jumbo-frame ports 42
    enable jumbo-frame ports 43
    enable jumbo-frame ports 44
    enable jumbo-frame ports 45
    enable jumbo-frame ports 46
    enable jumbo-frame ports 47
    enable jumbo-frame ports 48
    enable jumbo-frame ports 53
    enable jumbo-frame ports 54
    configure stpd s0 delete vlan Default ports all
    disable stpd s0 auto-bind vlan Default
    configure stpd s0 mode mstp cist
    create stpd s1
    configure stpd s1 mode mstp msti 1
    enable stpd s1 auto-bind vlan Default
    enable stpd s0
    enable stpd s1

#### GNU/Linux or Mac OS X

    $ e2x.py --quiet < /dev/null
    enable jumbo-frame ports 1
    enable jumbo-frame ports 2
    enable jumbo-frame ports 3
    enable jumbo-frame ports 4
    enable jumbo-frame ports 5
    enable jumbo-frame ports 6
    enable jumbo-frame ports 7
    enable jumbo-frame ports 8
    enable jumbo-frame ports 9
    enable jumbo-frame ports 10
    enable jumbo-frame ports 11
    enable jumbo-frame ports 12
    enable jumbo-frame ports 13
    enable jumbo-frame ports 14
    enable jumbo-frame ports 15
    enable jumbo-frame ports 16
    enable jumbo-frame ports 17
    enable jumbo-frame ports 18
    enable jumbo-frame ports 19
    enable jumbo-frame ports 20
    enable jumbo-frame ports 21
    enable jumbo-frame ports 22
    enable jumbo-frame ports 23
    enable jumbo-frame ports 24
    enable jumbo-frame ports 25
    enable jumbo-frame ports 26
    enable jumbo-frame ports 27
    enable jumbo-frame ports 28
    enable jumbo-frame ports 29
    enable jumbo-frame ports 30
    enable jumbo-frame ports 31
    enable jumbo-frame ports 32
    enable jumbo-frame ports 33
    enable jumbo-frame ports 34
    enable jumbo-frame ports 35
    enable jumbo-frame ports 36
    enable jumbo-frame ports 37
    enable jumbo-frame ports 38
    enable jumbo-frame ports 39
    enable jumbo-frame ports 40
    enable jumbo-frame ports 41
    enable jumbo-frame ports 42
    enable jumbo-frame ports 43
    enable jumbo-frame ports 44
    enable jumbo-frame ports 45
    enable jumbo-frame ports 46
    enable jumbo-frame ports 47
    enable jumbo-frame ports 48
    enable jumbo-frame ports 53
    enable jumbo-frame ports 54
    configure stpd s0 delete vlan Default ports all
    disable stpd s0 auto-bind vlan Default
    configure stpd s0 mode mstp cist
    create stpd s1
    configure stpd s1 mode mstp msti 1
    enable stpd s1 auto-bind vlan Default
    enable stpd s0
    enable stpd s1

### Translating Configuration From File

To translate a configuration from a file and write it to another file
use the file name as argument to E2X.

#### Windows

    >dir sample.*
     Volume in drive C has no label.
     Volume Serial Number is XXXX-XXXX

     Directory of C:

    27.10.2014  14:19               191 sample.cfg
                   1 File(s)            191 bytes
                   0 Dir(s)   9.450.618.880 bytes free

    >type sample.cfg
    # disable the 10 Gbps ports
    set port disable tg.1.*
    # change EOS defaults to match EXOS defaults
    set spantree disable
    set port jumbo disable ge.*.*;tg.*.*
    set lacp singleportlag enable

    >e2x.py sample.cfg
    NOTICE: Writing translated configuration to file "sample.xsf"
    NOTICE: Mapping port "tg.1.49" to port "53"
    NOTICE: Mapping port "tg.1.50" to port "54"
    NOTICE: Port "49" of target switch is not used
    NOTICE: Port "50" of target switch is not used
    NOTICE: Port "51" of target switch is not used
    NOTICE: Port "52" of target switch is not used

    >dir sample.*
     Volume in drive C has no label.
     Volume Serial Number is XXXX-XXXX

     Directory of C:

    27.10.2014  14:19               191 sample.cfg
    27.10.2014  14:20                36 sample.xsf
                   2 File(s)            227 bytes
                   0 Dir(s)   9.450.618.880 bytes free

    >type sample.xsf
    disable ports 53
    disable ports 54

#### GNU/Linux or Mac OS X

    $ ls sample.*
    sample.cfg

    $ cat sample.cfg
    # disable the 10 Gbps ports
    set port disable tg.1.*
    # change EOS defaults to match EXOS defaults
    set spantree disable
    set port jumbo disable ge.*.*;tg.*.*
    set lacp singleportlag enable

    $ e2x.py sample.cfg
    NOTICE: Writing translated configuration to file "sample.xsf"
    NOTICE: Mapping port "tg.1.49" to port "53"
    NOTICE: Mapping port "tg.1.50" to port "54"
    NOTICE: Port "49" of target switch is not used
    NOTICE: Port "50" of target switch is not used
    NOTICE: Port "51" of target switch is not used
    NOTICE: Port "52" of target switch is not used

    $ ls sample.*
    sample.cfg  sample.xsf

    $ cat sample.xsf
    disable ports 53
    disable ports 54

### Manually Entering Commands

#### Windows

    >e2x.py --ignore-defaults --quiet
    # Enter EOS configuration commands, one per line.
    # End with CTRL+Z on a line of its own (sometimes needed twice)
    set port disable tg.1.49
    ^Z
    ^Z
    disable ports 53

#### GNU/Linux or Mac OS X

Entering CTRL-D is not echoed to the terminal, and there is no RETURN
between the two CTRL-D inputs.

    $ e2x.py --ignore-defaults --quiet
    # Enter EOS configuration commands, one per line.
    # End with CTRL+D (sometimes needed twice)
    set port disable tg.1.49

*CTRL+D* *CTRL+D*

    disable ports 53

### Piping Command Output Into E2X

#### Windows

    >echo set port disable ge.1.1 | e2x.py --quiet --ignore-defaults
    disable ports 1

#### GNU/Linux or Mac OS X

    $ echo 'set port disable ge.1.1' | e2x.py --quiet --ignore-defaults
    disable ports 1
