# Development System Requirements

Development of E2X is done using GNU/Linux systems. A Mac OS X system
with development tools works as well. A Windows system with Cygwin
installed should be usable, too.

The source code is kept inside a git repository, thus a git installation
is needed for development.

Since E2X is developed in Python 3, a Python 3 installation is needed.
The E2X test suit uses the module *unittest.mock*, which was added in
version 3.3. It is likely that further Python modules added in 3.3, e.g.
the *ipaddress* module, will be used for E2X. In addition to unit
tests using the *unittest* module, automated integration tests using
[scripttest](http://pythonpaste.org/scripttest/) are implemented as well. A
copy of *scripttest* is included in the git repository.

The make program is used to ease creation of a single executable E2X
program, `e2x.py`. This enables easy generation of HTML documentation
or release archives as well. GNU Make is used because it is readily
available on GNU/Linux and for most other operating systems as well.

The single executable `e2x.py` program is built using the *zip* archiving
program.

Since E2X is hosted in GitHub, Markdown is used for
documentation. *Pandoc* is used to convert Markdown to HTML for use
outside of GitHub.

The source code is formatted according to PEP8, conformance is checked
using the `pep8` tool.

## List of Requirements

* git
* Python 3.3 or newer
* make
* zip
* pandoc

## Makefile Targets

* `make` builds the `e2x.py` executable
* `make clean` removes generated files
* `make distclean` calls `make clean` and removes Python cache files
* `make html` builds HTML documentation
* `make check` runs the automated tests
* `make preview` creates an archive comprising `e2x.py`, the sources and tests

# Repository Organisation

All Python source code can be found in the `src/` directory.  The test
suite can be found in the `tests/` directory.  Documentation (except
the README) is located inside the `docs/` directory.  The `templates/`
directory contains templates for python source files and unit test files.
The tools directory contains a git pre-commit script that checks for
PEP8 conformance as well as performing some portability checks. This
pre-commit script should be installed in the `.git/` directory of each
repository clone.

# E2X Translation Model

From a high level view, the E2X translation process starts by instantiating
models of the source and target switch. Based on this a mapping of source
to target ports is created. Then EOS configuration commands are read from the
input file and applied one after the other to change the source switch model
configuration. After applying the complete input configuration, the
configuration is compared to the target switch configuration and differences
are copied over. The copied configuration is then used to create an XOS
script file (text configuration file) as output.

## CLI

E2X uses a command line interface. The implementation is contained in the
file `src/cli.py` file. Argument and option processing uses the *argparse*
Python module. Reading input from file(s) and/or standard input uses the
Python module *fileinput*.

The CLI instantiates a *Core Module* (see below), and sets the appropriate
parameters (source and target switches, use of SFP ports, use of default
configuration settings or not, how to handle unknown input lines, ...). These
settings are set per E2X execution, they are the same for every input
file provided on the command line.

After that, each input file is read into memory and provided to the
*Core Module* to create a translated configuration. This is written to
the respective output file or standard output. Errors and other messages
are printed to standard error.

If any of the translation units resulted in an error message, `e2x.py` will
exit with a non-zero exit code. Otherwise the exit code will be 0.

## Core Module

The *Core Module* is implemented in the `src/CM.py` file. The `CoreModule`
class ties together all the parts needed for translating an ordered set
of configuration commands.

The different possible source- and target switches are registered in the
core module. The list of supported switch models is provided to e.g. the
`cli.py` file, where it is used to generate the help message and check
for valid switch names.

Instantiation of source- and target switch is triggered from `cli.py`.
The selected source switch defines the accepted input configuration
language, the target switch defined the output configuration language
used.

After instantiating source- and target switches, the
`CoreModule.translate()` method is used for translating a configuration
file. for each translation, source- and target switches are initialized,
default values are applied (if not disabled), and the port mapping is
created. Then the input configuration is applied to the source switch
model. Afterwards, a mapping of link aggregation groups (LAGs) similar
to the port mapping is created. The configuration of the source switch
is transferred to the target switch using the port- and LAG-mapping. Then
the output configuration is created from the target switch. Both
output configuration and errors, warnings, and other messages are
returned from the `CoreModule.translate()` method to the caller.

### Switch Model

The generic switch model is implemented in the `src.Switch.py` file. The
`Switch` class from this file is not used directly for source- or target
switches, but model specific classes are derived from the generic `Switch`
class. `Switch` can be viewed as an *abstract* class.

The `Switch` class basically defines the interface used by the *Core Module*,
but the implementation of (model specific) interface parts is provided
by the derived classes `EosSwitch` and `XosSwitch`.

#### Source Switch

A source switch needs an implementation of the `CmdInterpreter()` method.
This is provided in the file `src/EOS_read.py`. The command interpreter
is based on the Python module *cmd*. As such, implementation of global
commands (e.g. EOS `set` or any EXOS commands) is a straight forward
mapping to the *cmd* module usage. To apply the interpreted command to
the source switch, a reference to the switch object is passed to the
command interpreter.  EOS layer 3 configuration commands are IOS-like
and need additional context to correctly apply the current configuration
command (e.g. which interface is affected).

#### Target Switch

A target switch needs an implementation of the `ConfigWriter()` method.
This is provided in the file `src/XOS_write.py`. The config writer
functionality is organized according to the needs of the respective
configuration language. For example on EXOS, port sharing needs to
be configured before adding the LAG to a VLAN, and some physical port
configuration needs to be done before defining LAGs.

The generic `ConfigWriter()` class (implemented in `src/Switch.py`) calls
all *Feature Modules* (see below) in a fixed order, but the order inside
each *Feature Module* can be adjusted to the specific configuration language.

### Port and LAG Mapping

To correctly transfer a port configuration from source- to target switch,
a port mapping is created. This is based on the hardware descriptions of
the switch models (see `src/EOS.py` and `src/XOS.py`). Because the EOS
and XOS switches have slightly different port configurations, not all
ports have a universal mapping. For example the combo ports of a C5G124-48
have no exact counterpart on an Summit X460-48t switch. Additionally, the
Summit X460-48t has 52 ports, while the C5G124-48 has 48 ports only. Thus
some ports of the Summit switch will not be used when transferring a
configuration from a 48 port C5.

Additionally, the LAG configuration model differs significantly between
EOS and EXOS based switches. The former provide a couple of logical ports
that are used to configurae LAGs. The latter redefine ports to represent
an LAG (`enable sharing`). On EXOS, the redefined port name sometimes
represents the LAG, but sometimes it still represents the physical port.
Therefore physical port configuration is emitted first (see above), and
only those LAGs that are configured on the EOS switch will be represented
in the translated EXOS configuration.

### Macro Expansion

Prior to applying the configuration files read from an input file to the
source switch, macros in the configuration are expanded (`expand_macros()`).
There is currently just one macro implemented (`set lacp static`), and
this step is optional (the generic switch provides an implementation that
returns the exact configuration provided to the method).

## Feature Modules

E2X functionality is divided in so called *Feature Modules*. This is a logical
term, that is not reflected in the implementation of reading a config file.
Reading the configuration is based on the syntax of the interpreted command,
irrespective of the *Feature Module* containing this functionality.

Writing of the translated configuration is done by *Feature Module*, because
some features (e.g. VLANs) depend on prior configuration of other features
(e.g. LAGs).

As of E2X version 0.4.x there are 4 *Feature Modules*: *port*, *LAG*, *VLAN*,
and *STP*. The implementation is broken up in reading (`src/EOS_read.py`) and
writing (`src/XOS_write.py`).

# Flow of Execution

* Entry point is main() function in cli.py
* CoreModule is instantiated
    * creation of list of source and target switches
* Option parsing
* Source and target switches are instantiated
* For each input file
    * Reading of all lines of input into a Python list
    * CoreModule.translation() is called with the input configuration commands
        * Initialization of source and target switches
        * Application of default settings to source and target switches
        * Creation of port mapping from source to target switch
        * Macro expansion in input configuration
        * Application of each command from the expanded input connfiguration to
          source switch
        * Creation of LAG mapping from source to target (configured LAGs only)
        * Transfer of configuration from source to target switch
        * Return translated configuration (plus messages)
    * Print translated configuration
    * Print messages pertaining to translation

# Testing

To ensure a high quality implementation, every supported configuration
command needs to be tested. Additionally, the low level implementation
and interfaces are tested with unit tests. Any new functionality needs
to include tests. Bug fixes should include tests as well to avoid regressions.

# Extensibility

E2X is built with extensibility in mind. To add e.g. Alcatel to EXOS
translation, one would need to add Alcatel hardware definitions and a
command interpreter. There is no need to implement all features
supported by EOS, and additional features could be added to just the new
Alcatel files and to `XOS_write.py` without affecting EOS to EXOS translation.

Since switch configuration models as implemented by switch operating systems
often differ significantly, both reading and writing of configuration files
includes consistency checks. Configuration commands pertaining to some
feature that is not supported by the target platform result in an error.
The latter checks are implemented in the `ConfigWriter()` method of the
target switch.
