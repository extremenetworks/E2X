# Development System Requirements

Development of E2X is done using GNU/Linux systems. A Mac OS X system
with development tools works as well. A Windows system with Cygwin
installed should be usable, too.

The source code is kept inside a git repository, thus a git installation
is needed for development.

Since E2X is developed in [Python 3](http://www.python.org), a
Python 3 installation is needed.  The E2X test suit uses the module
[unittest.mock](https://docs.python.org/3/library/unittest.mock.html),
which was added in version 3.3. Further Python modules added in 3.3, e.g.
the [ipaddress](https://docs.python.org/3/library/ipaddress.html)
module, are used for E2X. In addition to unit tests using the
[unittest](https://docs.python.org/3/library/unittest.html)
module, automated integration tests using
[scripttest](http://pythonpaste.org/scripttest/) are implemented as
well. A copy of *scripttest* is included in the git repository.
Automatic testing of the interactive mode uses
[pexpect](https://pypi.python.org/pypi/pexpect). It can be installed
via `pip3 install pexpect` or `python3 -m pip install pexpect`,
or something similar, depending on the local Python 3 installation.

The make program is used to ease creation of a single
executable E2X program, `e2x.py`. The Makefile enables easy
generation of HTML documentation or release archives as well. [GNU
Make](http://www.gnu.org/software/make/) is used because it is readily
available on GNU/Linux and for most other operating systems as well.

The single executable `e2x.py` program is built using the *zip* archiving
program. The Python interpreter accepts ZIP archives of Python files as input.

Since E2X is hosted on [GitHub](https://github.com/),
[Markdown](https://help.github.com/articles/github-flavored-markdown/)
is used for documentation. [Pandoc](http://pandoc.org/) is used to
convert Markdown to HTML for use outside of GitHub.

The source code is formatted according to
[PEP8](https://www.python.org/dev/peps/pep-0008/), conformance is checked
using the [`pep8`](https://pypi.python.org/pypi/pep8) tool.

## List of Requirements

* git
* Python 3.3 or newer
* make
* zip
* pandoc
* POSIX compatible tools (e.g. cat, chmod, sed)
* pep8
* pexpect

## Makefile Targets

* `make` builds the `e2x.py` executable and HTML documentation
* `make clean` removes generated files
* `make distclean` calls `make clean` and removes Python cache files
* `make html` builds HTML documentation
* `make check` runs the automated tests
* `make bin-dist` creates an archive comprising `e2x.py` and documentation
* `make src-dist` creates an archive containing the complete source code
* `make preview` creates an archive comprising `e2x.py`, the sources and tests

# Repository Organisation

All Python source code can be found in the [src/](../src/)
directory. The test suite can be found in the [tests/](../tests/)
directory. Documentation (except the [README](../README.md)) is located
inside the [docs/](../docs/) directory. The [templates/](../templates/)
directory contains templates for python source files and unit test
files. The tools directory contains a git pre-commit script that checks
for PEP8 conformance as well as performing some portability checks. This
pre-commit script should be installed in the `.git/` directory of each
repository clone.

# E2X Translation Model

From a high level view, the E2X translation process starts by instantiating
models of the source and target switches. Based on this a mapping of source
to target ports is created. Then EOS configuration commands are read from the
input file and applied one after the other to change the source switch
configuration. After applying the complete input configuration, the
configured source switch is compared to the target switch and differences
are copied over. The target switch configuration is then used to create an XOS
script file (text configuration file), and possibly policy files, as output.

## Single Line Commands

The EOS layer 2 configuration commands comprise a single line each. Each such
configuration line is interpreted without regard for the context. The
configuration state of the switch is taken into account, e.g. a VLAN needs
to be created first before it can be named.

### Non-Configuration Commands

Switch commands that do not change the configuration (e.g. `dir`) do not
readily fit into the idea of translating a configuration. They are supported
in *interactive mode*, which can be used as an interactive translation
reference.

## Router Configuration Mode Commands

The IOS like router configuration mode of EOS switches uses different
configuration sub-modes, and IOS like configuration commands are valid
in some sub-modes only. Therefore the configuration parser of E2X needs
to keep additional state to correctly interpret configuration commands
(e.g. `ip address ...` pertains to the previous `interface vlan ...`).

If possible, router mode commands are translated even outside of the
correct context resp. configuration mode, but this may result in
a warning.

## CLI

E2X uses a command line interface. Entry point is the file
[`__main__.py`](../src/__main__.py), which will be used by
Python when called with the e2x.py ZIP archive as argument. The
command line interface implementation is contained in the file
[`cli.py`](../src/cli.py) file. Argument and option processing uses
the [argparse](https://docs.python.org/3/library/argparse.html) Python
module. Reading input from file(s) and/or standard input uses the Python
module [fileinput](https://docs.python.org/3/library/fileinput.html).

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

The *Core Module* is implemented in the [`CM.py`](../src/CM.py) file. The
`CoreModule` class ties together all the parts needed for translating
an ordered set of configuration commands.

The different possible source- and target switches are registered in the
core module. The list of supported switch models is provided to e.g. the
[`cli.py`](../src/cli.py) file, where it is used to generate the help
message and check for valid switch names.

Instantiation of source- and target switch is triggered from
[`cli.py`](../src/cli.py). The selected source switch defines the
accepted input configuration language, the target switch defined the
output configuration language used.

After instantiating source- and target switches, the
`CoreModule.translate()` method is used for translating a configuration
file. for each translation, source- and target switches are initialized,
default values are applied (unless this is disabled), and the port mapping is
created. Then the input configuration is applied to the source switch
model. Afterwards, a mapping of link aggregation groups (LAGs) similar
to the port mapping is created. The configuration of the source switch
is transferred to the target switch using the port- and LAG-mapping. Then
the output configuration is created from the target switch. Both
output configuration and errors, warnings, and other messages are
returned from the `CoreModule.translate()` method to the caller.

### Switch Model

The generic switch model is implemented in the
[`Switch.py`](../src/Switch.py) file. The `Switch` class from this file
is not used directly for source- or target switches, but model specific
classes are derived from the generic `Switch` class. `Switch` can be
viewed as an *abstract* class.

The `Switch` class basically defines the interface used by the *Core Module*,
but the implementation of (model specific) interface parts is provided
by the derived classes `EosSwitch` and `XosSwitch`.

#### Source Switch

A source switch needs an implementation of the `CmdInterpreter()` method.
This is provided in the file [`EOS_read.py`](../src/EOS_read.py). The
command interpreter is based on the Python module
[*cmd*](https://docs.python.org/3/library/cmd.html). As such,
implementation of global commands (e.g. EOS `set` or any EXOS commands)
is a straight forward mapping to the *cmd* module usage. To apply the
interpreted command to the source switch, a reference to the switch
object is passed to the command interpreter. EOS layer 3 configuration
commands are IOS-like and need additional context to correctly apply
the current configuration command (e.g. which interface is affected).

#### Target Switch

A target switch needs an implementation of the `ConfigWriter()` method.
This is provided in the file [`XOS_write.py`](../src/XOS_write.py). The
config writer functionality is organized according to the needs of the
respective configuration language. For example on EXOS, port sharing needs
to be configured before adding the LAG to a VLAN, and some physical port
configuration needs to be done before defining LAGs.

The generic `ConfigWriter()` class (implemented in
[`Switch.py`](../src/Switch.py)) calls all *Feature Modules* (see below)
in a fixed order, but the order inside each *Feature Module* can be
adjusted to the specific configuration language.

### Port and LAG Mapping

To correctly transfer a port configuration from source- to target
switch, a port mapping is created. This is based on the hardware
descriptions of the switch models (see [`EOS.py`](../src/EOS.py) and
[`XOS.py`](../src/XOS.py)). Because the EOS and XOS switches have slightly
different port configurations, not all ports have an obvious mapping. For
example the combo ports of a C5G124-48 have no exact counterpart on an
Summit X460-48t switch. Additionally, the Summit X460-48t has 52 ports,
while the C5G124-48 has 48 ports only. Thus some ports of the Summit
switch will not be used when transferring a configuration from a 48
port C5.

Additionally, the LAG configuration model differs significantly between
EOS and EXOS based switches. The former provide a couple of logical ports
that are used to configurae LAGs. The latter redefine ports to represent
an LAG (`enable sharing`). On EXOS, the redefined port name sometimes
represents the LAG, but sometimes it still represents the physical port.
Therefore physical port configuration is emitted first (see above), and
only those LAGs that are configured on the EOS switch will be represented
in the translated EXOS configuration.

### Configuration Normalization

The first step after reading the configuration lines is to *normalize* it.
For EOS, that means converting all key words to lower case.

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

As of E2X version 0.4.x there are 4 *Feature Modules*: *port*,
*LAG*, *VLAN*, and *STP*. The implementation is broken up
in reading ([`EOS_read.py`](../src/EOS_read.py)) and writing
([`XOS_write.py`](../src/XOS_write.py)).

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
        * Input configuration normalization
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
Alcatel files and to [`XOS_write.py`](../src/XOS_write.py) without
affecting EOS to EXOS translation.

Since switch configuration models as implemented by switch operating systems
often differ significantly, both reading and writing of configuration files
includes consistency checks. Configuration commands pertaining to some
feature that is not supported by the target platform result in an error.
The latter checks are implemented in the `ConfigWriter()` method of the
target switch.

## Adding Configuration Command Translation

This section gives a step by step overview on adding a new switch
configuration command translation from ExtremeEOS to ExtremeXOS fitting
into an existing function module to E2X.

### Switch Model

The first step for adding a new configuration command translation is
to add the respective configuration attribute(s) to the switch model. A
simple per switch attribute can be added as a new variable. A more complex
attribute, like a list of syslog servers, might require a new class. This
is done in the file [`Switch.py`](../src/Switch.py). A new class would be
added as a new file, see e.g. [`SyslogServer.py`](../src/SyslogServer.py).

The values of the new attributes need to be transfered from the
source switch model to the target switch model. This is done in method
`Switch.transfer_config()`.

To verify that the new attributes have been included in the translation,
they need to be added to the `ConfigWriter.check_unwritten()` method.

For debugging purposes, new switch model attributes should be added to
the `Switch.__str__()` method.

### Switch OS Defaults

If the added attributes have default values in ExtremeEOS and/or ExtremeXOS,
those need be added to `EosSwitch.apply_default_settings()` (file
[`EOS.py`](../src/EOS.py)) and/or `XosSwitch.apply_default_settings()`
(file [`XOS.py`](../src/XOS.py)).

### Configuration Command Parsing

Parsing of the new configuration command needs to be added to the file
[`EOS_read.py`](../src/EOS_read.py).

### Configuration Line Writing

Writing of the translated commands needs to be added to the
appropriate method (corresponding to a functional module) in
[`XOS_write.py`](../src/XOS_write.py). The order of the functional
modules needs to ensure that prerequsites are fulfilled for
every translated command. E.g., a VLAN needs to be created before an IP
address can be configured for that VLAN on ExtremeXOS.

### Tests

To verify that the new translation did not break any existing functionality,
the automated test suit needs to be run (`make check`). Some tests may fail
because of the new functionality, e.g. the output of `Switch.__str__()` is
tested and the new switch attribute(s) changed it. These tests need to be
adjusted to the added command translation.

To verify that the translation works, and to ensure it continues to work,
tests should be added. [`IntegrationTest.py`](../tests/IntegrationTest.py)
is used to check translation of configuration snippets. The new command
translation needs to be added there. Additional unit tests should be
added as well.

### Documentation

The newly translated ExtremeEOS command needs to be added to the file
[`ReleaseNotes.md`](ReleaseNotes.md). Update additional documentation
as needed.

### Checklist

* [`Switch.py`](../src/Switch.py)
    * Add new switch attributes (may need new classes for complex attributes)
    * Add attributes to `Switch.__str__()`
    * Add attributes to `Switch.transfer_config()`
    * Add attributes to `ConfigWriter.check_unwritten()`
* [`EOS.py`](../src/EOS.py)
    * Add defaults for new switch attributes
    * Add command keywords to EosSwitch.normalize_config()
* [`XOS.py`](../src/XOS.py)
    * Add defaults for new switch attributes
* [`EOS_read.py`](../src/EOS_read.py)
    * Add command line parsing
* [`XOS_write.py`](../src/XOS_write.py)
    * Add translated commands to `XosConfigWriter.<FunctionModule>()`
* Run automated tests (`make check`)
    * Adjust tests to changes (e.g. for `Switch.__str__()`)
    * Verify existing functionality still works as expected
* Add tests
    * Test new command translation
        * [`IntegrationTest.py`](../tests/IntegrationTest.py)
    * Add unit tests
* Update [`ReleaseNotes.md`](ReleaseNotes.md) with the new command translation
* Update the [`Manual.md`](Manual.md) and/or other documentation if applicable

## Adding Interactive Mode Command Translation

Command translation for the interactive mode is independent of
configuration command translation. Translation is done using
pattern matching and text replacement. The pattern replacement
is defined in the initializer of class `Translator` in the file
[`Translator.py`](../src/Translator.py). Any new commands need to be added
there. Note that the order of the specified patterns is important.
More specific patterns need to preceed less specific patterns with the
same prefix.

The command list displayed in E2X interactive mode is generated from the
file [`ReleaseNotes.md`](ReleaseNotes.md). Any new commands need to be
added there as well.

All command translations in interactive mode need to be added to the
[`InteractiveModeIntegrationTest.py`](../tests/InteractiveModeIntegrationTest.py)
by adding translation examples to the file
[`interactive_statements`](../tests/interactive_statements).

## Adding Interactive Mode How-To

The E2X interactive mode how-tos are defined in XML format in the
file [`HowToHandler.py`](../src/HowToHandler.py) in the attribute
`HowToHandler.howtos`.

Any new how-to(s) should be added to [`ReleaseNotes.md`](ReleaseNotes.md)
as well.

If the new how-to(s) contain commands missing from interactive mode
command translation, consider adding them there, too.
