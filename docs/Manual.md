# E2X Translator User Manual

## Overview

The E2X Translator (E2X) is a command line tool to translate the
configuration of an Enterasys Operating System (EOS) switch into
an equivalent ExtremeXOS Network Operating System (EXOS) switch
configuration. Main intention is to help migrating from Enterasys Networks
(now Extreme Networks) SecureStack or similar to Extreme Networks Summit
Series switches.

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

### Input Configuration Formats

E2X supports EOS text configuration files as input.

### Output Configuration Formats

E2X supports ExtremeXOS text configuration files, also known as EXOS script
files (extension .xsf), as output.

### Source Switch Models

* C5G124-24
* C5K125-48
* C5K125-48P2 (this is the default model used)

### Target Switch Models

* SummitX460-24t
* SummitX460-48p
* SummitX460-48p with an XGM3S-2SF module (this is the default model used)
* SummitX460-48p with an XGM3S-2XF module
* SummitX460-48p with an XGM3S-4SF module
* SummitX460-48p with an XGM3S-2SF and an XGM3S-4SF module

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

To convert several configuration files in one go, just provide all file names
as program arguments:

    e2x.py config1.cfg config2.cfg config3.cfg

This will create the output files *config1.xsf*, *config2.xsf*, and
*config3.xsf*.

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
        * C5K125-48
        * C5K125-48P2
* --target *target_switch_model*
    * Specify the target switch model to use. This should correspond to the
      switch model to migrate to. The switch model is used to create a mapping
      from the source switch to equivalent ports of the target switch.
      Currently the following target switch model keywords can be used:
        * SummitX460-24t
        * SummitX460-48p
        * SummitX460-48p+2sf
        * SummitX460-48p+2xf
        * SummitX460-48p+4sf
        * SummitX460-48p+2sf+4sf
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
output (e.g. error messages) is written to *standard error*.

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
