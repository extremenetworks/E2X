#! /usr/bin/env python3

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

"""Command line interface to E2X

Use the option -h resp. --help to print usage information.
The command line interface of E2X can be used as a filter program.
"""

import argparse
import fileinput
import os
import sys

import CM

progname = 'e2x'
progver = '0.6.4'
progdesc = """\
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
"""


def main():
    return_value = 0
    # get switch models available for translation from core module
    # to populate option parser help output
    c = CM.CoreModule()
    source_switches = sorted(c.get_source_switches())
    target_switches = sorted(c.get_target_switches())
    source_switch_models_help = 'supported SOURCE switch models:'
    for sw in source_switches:
        source_switch_models_help += '\n    ' + sw
    switch_models_help = source_switch_models_help
    target_switch_models_help = 'supported TARGET switch models:'
    for sw in target_switches:
        target_switch_models_help += '\n    ' + sw
    switch_models_help += '\n\n' + target_switch_models_help
    stack_switch_models_help = """\
Use a comma separated list of switch models to specify a stack as
source or target switch:

    --source C5K125-48,C5G124-24,C5K125-48P2
    --target SummitX460-48p+2sf,SummitX460-24t,SummitX460-48p+2sf

There must not be any whitespace in the list of switch models!
"""
    switch_models_help += '\n\n' + stack_switch_models_help

    # option and argument parsing
    parser = argparse.ArgumentParser(
        prog=progname, description=progdesc,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=switch_models_help)
    parser.add_argument('-V', '--version', action='version',
                        version=progname + ' ' + progver)
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='suppress non-error messages')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='print informational messages')
    parser.add_argument('-D', '--debug', action='store_true',
                        help='print debug information')
    parser.add_argument('--source', default='C5K125-48P2',
                        help='source switch model (default %(default)s)')
    parser.add_argument('--target', default='SummitX460-48p+2sf',
                        help='target switch model (default %(default)s)')
    parser.add_argument('-o', '--outfile',
                        help="specify non-default output file, '-' for STDOUT")
    parser.add_argument('-d', '--outdir', default='.',
                        help="specify output directory (default"
                        " '%(default)s')")
    #parser.add_argument('--mgmt-port', action='store_true',
                        #help='use XOS management port instead of'
                        #' in-band management')
    parser.add_argument('--sfp-list',
                        help="list of combo ports with SFP installed, e.g."
                        " 'ge.1.47,ge.1.48'")
    parser.add_argument('--ignore-defaults', action='store_true',
                        help='ignore switch default settings for translation')
    parser.add_argument('--keep-unknown-lines', action='store_true',
                        help='copy unknown input configuration lines to '
                        'output')
    parser.add_argument('--comment-unknown-lines', action='store_true',
                        help='add unknown input configuration lines as'
                        ' comments to output')
    parser.add_argument('--err-unknown-lines', action='store_true',
                        help='treat unknown input configuration lines as'
                        ' errors')
    parser.add_argument('--err-warnings', action='store_true',
                        help='treat warnings as errors')
    parser.add_argument('--messages-as-comments', action='store_true',
                        help='add program messages as comments to translated'
                        ' config')
    parser.add_argument('--abort-on-error', action='store_true',
                        help='do not create translation of this input file'
                        ' if an error occurs')
    parser.add_argument('--disable-unused-ports', action='store_true',
                        help='disable additional, unused ports of target'
                        ' switch')
    parser.add_argument('FILE', nargs='*',
                        help='EOS file to translate (default STDIN)')
    args = parser.parse_args()

    # set core module options
    if args.debug:
        print('DEBUG: Command line arguments:', file=sys.stderr)
        print('DEBUG:', args, file=sys.stderr)
        c.enable_debug()
    if args.ignore_defaults:
        c.disable_defaults()
    if args.keep_unknown_lines:
        c.enable_copy_unknown()
    if args.comment_unknown_lines:
        c.enable_copy_unknown()
        c.enable_comment_unknown()
    if args.disable_unused_ports:
        c.disable_unused_ports()

    # check source switch description
    for sw in args.source.split(','):
        if not sw:
            continue
        if sw not in source_switches:
            print(progname + ':', 'error parsing argument to --source option',
                  file=sys.stderr)
            print('\n' + source_switch_models_help.rstrip())
            print('\n' + stack_switch_models_help.rstrip())
            return 1
    # check target switch description
    for sw in args.target.split(','):
        if not sw:
            continue
        if sw not in target_switches:
            print(progname + ':', 'error parsing argument to --target option',
                  file=sys.stderr)
            print('\n' + target_switch_models_help.rstrip())
            print('\n' + stack_switch_models_help.rstrip())
            return 1

    # initialize source and target switches
    ret, trace = c.set_source_switch(args.source)
    if not ret:
        print('ERROR: Could not set source switch', file=sys.stderr)
        if trace:
            print(trace, file=sys.stderr)
        return 1
    if args.sfp_list:
        ret = c.source.set_combo_using_sfp(args.sfp_list.split(','))
        if ret:
            return_value = 1
            for l in ret:
                print(l, file=sys.stderr)
    if args.debug:
        print('DEBUG: Source switch:', file=sys.stderr)
        print(str(c.source), end='', file=sys.stderr)
    ret, trace = c.set_target_switch(args.target)
    if not ret:
        print('ERROR: Could not set target switch', file=sys.stderr)
        if trace:
            print(trace, file=sys.stderr)
        return 1
    if args.debug:
        print('DEBUG: Target switch:', file=sys.stderr)
        print(str(c.target), end='', file=sys.stderr)

    # provide contents of each input file to translation function
    if not args.FILE:
        args.FILE = ['-']
    outdir = args.outdir.rstrip('/\\')
    if args.debug:
        print("DEBUG: Output directory is '" + outdir + "'", file=sys.stderr)
    for f in args.FILE:
        if args.debug:
            print("DEBUG: Current input file is '" + f + "'", file=sys.stderr)
        if args.outfile:
            outname = args.outfile
        elif f != '-':
            outname = os.path.basename(f)
            if c.target.get_os().lower() == 'xos':
                if outname.lower().endswith('.cfg'):
                    outname = outname[:-4]
                outname += '.xsf'
            else:
                outname += '.e2x'
        else:
            outname = '-'
        if outdir != '.':
            outname = outdir + '/' + outname
        if args.debug:
            print("DEBUG: Current output file is '" + outname + "'",
                  file=sys.stderr)

        # print a help message if reading from an interactive terminal
        if f == '-' and sys.stdin is not None and sys.stdin.isatty():
            comment = c.target.get_cmd().get_comment()
            if sys.platform.startswith('win'):
                eof = 'Z on a line of its own'
            else:
                eof = 'D'
            print(comment, 'Enter', c.source.get_os(),
                  'configuration commands, one per line.',
                  file=sys.stderr)
            print(comment, 'End with CTRL+' + eof, '(sometimes needed twice)',
                  file=sys.stderr)

        # read input configuration line-by-line
        conf = []
        for l in fileinput.input(f):
            conf.append(l.rstrip())
            if args.debug:
                print("DEBUG: Read input config line '" + conf[-1] + "'",
                      file=sys.stderr)

        # translate complete input configuration
        (t_conf, err) = c.translate(conf)

        error_occurred = False
        for l in err:
            if (isinstance(l, str) and l.startswith('ERROR') or
                    (args.err_warnings and l.startswith('WARN')) or
                    (args.err_unknown_lines and
                     'Ignoring unknown command' in l)):
                error_occurred = True

        if args.debug:
            print('DEBUG: Configured source switch:', file=sys.stderr)
            print(str(c.source), end='', file=sys.stderr)
            print('DEBUG: Configured target switch:', file=sys.stderr)
            print(str(c.target), end='', file=sys.stderr)
            print('DEBUG: Translated configuration:', file=sys.stderr)
            print(t_conf, file=sys.stderr)

        # write translated configuration
        if not (args.abort_on_error and error_occurred):
            out = sys.stdout
            if outname != '-':
                out = open(outname, 'w')
                msg = 'NOTICE: Writing translated configuration to file'
                msg += ' "' + outname + '"'
                err.insert(0, msg)
            for l in t_conf:
                if isinstance(l, str):
                    print(l.rstrip(), file=out)
                elif isinstance(l, list):
                    # create ACL file, XOS only!
                    acl_dir = ''
                    if outname != '-':
                        acl_dir = outname[:-3] + 'acls'
                        if not os.path.exists(acl_dir):
                            os.mkdir(acl_dir)
                    acl_name = l.pop(0) + '.pol'
                    acl_entries = ''
                    for acl_entry in l:
                        acl_entries += acl_entry
                    if out == sys.stdout:
                        acl_str = acl_name + '\n' + acl_entries.rstrip()
                        print(c.target.get_cmd().get_comment(), acl_str,
                              file=out)
                    else:
                        acl_out = open(acl_dir + '/' + acl_name, 'w')
                        msg = ('NOTICE: Writing translated ACL file "' +
                               acl_dir + '/' + acl_name + '"')
                        err.append(msg)
                        print(acl_entries.rstrip(), file=acl_out)
                        acl_out.close()
                else:
                    print('ERROR: Unknown configuration line format:', l,
                          file=sys.stderr)
                    return_value = 1
            if args.messages_as_comments:
                if err:
                    print('', file=out)
                for l in err:
                    if (l and (not l.startswith('DEBUG') or args.debug)):
                        print(c.target.get_cmd().get_comment(), l.rstrip(),
                              file=out)
            if outname != '-':
                out.flush()
                out.close()
        else:
            print('NOTICE: Error translating input file "' + str(f) +
                  '", no translation created', file=sys.stderr)
        if args.debug:
            print('DEBUG: Errors:', file=sys.stderr)
        for l in err:
            if (l and isinstance(l, str) and
                    (not l.startswith('DEBUG') or args.debug) and
                    (not l.startswith('INFO') or args.verbose) and
                    (not args.quiet or l.startswith('ERROR') or
                     (args.err_warnings and l.startswith('WARN')) or
                     (args.err_unknown_lines and 'Ignoring unknown command'
                      in l))):
                print(l, file=sys.stderr)
                if (l.startswith('ERROR') or
                    (args.err_warnings and l.startswith('WARN')) or
                    (args.err_unknown_lines and
                     ('Ignoring unknown command' in l))):
                    return_value = 1

    return return_value

if __name__ == '__main__':
    ret = main()
    sys.exit(ret)

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
