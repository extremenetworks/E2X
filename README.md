# E2X Translator README

The E2X Translator (E2X) is a command line tool to translate the
configuration of an Enterasys Operating System (EOS) switch into
an equivalent ExtremeXOS Network Operating System (EXOS) switch
configuration. Main intention is to help migrating from Enterasys Networks
(now Extreme Networks) SecureStack or similar to Extreme Networks Summit
Series switches.

## Reference Platforms

The reference source platform for E2X is a C5K125-48P2 switch (C-Series
switch with 48 triple speed ports with PoE (including 2 combo ports),
and 2 SFP+ uplink ports) using EOS version 6.71.

The reference target platform is a Summit X460-48p switch with an
XGM3S-2SF uplink module (Summit Series switch with 48 triple speed ports
with PoE, 4 SFP ports, and 2 SFP+ uplink ports).

## System Requirements

E2X is implemented in Python 3, with a minimum required version of 3.3.
Development and testing is primarily done on GNU/Linux systems, with
additional testing on Windows and Mac OS X.

## Documentation

Documentation for E2X can be found in the [docs/](docs/) directory.
There you find a [user manual](docs/Manual.md) and a [development
document](docs/Development.md).

### Online Help

E2X prints a short help message if the option `--help` is used:

```
$ e2x.py --help
usage: e2x [-h] [-V] [-q] [-v] [-D] [--source SOURCE] [--target TARGET]
           [-o OUTFILE] [-d OUTDIR] [--sfp-list SFP_LIST] [--ignore-defaults]
           [--keep-unknown-lines] [--comment-unknown-lines]
           [--err-unknown-lines] [--err-warnings] [--messages-as-comments]
           [--abort-on-error] [--disable-unused-ports]
           [FILE [FILE ...]]

Translate ExtremeEOS switch configuration commands to ExtremeXOS. If no
FILEs are specified, input is read from STDIN and written to STDOUT, and
ACLs are preceded by a comment giving the policy file name used in the
translation. If FILEs are specified, the translated configuration read
from a file is written to a file with the same name with the extension
'.xsf' appended. The associated ACLs are written to individual policy
files saved in directory named after the input file (with extension
'.acls'). Default settings of source and target switches are considered
unless the option to ignore switch default settings is given. Valid
input lines that are not yet supported will be ignored.

positional arguments:
  FILE                  EOS file to translate (default STDIN)

optional arguments:
  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit
  -q, --quiet           suppress non-error messages
  -v, --verbose         print informational messages
  -D, --debug           print debug information
  --source SOURCE       source switch model (default C5K125-48P2)
  --target TARGET       target switch model (default SummitX460-48p+2sf)
  -o OUTFILE, --outfile OUTFILE
                        specify non-default output file, '-' for STDOUT
  -d OUTDIR, --outdir OUTDIR
                        specify output directory (default '.')
  --sfp-list SFP_LIST   list of combo ports with SFP installed, e.g.
                        'ge.1.47,ge.1.48'
  --ignore-defaults     ignore switch default settings for translation
  --keep-unknown-lines  copy unknown input configuration lines to output
  --comment-unknown-lines
                        add unknown input configuration lines as comments to
                        output
  --err-unknown-lines   treat unknown input configuration lines as errors
  --err-warnings        treat warnings as errors
  --messages-as-comments
                        add program messages as comments to translated config
  --abort-on-error      do not create translation of this input file if an
                        error occurs
  --disable-unused-ports
                        disable additional, unused ports of target switch

supported SOURCE switch models:
    C5G124-24
    C5G124-24P2
    C5G124-48
    C5G124-48P2
    C5K125-24
    C5K125-24P2
    C5K125-48
    C5K125-48P2
    C5K175-24

supported TARGET switch models:
    SummitX460-24p
    SummitX460-24p+2sf
    SummitX460-24p+2sf+4sf
    SummitX460-24p+2xf
    SummitX460-24p+2xf+4sf
    SummitX460-24p+4sf
    SummitX460-24t
    SummitX460-24t+2sf
    SummitX460-24t+2sf+4sf
    SummitX460-24t+2xf
    SummitX460-24t+2xf+4sf
    SummitX460-24t+4sf
    SummitX460-24x
    SummitX460-24x+2sf
    SummitX460-24x+2sf+4sf
    SummitX460-24x+2xf
    SummitX460-24x+2xf+4sf
    SummitX460-24x+4sf
    SummitX460-48p
    SummitX460-48p+2sf
    SummitX460-48p+2sf+4sf
    SummitX460-48p+2xf
    SummitX460-48p+2xf+4sf
    SummitX460-48p+4sf
    SummitX460-48t
    SummitX460-48t+2sf
    SummitX460-48t+2sf+4sf
    SummitX460-48t+2xf
    SummitX460-48t+2xf+4sf
    SummitX460-48t+4sf
    SummitX460-48x
    SummitX460-48x+2sf
    SummitX460-48x+2sf+4sf
    SummitX460-48x+2xf
    SummitX460-48x+2xf+4sf
    SummitX460-48x+4sf

Use a comma separated list of switch models to specify a stack as
source or target switch:

    --source C5K125-48,C5G124-24,C5K125-48P2
    --target SummitX460-48p+2sf,SummitX460-24t,SummitX460-48p+2sf

There must not be any whitespace in the list of switch models!
```

## License

E2X is licensed under the [CDDL 1.0](http://opensource.org/licenses/CDDL-1.0).
See the file [LICENSE.txt](LICENSE.txt) for details.