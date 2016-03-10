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

import unittest
import sys
import os
import filecmp
import tempfile
sys.path.extend(['../src'])
from scripttest import TestFileEnvironment


class IntegrationTest(unittest.TestCase):

    # check if another script then standard should be used. we don't do good
    # args parsing here because this should be the only arg
    # pop is necessary so unittest does not complain about unknown parameter
    # os.path.normpath is primarily for Windows compatibility
    # note a relative path has TestFileEnvironment dir as origin
    if len(sys.argv) > 1:
        script = os.path.normpath(os.path.abspath(sys.argv.pop(1)))
    else:
        # this needs to be adjusted if the relative path of the e2x script in
        # regards to this file changes
        script = os.path.normpath(
            os.path.abspath("{}/../src/__main__.py".format(
                os.path.dirname(os.path.abspath(__file__)))))

    # list of keywords to ignore in most tests
    # (mostly when NOT using --ignore-defaults)
    jumbo_ignore = ["jumbo-frame"]
    ignore_stpd = ["stpd"]
    ignore_web = ["web"]
    ignore_mgmt = ["enable dhcp vlan"]
    ignore_idle = ["configure idletimeout"]
    default_ignores = (jumbo_ignore + ignore_stpd + ignore_web + ignore_mgmt +
                       ignore_idle)
    ignore_port_mapping = ["INFO: Mapping port", "NOTICE: Mapping port"]
    ignore_unused_ports = ['of target switch is not used']
    ignore_outfile = ["NOTICE: Writing translated configuration to file"]
    ignore_lag_info = ["INFO: LAG ",
                       "NOTICE: XOS always allows single port LAGs"]
    ignore_info_vlan_1 = ['INFO: Cannot rename VLAN 1 from "Default" to '
                          '"DEFAULT VLAN"']
    ignore_stpd_info = ["INFO: Creating XOS equivalent of EOS default MSTP "
                        "respectively RSTP configuration",
                        "INFO: XOS does not support automatic RSTP/MSTP edge "
                        "port detection"]
    ignore_user = ['NOTICE: Ignoring user account "rw" as XOS does not'
                   ' differentiate super-user rights from read-write',
                   'NOTICE: Transfering "ro" user account settings to "user"',
                   'NOTICE: User account "admin" has no password, consider'
                   ' setting with "configure account admin" on XOS',
                   'NOTICE: User account "user" has no password, consider'
                   ' setting with "configure account user" on XOS']

    # EOS has jumbo frames enabled by default
    def_jumbo_conf = ['enable jumbo-frame ports ' + str(i) + '\n'
                      for i in list(range(1, 49)) + list(range(53, 55))]

    # our standard STP compatibility configuration
    std_stp_conf = ['configure stpd s0 delete vlan Default ports all\n',
                    'disable stpd s0 auto-bind vlan Default\n',
                    'configure stpd s0 mode mstp cist\n',
                    'create stpd s1\n',
                    'configure stpd s1 mode mstp msti 1\n',
                    'enable stpd s1 auto-bind vlan Default\n']
    def_stp_conf = std_stp_conf + ['enable stpd s0\n', 'enable stpd s1\n']

    # EOS has webview (HTTP management) enabled by default, XOS 16.1 as well
    def_web_conf = []

    # EOS enables DHCP for the managament IP address by default
    def_mgmt_conf = ['enable dhcp vlan Default\n']

    # EOS uses 5min default idle timeout, XOS 20 min
    def_idle_conf = ['configure idletimeout 5\n']

    # different defaults between EOS and XOS result in normal messages
    def_map_msg = [
        'NOTICE: Mapping port "tg.1.49" to port "53"\n',
        'NOTICE: Mapping port "tg.1.50" to port "54"\n',
        'NOTICE: Port "49" of target switch is not used\n',
        'NOTICE: Port "50" of target switch is not used\n',
        'NOTICE: Port "51" of target switch is not used\n',
        'NOTICE: Port "52" of target switch is not used\n',
    ]
    def_lag_msg = ['NOTICE: XOS always allows single port LAGs\n']
    def_usr_msg = [
        'NOTICE: Ignoring user account "rw" as XOS does not differentiate'
        ' super-user rights from read-write\n',
        'NOTICE: Transfering "ro" user account settings to "user"\n',
        'NOTICE: User account "admin" has no password, consider setting with'
        ' "configure account admin" on XOS\n',
        'NOTICE: User account "user" has no password, consider setting with'
        ' "configure account user" on XOS\n',
    ]

    # default config generated with empty input file
    default_config = (def_jumbo_conf + def_stp_conf + def_web_conf +
                      def_mgmt_conf + def_idle_conf)
    default_messages = def_map_msg + def_lag_msg + def_usr_msg

    # known unknown commands (adjust after learning them)
    unknown_cmds = [
        'set dhcp disable\n',
        'configure vlan VLANName tag 42\n',
        'disable clipaging\n',
        'enable stacking\n',
        'access-list ipv6mode\n',
        'access-list ipv6 acl_1 permit ipv6 host 40:ab:0:0:0:0:0:1 any\n',
        'access-list mac mac_1 permit 33:33:33:33:33:33 any\n',
        'access-group name\n',
        'access-group name in\n',
        'ipv6 access-group name in\n',
        'router id 192.0.2.1\n',
        'interface fubar 0\n',
        'begin something\n',
        'end state\n',
        'set ip protocol unknown\n',
        'set host container\n',
        'set ip unknown\n',
        'set logo\n',
        'set logout fubar\n',
        'set logout 42 minutes\n',
        'set ip address 10.1.1.1 interface vlan.0.2 mask 255.255.255.0\n',
        'set ip address 10.1.1.1 interface vlan.0.2 mask 255.255.255.0 gateway'
        ' 10.0.0.1\n',
        'set radius enable gibberish\n',
        'set tacacs enable gibberish\n',
    ]
    unknown_tmpl = 'NOTICE: Ignoring unknown command "{}"\n'
    unknown_notices = []
    for c in unknown_cmds:
        unknown_notices.append(unknown_tmpl.format(c.strip()))
    unknown_errors = []
    for c in unknown_notices:
        unknown_errors.append(c.replace('NOTICE', 'ERROR', 1))

    # EOS configuration that results in empty translation for XOS
    eos_to_exos_defaults_conf = [
        'set port jumbo disable *.*.*\n',
        'set spantree disable\n',
        'set logout 20\n',
        'clear system login rw\n',
        'set lacp singleportlag enable\n',
        'set ip protocol none\n',
    ]

    @classmethod
    def setUpClass(cls):
        # creates secure tmpdir in system tmpdir with tempfile.mkdtemp() and
        # deletes it at end of context
        cls.tmp = tempfile.TemporaryDirectory(prefix="e2x_tmp-")
        cls.tmpdir = cls.tmp.name
        # the following is purely the appease scripttest
        with open('{}/.scripttest-test-dir.txt'.format(cls.tmpdir), 'w') as f:
            f.write("")

    # old version, could be used if needed for debug
    # set tmpdir to a directory named tmp in the same dir as this script
    # cls.tmpdir = "{}/tmp".format(os.path.dirname(os.path.abspath(__file__)))

    def setUp(self):
        self.script_env = TestFileEnvironment(self.tmpdir)

    def _acl_deny_any(self, nr=20):
        return [
            '# next entry added to match EOS ACL implicit deny\n',
            'entry {}'.format(nr) + ' {\n', '  if {\n',
            '    source-address 0.0.0.0/0;\n', '  } then {\n',
            '    deny;\n', '  }\n', '}\n']

    # for creating test input files, takes filename (relative to scripttest
    # working directory) and list of config strings
    def create_input(self, filename, content):
        with open('{}/{}'.format(self.tmpdir, filename), 'w') as file_input:
            for line in content:
                file_input.write(line)

    # for verifying test output files, takes filename (relative to scriptest
    # working directory) and list of expected strings
    def verify_output(self, filename, expected_content, ignore_this):
        with open('{}/{}'.format(self.tmpdir, filename), 'r') as output_file:
            expected_line = 0
            for content in output_file:
                for keyword in ignore_this:
                    if keyword in content:
                        break
                else:
                    self.assertTrue(expected_line < len(expected_content),
                                    "Unexpected content: {}".format(content))
                    self.assertEqual(expected_content[expected_line], content,
                                     "Unexpected content: {}".format(content))
                    expected_line += 1
        # check for missing expected content
        self.assertEqual(expected_line, len(expected_content),
                         "Missing content line #{}".format(expected_line))

    # verify that the given file does not contain warning messages
    def verify_no_warnings(self, filename):
        with open('{}/{}'.format(self.tmpdir, filename), 'r') as output_file:
            warn_found = False
            for content in output_file:
                if content.startswith('WARN'):
                    warn_found = True
                    break
        # check for missing expected content
        self.assertFalse(warn_found)

    # convenience method for running the standard tests
    def runner(self, testcommands, options, expected_result, ignore_this):
        self.create_input('testinput', testcommands)
        self.script_env.run(self.script, '-otestoutput.xsf', '--quiet',
                            'testinput', *options)
        self.verify_output('testoutput.xsf', expected_result, ignore_this)

    # function to write stderr or stdout return from scripttest to a file so it
    # can be easily analyzed by verify_output
    def stderrToFile(self, stderr, filename):
        with open('{}/{}'.format(self.tmpdir, filename), 'w') as f:
            for line in stderr.splitlines():
                f.write("{}\n".format(line.rstrip()))

# basic functionality tests
    def test_case_017(self):  # check if stdout output and stdin input works
        ret = self.script_env.run(self.script, '--ignore-defaults',
                                  expect_stderr=True,
                                  stdin=str.encode("set port enable ge.1.1\n"))
        self.assertEqual(ret.stdout, "enable ports 1\n")

    def test_case_018(self):  # check if output file option works
        self.create_input('test.cfg', ["set port enable ge.1.1\n"])
        self.script_env.run(self.script, '-oXOS.xsf', 'test.cfg',
                            '--ignore-defaults', expect_stderr=True)
        # check if output is a file
        self.assertTrue(os.path.isfile('{}/XOS.xsf'.format(self.tmpdir)),
                        "Output not a file")
        # check if output is right
        self.verify_output('XOS.xsf', ["enable ports 1\n"], [])

    def test_case_054(self):  # check if -o works for absolute paths
        self.create_input('test.cfg', ["set port enable ge.1.1\n"])
        self.script_env.run(self.script, '-o{}/XOS.xsf'.format(self.tmpdir),
                            'test.cfg', '--ignore-defaults',
                            expect_stderr=True)
        # check if output is a file
        self.assertTrue(os.path.isfile('{}/XOS.xsf'.format(self.tmpdir)),
                        "Output not a file")
        # check if output is right
        self.verify_output('XOS.xsf', ["enable ports 1\n"], [])

    def test_case_019(self):  # check if output dir option works
        self.create_input('config.cfg', ["set port enable ge.1.1\n"])
        os.mkdir('{}/test'.format(self.tmpdir))
        self.script_env.run(self.script, '-d./test', 'config.cfg',
                            '--ignore-defaults', expect_stderr=True)
        # check if output is a file at the right place with the right name
        self.assertTrue(os.path.isfile('{}/test/config.xsf'.format(
                                       self.tmpdir)), "Output not a file")
        # check if output is right
        self.verify_output('test/config.xsf', ["enable ports 1\n"], [])

    def test_case_020(self):  # check if --quiet works
        self.create_input('empty.cfg', [])
        self.script_env.run(self.script, '-oout.xsf', 'empty.cfg',
                            '--ignore-defaults', '--quiet')
        # scripttest raises error if our port notices are written (to stderr)

    def test_case_021(self):  # check if --sfp-list works
        self.create_input('test.cfg', ["set port enable ge.1.47\n"])
        self.script_env.run(self.script, '-oout.xsf', 'test.cfg',
                            '--ignore-defaults', '--sfp-list', 'ge.1.47',
                            '--quiet')
        # test if port is correctly mapped to first free SFP port
        self.verify_output('out.xsf', ["enable ports 49\n"], [])

    def test_case_095(self):  # check if unknown lines are reported
        self.create_input('test.cfg', self.unknown_cmds)
        ret = self.script_env.run(self.script, '-otest.xsf', 'test.cfg',
                                  '--ignore-defaults', expect_error=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr', self.unknown_notices,
                           self.default_ignores + self.ignore_outfile +
                           self.ignore_lag_info + self.ignore_info_vlan_1 +
                           self.ignore_port_mapping + self.ignore_stpd_info +
                           self.ignore_unused_ports)
        # check that no error return code is set
        self.assertEqual(ret.returncode, 0, "Wrong exit code")

    def test_case_022(self):  # check if --keep-unknown-lines works
        self.create_input('test.cfg', self.unknown_cmds)
        self.script_env.run(self.script, '-otest.xsf', 'test.cfg',
                            '--ignore-defaults', '--keep-unknown-lines',
                            '--quiet')
        # verify if line untouched and has a newline before it
        self.verify_output('test.xsf', ["\n"] + self.unknown_cmds, [])

    def test_case_023(self):  # check if --comment-unknown-lines works
        self.create_input('test.cfg', self.unknown_cmds)
        self.script_env.run(self.script, '-otest.xsf', 'test.cfg',
                            '--ignore-defaults', '--comment-unknown-lines',
                            '--quiet')
        # verify if line is commented with XOS comment char and has a newline
        # before it
        commented_cmds = ['\n'] + ['# ' + c for c in self.unknown_cmds]
        self.verify_output('test.xsf', commented_cmds, [])

    def test_case_024(self):  # check if --err-unknown-lines works
        self.create_input('test.cfg', self.unknown_cmds)
        ret = self.script_env.run(self.script, '-otest.xsf', 'test.cfg',
                                  '--ignore-defaults', '--err-unknown-lines',
                                  '--quiet', expect_error=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr', self.unknown_errors,
                           self.default_ignores + self.ignore_outfile +
                           self.ignore_lag_info + self.ignore_info_vlan_1 +
                           self.ignore_port_mapping + self.ignore_stpd_info +
                           self.ignore_unused_ports)
        # check if error return code is set
        self.assertEqual(ret.returncode, 1, "Wrong exit code")

    def test_case_025(self):  # check if --ignore-defaults works
        # test on empty config
        self.create_input('empty.cfg', [""])
        self.script_env.run(self.script, '-otest-normal.xsf', 'empty.cfg',
                            '--quiet')
        self.script_env.run(self.script, '-otest-ignore.xsf', 'empty.cfg',
                            '--ignore-defaults', '--quiet')
        # check if both files were created
        self.assertTrue(os.path.isfile('{}/test-normal.xsf'.format(
                        self.tmpdir)), "test-normal.xsf is missing")
        self.assertTrue(os.path.isfile('{}/test-ignore.xsf'.format(
                        self.tmpdir)), "test-ignore.xsf is missing")
        # the 2 output files should not be the same
        self.assertFalse(filecmp.cmp('{}/test-normal.xsf'.format(self.tmpdir),
                                     '{}/test-ignore.xsf'.format(self.tmpdir)),
                         "same output with and without --ignore-defaults")

    def test_case_026(self):  # check if --abort-on-error works
        # needs another command if set dhcp is ever implemented
        self.create_input('test.cfg',
                          ["set port enable ge.1.1\n", "set dhcp disable\n",
                           "set port enable ge.1.2\n"])
        ret = self.script_env.run(self.script, '-otest.xsf', 'test.cfg',
                                  '--ignore-defaults', '--err-unknown-lines',
                                  '--abort-on-error', '--quiet',
                                  expect_error=True)
        # check if error return code is set
        self.assertEqual(ret.returncode, 1, "Wrong exit code")
        # check if the output file is there (it should be not)
        self.assertFalse(os.path.isfile('{}/test.xsf'.format(self.tmpdir)),
                         "Output file should not exist")

    def test_case_027(self):  # check if --messages-as-comments works
        # test on empty config
        self.create_input('empty.cfg', [""])
        ret = self.script_env.run(self.script, '-otest.xsf', 'empty.cfg',
                                  '--ignore-defaults', '--verbose',
                                  '--messages-as-comments', expect_stderr=True)
        # check if output is stderr with comment char and leading newline
        with open('{}/test.xsf'.format(self.tmpdir), 'r') as output_file:
            # test for expected leading empty line
            self.assertEqual(output_file.readline(), "\n")
            # check rest line for line
            for line in ret.stderr.splitlines():
                self.assertEqual("# {}".format(line),
                                 output_file.readline().rstrip())

    def test_case_028(self):  # check if --disable-unused-ports works
        # test on empty config
        self.runner([""], ['--ignore-defaults', '--disable-unused-ports'],
                    ['disable ports 49\n', 'disable ports 50\n',
                     'disable ports 51\n', 'disable ports 52\n'], [])

    def test_case_029(self):  # check if --verbose works
        self.create_input('comment.cfg', ["# this is a comment"])
        ret = self.script_env.run(self.script, '-ocomment.xsf', 'comment.cfg',
                                  '--ignore-defaults', '--verbose',
                                  expect_stderr=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr',
                           ['INFO: Ignoring comment "# this is a comment"\n'],
                           ["NOTICE", 'INFO: LAG',
                            'NOTICE: XOS always allows single port LAGs'] +
                           self.ignore_port_mapping)

    def test_case_075(self):  # check that --ignore-defaults does not WARN
        self.create_input('empty.cfg', [''])
        ret = self.script_env.run(self.script, '-oempty.xsf', 'empty.cfg',
                                  '--ignore-defaults', '--verbose',
                                  expect_stderr=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_no_warnings('stderr')

    def test_case_076(self):  # check --ignore-defaults messages
        self.create_input('empty.cfg', [''])
        ret = self.script_env.run(self.script, '-oempty.xsf', 'empty.cfg',
                                  '--ignore-defaults', expect_stderr=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr',
                           ['NOTICE: Writing translated configuration to file'
                            ' "empty.xsf"\n',
                            'NOTICE: Mapping port "tg.1.49" to port "53"\n',
                            'NOTICE: Mapping port "tg.1.50" to port "54"\n',
                            'NOTICE: Port "49" of target switch is not used\n',
                            'NOTICE: Port "50" of target switch is not used\n',
                            'NOTICE: Port "51" of target switch is not used\n',
                            'NOTICE: Port "52" of target switch is not used'
                            '\n'],
                           [])

# FM ports
    def test_case_001(self):
        self.runner(["set port enable ge.1.1\n"], ['--ignore-defaults'],
                    ["enable ports 1\n"], [])

    def test_case_002(self):
        self.runner(["set port enable tg.1.49\n"], ['--ignore-defaults'],
                    ["enable ports 53\n"], [])

    def test_case_003(self):
        self.runner(["set port disable ge.1.1\n"], [], ["disable ports 1\n"],
                    self.default_ignores)

    def test_case_004(self):
        self.runner(["set port disable tg.1.50\n"], [], ["disable ports 54\n"],
                    self.default_ignores)

    def test_case_005(self):
        self.runner(['set port alias ge.1.10 "Port alias longer than 20 '
                     'characters"\n'], [],
                    ["configure ports 10 display-string Port_alias_long"
                     "\n", 'configure ports 10 description-string "Port_alias'
                     '_longer_than_20_characters"\n'], self.default_ignores)

    def test_case_006(self):
        self.runner(['set port speed ge.1.7 100\n',
                     'set port duplex ge.1.7 full\n',
                     'set port negotiation ge.1.7 disable\n'], [],
                    ["configure ports 7 auto off speed 100 duplex full\n"],
                    self.default_ignores)

    def test_case_007(self):
        self.runner(['set port duplex ge.1.8 full\n',
                     'set port negotiation ge.1.8 disable\n'], [],
                    ["configure ports 8 auto off speed 10 duplex full\n"],
                    self.default_ignores)

    def test_case_008(self):
        self.runner(['set port negotiation ge.1.9 disable\n'], [],
                    ["configure ports 9 auto off speed 10 duplex half\n"],
                    self.default_ignores)

    def test_case_009(self):
        # test if empty input triggers correct jumbo frame handling
        expected_content = []
        # generate the expected result because we don't want to type 50 lines
        for i in range(1, 49):
            expected_content.append("enable jumbo-frame ports {}\n".format(i))
        expected_content.append("enable jumbo-frame ports 53\n")
        expected_content.append("enable jumbo-frame ports 54\n")
        self.runner([""], [], expected_content, self.ignore_stpd +
                    self.ignore_web + self.ignore_mgmt + self.ignore_idle)

    def test_case_010(self):
        self.runner(['set port jumbo disable ge.1.12'], [], [],
                    ["enable jumbo-frame"] + self.ignore_stpd +
                    self.ignore_web + self.ignore_mgmt + self.ignore_idle)
        # expected output <empty>

    def test_case_011(self):
        self.runner(['set port jumbo disable ge.1.12'], ['--ignore-defaults'],
                    ["disable jumbo-frame ports 12\n"], [])

# FM VLAN
    def test_case_012(self):
        self.runner(['set vlan create 100\n', 'set vlan name 100 DATA'],
                    [], ["create vlan DATA tag 100\n"], self.default_ignores)

    def test_case_013(self):
        self.runner(['set vlan create 100\n'], [],
                    ["create vlan VLAN_0100 tag 100\n"],
                    self.default_ignores)

    def test_case_014(self):
        self.create_input('testinput', ['set vlan create 100\n',
                                        'set port vlan ge.1.1 100'])
        ret = self.script_env.run(self.script, '-otestoutput.xsf',
                                  'testinput', '--quiet', expect_error=True,
                                  expect_stderr=True)
        self.assertEqual(ret.returncode, 1, "Wrong exit code")
        # TODO maybe check error message
        # expected output <Error message caused by configuration not supported
        #  on XOS> because of not modifying egress

    def test_case_015(self):
        self.runner(['set vlan create 100\n', 'set port vlan ge.1.1 100\n',
                     'clear vlan egress 1 ge.1.1\n',
                     'set vlan egress 100 ge.1.1 untagged\n'],
                    [],
                    ["configure vlan Default delete ports 1\n",
                     "create vlan VLAN_0100 tag 100\n",
                     "configure vlan VLAN_0100 add ports 1 untagged\n"],
                    self.default_ignores)

    def test_case_030(self):
        self.create_input('testinput', ['set port vlan ge.1.1 100'])
        ret = self.script_env.run(self.script, '-o testoutput.xsf',
                                  'testinput', '--quiet', expect_error=True,
                                  expect_stderr=True)
        self.assertEqual(ret.returncode, 1, "Wrong exit code")
        self.assertEqual(ret.stderr, "ERROR: VLAN 100 not found (set port "
                                     "vlan ge.1.1 100)\n", "Unexpected Error")
        # expected output <ERROR: VLAN 100 not found (set port vlan)> because
        # there is no VLAN 100 yet

    def test_case_016(self):
        self.runner(['set vlan create 200\n',
                     'set vlan name 200 VOICE\n',
                     'set port vlan ge.1.2 200\n',
                     'clear vlan egress 1 ge.1.2\n',
                     'set vlan egress 200 ge.1.2 untagged\n'],
                    ['--ignore-defaults'],
                    ["configure vlan Default delete ports 2\n",
                     "create vlan VOICE tag 200\n",
                     "configure vlan VOICE add ports 2 untagged\n"], [])

    def test_case_031(self):
        self.runner(['set vlan create 2,3\n',
                     'set vlan egress 2 ge.1.2-5 tagged\n',
                     'set vlan egress 3 ge.1.2-5 tagged\n',
                     'clear vlan egress 2,3 ge.1.4\n'],
                    ['--ignore-defaults', '--quiet'],
                    ['create vlan VLAN_0002 tag 2\n',
                     'configure vlan VLAN_0002 add ports 2-3,5 tagged\n',
                     'create vlan VLAN_0003 tag 3\n',
                     'configure vlan VLAN_0003 add ports 2-3,5 tagged\n'],
                    [])

    def test_case_032(self):
        self.runner(['set port jumbo disable *.*.*\n',
                     'set vlan create 4,10,20,100-105,666,1000,3001-3010\n',
                     'set vlan name 4 ADMIN\n', 'set vlan name 10 DATA\n',
                     'set vlan name 20 VOICE\n', 'set vlan name 100 "VMK"\n',
                     'set vlan name 101 "VIRTUAL SERVER 1"\n',
                     'set vlan name 102 "VIRTUAL SERVER 2"\n',
                     'set vlan name 103 "VIRTUAL SERVER 3"\n',
                     'set vlan name 104 "VIRTUAL SERVER 4"\n',
                     'set vlan name 105 "VIRTUAL SERVER 5"\n',
                     'set vlan name 666 "UNUSED PORTS"\n',
                     'set vlan name 1000 "NATIVE"\n',
                     'set port vlan ge.1.1-40 10 modify-egress\n',
                     'set vlan egress 20 ge.1.1-40 tagged\n',
                     'set port vlan ge.1.41-44 100 modify-egress\n',
                     'set vlan egress 101-105 ge.1.45-46 tagged\n',
                     'clear vlan egress 1 ge.1.45-46;tg.*.*\n',
                     'set port vlan ge.1.45-48;tg.*.* 1000\n',
                     'set vlan egress 1000 ge.1.45-48;tg.*.* untagged\n',
                     'set port vlan ge.1.47-48 666 modify-egress\n',
                     'set port disable ge.1.47-48\n',
                     'set vlan egress 4,10,20,100-105,666,3001-3010 tg.*.* '
                     'tagged\n'], [],
                    ['disable ports 47\n',
                     'disable ports 48\n',
                     'configure vlan Default delete ports 1-48,53-54\n',
                     'create vlan ADMIN tag 4\n',
                     'configure vlan ADMIN add ports 53-54 tagged\n',
                     'create vlan DATA tag 10\n',
                     'configure vlan DATA add ports 1-40 untagged\n',
                     'configure vlan DATA add ports 53-54 tagged\n',
                     'create vlan VOICE tag 20\n',
                     'configure vlan VOICE add ports 1-40,53-54 tagged\n',
                     'create vlan VMK tag 100\n',
                     'configure vlan VMK add ports 41-44 untagged\n',
                     'configure vlan VMK add ports 53-54 tagged\n',
                     'create vlan VIRTUAL_SERVER_1 tag 101\n',
                     'configure vlan VIRTUAL_SERVER_1 add ports 45-46,53-54 '
                     'tagged\n',
                     'create vlan VIRTUAL_SERVER_2 tag 102\n',
                     'configure vlan VIRTUAL_SERVER_2 add ports 45-46,53-54 '
                     'tagged\n',
                     'create vlan VIRTUAL_SERVER_3 tag 103\n',
                     'configure vlan VIRTUAL_SERVER_3 add ports 45-46,53-54 '
                     'tagged\n',
                     'create vlan VIRTUAL_SERVER_4 tag 104\n',
                     'configure vlan VIRTUAL_SERVER_4 add ports 45-46,53-54 '
                     'tagged\n',
                     'create vlan VIRTUAL_SERVER_5 tag 105\n',
                     'configure vlan VIRTUAL_SERVER_5 add ports 45-46,53-54 '
                     'tagged\n',
                     'create vlan UNUSED_PORTS tag 666\n',
                     'configure vlan UNUSED_PORTS add ports 47-48 untagged\n',
                     'configure vlan UNUSED_PORTS add ports 53-54 tagged\n',
                     'create vlan NATIVE tag 1000\n',
                     'configure vlan NATIVE add ports 45-46,53-54 untagged\n',
                     'create vlan VLAN_3001 tag 3001\n',
                     'configure vlan VLAN_3001 add ports 53-54 tagged\n',
                     'create vlan VLAN_3002 tag 3002\n',
                     'configure vlan VLAN_3002 add ports 53-54 tagged\n',
                     'create vlan VLAN_3003 tag 3003\n',
                     'configure vlan VLAN_3003 add ports 53-54 tagged\n',
                     'create vlan VLAN_3004 tag 3004\n',
                     'configure vlan VLAN_3004 add ports 53-54 tagged\n',
                     'create vlan VLAN_3005 tag 3005\n',
                     'configure vlan VLAN_3005 add ports 53-54 tagged\n',
                     'create vlan VLAN_3006 tag 3006\n',
                     'configure vlan VLAN_3006 add ports 53-54 tagged\n',
                     'create vlan VLAN_3007 tag 3007\n',
                     'configure vlan VLAN_3007 add ports 53-54 tagged\n',
                     'create vlan VLAN_3008 tag 3008\n',
                     'configure vlan VLAN_3008 add ports 53-54 tagged\n',
                     'create vlan VLAN_3009 tag 3009\n',
                     'configure vlan VLAN_3009 add ports 53-54 tagged\n',
                     'create vlan VLAN_3010 tag 3010\n',
                     'configure vlan VLAN_3010 add ports 53-54 tagged\n'],
                    self.ignore_stpd + self.ignore_web + self.ignore_mgmt +
                    self.ignore_idle)

    def test_case_033(self):
        self.runner(['set vlan create 2\n', 'set vlan create 3\n'],
                    ['--ignore-defaults', '--quiet'],
                    ['create vlan VLAN_0002 tag 2\n',
                     'create vlan VLAN_0003 tag 3\n'], [])

    def test_case_034(self):
        self.runner(['set vlan create 2,3\n'],
                    ['--ignore-defaults', '--quiet'],
                    ['create vlan VLAN_0002 tag 2\n',
                     'create vlan VLAN_0003 tag 3\n'], [])

    def test_case_120(self):
        self.runner(['set vlan create 3,2\n'],
                    ['--ignore-defaults', '--quiet'],
                    ['create vlan VLAN_0003 tag 3\n',
                     'create vlan VLAN_0002 tag 2\n'], [])

    def test_case_121(self):
        self.runner(['set vlan create 2-3\n'],
                    ['--ignore-defaults', '--quiet'],
                    ['create vlan VLAN_0002 tag 2\n',
                     'create vlan VLAN_0003 tag 3\n'], [])

    def test_case_035(self):
        self.runner(['set vlan create 2,3\n',
                     'set port vlan ge.1.2 2 modify-egress\n',
                     'set port vlan ge.1.3 3 modify-egress\n'],
                    ['--ignore-defaults', '--quiet'],
                    ['configure vlan Default delete ports 2-3\n',
                     'create vlan VLAN_0002 tag 2\n',
                     'configure vlan VLAN_0002 add ports 2 untagged\n',
                     'create vlan VLAN_0003 tag 3\n',
                     'configure vlan VLAN_0003 add ports 3 untagged\n'], [])

    def test_case_036(self):
        self.runner(['set vlan create 2,3\n',
                     'set vlan egress 2 ge.1.1 tagged\n',
                     'set vlan egress 3 ge.1.1 tagged\n'],
                    ['--ignore-defaults', '--quiet'],
                    ['create vlan VLAN_0002 tag 2\n',
                     'configure vlan VLAN_0002 add ports 1 tagged\n',
                     'create vlan VLAN_0003 tag 3\n',
                     'configure vlan VLAN_0003 add ports 1 tagged\n'], [])

    def test_case_037(self):
        self.runner(['set vlan create 2,3\n',
                     'set vlan egress 2,3 ge.1.1 tagged\n'],
                    ['--ignore-defaults', '--quiet'],
                    ['create vlan VLAN_0002 tag 2\n',
                     'configure vlan VLAN_0002 add ports 1 tagged\n',
                     'create vlan VLAN_0003 tag 3\n',
                     'configure vlan VLAN_0003 add ports 1 tagged\n'], [])

    def test_case_038(self):
        self.runner(['set vlan create 2,100,200\n',
                     'set vlan name 2 ADMIN\n'
                     'set vlan name 100 DATA\n',
                     'set vlan name 200 VOICE\n',
                     'set port vlan ge.*.* 100 modify-egress\n',
                     'set vlan egress 200 ge.*.* tagged\n',
                     'set vlan egress 2,100,200 tg.*.* tagged\n'],
                    ['--ignore-defaults', '--quiet'],
                    ['configure vlan Default delete ports 1-48\n',
                     'create vlan ADMIN tag 2\n',
                     'configure vlan ADMIN add ports 53-54 tagged\n',
                     'create vlan DATA tag 100\n',
                     'configure vlan DATA add ports 1-48 untagged\n',
                     'configure vlan DATA add ports 53-54 tagged\n',
                     'create vlan VOICE tag 200\n',
                     'configure vlan VOICE add ports 1-48,53-54 tagged\n'], [])

    def test_case_039(self):
        self.create_input('testinput', ['set vlan create 2\n', 'set vlan name '
                                        '2 Mgmt\n'])
        ret = self.script_env.run(self.script, '-otestoutput', 'testinput',
                                  '--ignore-defaults', '--quiet',
                                  expect_error=True)
        self.verify_output('testoutput', ['create vlan VLAN_0002 tag 2\n'],
                           [])
        self.assertEqual(ret.returncode, 1, "Wrong exit code")
        self.assertEqual(ret.stderr, 'ERROR: Cannot use name "Mgmt" for '
                         'regular VLAN\n', "Wrong error message")

    def test_case_040(self):
        self.create_input('testinput', ['set vlan create 2\n', 'set vlan name '
                                        '2 Mgmt\n', 'set port vlan ge.1.1 2 '
                                        'modify-egress\n'])
        ret = self.script_env.run(self.script, '-otestoutput', 'testinput',
                                  '--ignore-defaults', '--quiet',
                                  expect_error=True)
        self.verify_output('testoutput',
                           ['configure vlan Default delete ports 1\n', 'create'
                            ' vlan VLAN_0002 tag 2\n', 'configure vlan '
                            'VLAN_0002 add ports 1 untagged\n'], [])
        self.assertEqual(ret.returncode, 1, "Wrong exit code")
        self.assertEqual(ret.stderr, 'ERROR: Cannot use name "Mgmt" for '
                         'regular VLAN\n', "Wrong error message")

    def test_case_041(self):
        self.create_input('testinput', ['set vlan name 1 "A Name"\n'])
        ret = self.script_env.run(self.script, '-otestoutput', 'testinput',
                                  '--ignore-defaults', '--quiet',
                                  expect_error=True)
        self.verify_output('testoutput', [], [])
        self.assertEqual(ret.returncode, 1, "Wrong exit code")
        self.assertEqual(ret.stderr, 'ERROR: Cannot rename VLAN 1 from '
                         '"Default" to "A Name"\n', "Wrong error message")

    def test_case_042(self):
        self.create_input('testinput', [])
        ret = self.script_env.run(self.script, '-otestoutput', 'testinput',
                                  '--verbose', expect_stderr=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr', ['INFO: Cannot rename VLAN 1 from '
                                      '"Default" to "DEFAULT VLAN"\n'],
                           ['NOTICE', 'INFO: LAG',
                            'NOTICE: XOS always allows single port LAGs',
                            'INFO: Creating XOS equivalent of EOS default MSTP'
                            ' respectively RSTP configuration',
                            'INFO: XOS does not support automatic RSTP/MSTP'
                            ' edge port detection'] +
                           self.ignore_port_mapping + self.ignore_user)

    def test_case_043(self):
        self.create_input('testinput', ['set vlan name 1 "DEFAULT VLAN"\n'])
        ret = self.script_env.run(self.script, '-otestoutput', 'testinput',
                                  '--ignore-defaults', '--quiet',
                                  expect_error=True)
        self.verify_output('testoutput', [], [])
        self.assertEqual(ret.returncode, 1, "Wrong exit code")
        self.assertEqual(ret.stderr, 'ERROR: Cannot rename VLAN 1 from "'
                         'Default" to "DEFAULT VLAN"\n', "Wrong error message")

    def test_case_044(self):
        self.runner(['set vlan name 1 "Default"\n'],
                    ['--ignore-defaults', '--quiet'], [], [])

    def test_case_045(self):
        self.runner(['set vlan name 1 Default\n'],
                    ['--ignore-defaults', '--quiet'], [], [])

    def test_case_046(self):
        self.create_input('testinput', ['set vlan create 2\n', 'set vlan '
                                        'egress 2 ge.1.1 untagged\n'])
        ret = self.script_env.run(self.script, '-otestoutput', 'testinput',
                                  '--ignore-defaults', '--quiet',
                                  expect_error=True)
        self.assertEqual(ret.returncode, 1, "Wrong exit code")
        self.assertEqual(ret.stderr,
                         'ERROR: Port "1" has multiple untagged egress VLANs: '
                         '(\'Default\', 1) (\'VLAN_0002\', 2)\n'
                         'ERROR: Untagged VLAN egress and ingress differs for '
                         'port "1"\n',
                         "Wrong error message")

    def test_case_122(self):
        self.create_input('testinput',
                          ['set vlan create 2\n',
                           'set port vlan ge.1.1 2\n',
                           'set vlan egress 2 ge.1.1 tagged\n',
                           'clear vlan egress 1 ge.1.1\n',
                           ])
        ret = self.script_env.run(self.script, '-otestoutput', 'testinput',
                                  '--ignore-defaults', '--quiet')
        self.verify_output('testoutput',
                           ['configure vlan Default delete ports 1\n',
                            'create vlan VLAN_0002 tag 2\n',
                            'configure vlan VLAN_0002 add ports 1 tagged\n',
                            ],
                           [])
        self.assertEqual(ret.stderr, '', "Wrong error message")

    def test_case_127(self):
        self.create_input('testinput', ['clear vlan egress 1 ge.1.1\n'])
        ret = self.script_env.run(self.script, '-otestoutput', 'testinput',
                                  '--ignore-defaults', '--quiet')
        self.verify_output('testoutput',
                           ['configure vlan Default delete ports 1\n'],
                           [])
        self.assertEqual(ret.stderr, '', "Wrong error message")

    def test_case_128(self):
        self.create_input('testinput', ['clear vlan egress 1 ge.1.1\n'])
        ret = self.script_env.run(self.script, '-otestoutput', 'testinput',
                                  '--ignore-defaults', expect_error=True)
        self.assertEqual(ret.returncode, 0, "Wrong exit code")
        self.verify_output('testoutput',
                           ['configure vlan Default delete ports 1\n'],
                           [])
        self.assertIn('NOTICE: Port "1" has PVID of 1, but VLAN 1 missing '
                      'from egress, ignoring PVID', ret.stderr)

# FM LACP
    def test_case_047(self):
        self.create_input('testinput',
                          ['set lacp aadminkey lag.0.1 100\n',
                           'set port lacp port ge.1.1 aadminkey 100 enable\n',
                           'set port lacp port ge.1.1 enable\n'])
        ret = self.script_env.run(self.script, '-o-', 'testinput',
                                  '--ignore-defaults', '--quiet',
                                  expect_error=True)
        self.assertEqual(ret.returncode, 1, "Wrong exit code")
        self.assertEqual(ret.stderr, 'ERROR: LAG consisting of one port ("1") '
                         'only, but single port LAG not enabled on source '
                         'switch\n')
        self.assertEqual(ret.stdout, 'enable sharing 1 grouping 1 algorithm '
                         'address-based L3 lacp\n')

    def test_case_048(self):
        self.runner(['set lacp aadminkey lag.0.1 100\n',
                     'set port lacp port ge.1.1 aadminkey 100 enable\n',
                     'set port lacp port ge.1.1 enable\n',
                     'set port lacp port ge.1.2 aadminkey 100 enable\n',
                     'set port lacp port ge.1.2 enable\n'], [],
                    ['enable sharing 1 grouping 1-2 algorithm address-based L3'
                     ' lacp\n', 'configure vlan Default delete ports 2\n'],
                    self.default_ignores)

    def test_case_049(self):
        self.runner(['set lacp singleportlag enable\n',
                     'set lacp aadminkey lag.0.1 100\n',
                     'set port lacp port ge.1.1 aadminkey 100 enable\n',
                     'set port lacp port ge.1.1 enable\n'], [],
                    ['enable sharing 1 grouping 1 algorithm address-based L3 '
                     'lacp\n'], self.default_ignores)

    def test_case_050(self):
        self.runner(['set lacp static lag.0.1 ge.1.1-2\n'], [],
                    ['enable sharing 1 grouping 1-2 algorithm address-based '
                     'L3\n',
                     'configure vlan Default delete ports 2\n'],
                    self.default_ignores)

    def test_case_051(self):
        self.runner(['set lacp static lag.0.1 ge.1.1-2\n',
                     'set vlan create 2\n',
                     'set vlan name 2 Two\n',
                     'set port vlan lag.0.1 2 modify-egress\n'], [],
                    ['enable sharing 1 grouping 1-2 algorithm address-based '
                     'L3\n',
                     'configure vlan Default delete ports 1-2\n',
                     'create vlan Two tag 2\n',
                     'configure vlan Two add ports 1 untagged\n'],
                    self.default_ignores)

    def test_case_052(self):
        self.runner(['set lacp static lag.0.1 ge.1.1-2\n',
                     'set vlan create 2\n',
                     'set vlan name 2 Two\n',
                     'set port vlan lag.0.1;ge.1.1-2 2 modify-egress\n'], [],
                    ['enable sharing 1 grouping 1-2 algorithm address-based '
                     'L3\n',
                     'configure vlan Default delete ports 1-2\n',
                     'create vlan Two tag 2\n',
                     'configure vlan Two add ports 1 untagged\n'],
                    self.default_ignores)

    def test_case_053(self):
        self.runner(['set lacp aadminkey lag.0.6 6\n',
                     'set port lacp port tg.1.49,50 enable\n',
                     'set port lacp port tg.1.49,50 aadminkey 6\n'], [],
                    ['enable sharing 53 grouping 53-54 algorithm address-based'
                     ' L3 lacp\n',
                     'configure vlan Default delete ports 54\n'],
                    self.default_ignores)

    def test_case_055(self):
        self.runner(['set port disable lag.*.*\n'], [], [],
                    self.default_ignores)

    def test_case_056(self):
        self.create_input('testinput', ['set lacp aadminkey lag.0.1 100\n'])
        ret = self.script_env.run(self.script, '-o-', 'testinput',
                                  '--ignore-defaults', '--quiet',
                                  expect_error=True)
        self.assertEqual(ret.returncode, 1, "Wrong exit code")
        self.assertEqual(ret.stderr,
                         'ERROR: LAG "lag.0.1" is configured, but not mapped'
                         ' to target switch\n')
        self.assertEqual(ret.stdout, '')

    def test_case_057(self):
        self.create_input('testinput', ['set lacp static lag.0.1\n'])
        ret = self.script_env.run(self.script, '-o-', 'testinput',
                                  '--ignore-defaults', '--quiet',
                                  expect_error=True)
        self.assertEqual(ret.returncode, 1, "Wrong exit code")
        self.assertEqual(ret.stderr,
                         'ERROR: LAG "lag.0.1" is configured, but not mapped'
                         ' to target switch\n')
        self.assertEqual(ret.stdout, '')

    def test_case_058(self):
        self.create_input('testinput', ['set lacp disable\n'])
        ret = self.script_env.run(self.script, '-o-', 'testinput',
                                  '--ignore-defaults', '--quiet',
                                  expect_error=True)
        self.assertEqual(ret.returncode, 1, "Wrong exit code")
        self.assertEqual(ret.stderr, 'ERROR: LACP cannot be enabled/disabled '
                         'globally on XOS\n')
        self.assertEqual(ret.stdout, '')

    def test_case_059(self):
        expected_content = []
        # generate the expected result because we don't want to type a line
        # for each of the 48 disabled ports
        for i in range(1, 49):
            expected_content.append('disable ports {}\n'.format(i))
        self.runner(['set port disable ge.*.*\n',
                     'set port lacp port *.*.* disable\n'],
                    [], expected_content,
                    self.default_ignores)

    def test_case_123(self):
        self.create_input('testinput', ['set port alias lag.0.1 "LAG One"\n'])
        ret = self.script_env.run(self.script, '-o-', 'testinput',
                                  '--ignore-defaults', '--log-level=WARN',
                                  expect_error=True)
        self.assertEqual(ret.returncode, 1, "Wrong exit code")
        self.assertEqual(ret.stderr,
                         'WARN: LAG "lag.0.1" cannot be mapped to target '
                         'switch\n'
                         'ERROR: LAG "lag.0.1" is configured, but not mapped'
                         ' to target switch\n')
        self.assertEqual(ret.stdout, '')

    def test_case_124(self):
        self.create_input('testinput',
                          ['set port alias lag.0.1 "LAG One"\n',
                           'set port lacp port ge.1.1-2 enable\n',
                           ])
        ret = self.script_env.run(self.script, '-otestoutput', 'testinput',
                                  '--log-level=WARN')
        self.verify_output('testoutput',
                           [
                               'enable sharing 1 grouping 1-2 algorithm '
                               'address-based L3 lacp\n',
                               'configure ports 1 display-string LAG_One\n',
                               'configure ports 2 display-string LAG_One\n',
                               'configure ports 1 description-string '
                               '"LAG_One"\n',
                               'configure ports 2 description-string '
                               '"LAG_One"\n',
                               'configure vlan Default delete ports 2\n',
                           ],
                           self.default_ignores)
        self.assertEqual(ret.stderr, '')

    def test_case_125(self):
        self.create_input('testinput',
                          [
                              'set vlan create 2\n',
                              'set vlan name 2 "VLAN 2"\n',
                              'set port vlan lag.0.1 2 modify-egress\n',
                              'set port lacp port ge.1.1-2 enable\n',
                          ])
        ret = self.script_env.run(self.script, '-otestoutput', 'testinput',
                                  '--log-level=ERROR')
        self.verify_output('testoutput',
                           [
                               'enable sharing 1 grouping 1-2 algorithm '
                               'address-based L3 lacp\n',
                               'configure vlan Default delete ports 1-2\n',
                               'create vlan VLAN_2 tag 2\n',
                               'configure vlan VLAN_2 add ports 1 untagged\n',
                           ],
                           self.default_ignores)
        self.assertEqual(ret.stderr, '')

    def test_case_126(self):
        self.create_input('testinput',
                          [
                              'set vlan create 2\n',
                              'set vlan name 2 "VLAN 2"\n',
                              'set vlan egress 2 lag.0.1 tagged\n',
                              'set port lacp port ge.1.1-2 enable\n',
                          ])
        ret = self.script_env.run(self.script, '-otestoutput', 'testinput',
                                  '--log-level=ERROR')
        self.verify_output('testoutput',
                           [
                               'enable sharing 1 grouping 1-2 algorithm '
                               'address-based L3 lacp\n',
                               'configure vlan Default delete ports 2\n',
                               'create vlan VLAN_2 tag 2\n',
                               'configure vlan VLAN_2 add ports 1 tagged\n',
                           ],
                           self.default_ignores)
        self.assertEqual(ret.stderr, '')

# FM STP
    def test_case_060(self):
        self.runner(['set spantree enable\n'], [], self.std_stp_conf +
                    ['enable stpd s0\n', 'enable stpd s1\n'],
                    self.jumbo_ignore + self.ignore_web + self.ignore_mgmt +
                    self.ignore_idle)

    def test_case_061(self):
        self.runner(['set spantree disable\n'], [], [],
                    self.jumbo_ignore + self.ignore_web + self.ignore_mgmt +
                    self.ignore_idle)

    def test_case_062(self):
        self.create_input('testinput', ['set spantree msti sid 2 create\n'])
        ret = self.script_env.run(self.script, '-otestoutput.xsf', 'testinput',
                                  expect_stderr=True, expect_error=True)
        expected_output = [
            'configure mstp revision 0\n',
            'configure stpd s0 delete vlan Default ports all\n',
            'disable stpd s0 auto-bind vlan Default\n',
            'configure stpd s0 mode mstp cist\n',
            'enable stpd s0\n',
            'create stpd s2\n',
            'configure stpd s2 default-encapsulation dot1d\n',
            'configure stpd s2 mode mstp msti 2\n',
            'enable stpd s2\n',
        ]
        expected_errors = [
            'NOTICE: Writing translated configuration to file '
            '"testoutput.xsf"\n',
            'ERROR: Existing VLAN 1 mapped to MST instance 0 (CIST), but XOS'
            ' cannot map any VLANs to the CIST\n',
            'ERROR: No VLANs associated with any MST instance\n',
            'WARN: VLAN "Default" with tag "1" is not part of any MST'
            ' instance\n',
        ]
        self.verify_output('testoutput.xsf', expected_output,
                           self.jumbo_ignore + self.ignore_web +
                           self.ignore_mgmt + self.ignore_idle)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr', expected_errors,
                           ['Mapping', 'Port', 'LAGs', 'ser account'])
        self.assertEqual(ret.returncode, 1)

    def test_case_063(self):
        self.runner(['set spantree msti sid 2 create\n', 'set vlan create 2000'
                     '\n', 'set spantree mstmap 2000 sid 2\n', 'set spantree '
                     'mstmap 1 sid 2\n'], [],
                    ['create vlan VLAN_2000 tag 2000\n',
                     'configure mstp revision 0\n',
                     'configure stpd s0 delete vlan Default ports all\n',
                     'disable stpd s0 auto-bind vlan Default\n',
                     'configure stpd s0 mode mstp cist\n',
                     'enable stpd s0\n',
                     'create stpd s2\n',
                     'configure stpd s2 default-encapsulation dot1d\n',
                     'configure stpd s2 mode mstp msti 2\n',
                     'enable stpd s2 auto-bind vlan Default\n',
                     'enable stpd s2 auto-bind vlan VLAN_2000\n',
                     'enable stpd s2\n',
                     ],
                    self.jumbo_ignore + self.ignore_web +
                    self.ignore_mgmt + self.ignore_idle)

    def test_case_064(self):
        self.create_input('testinput', ['set spantree adminedge ge.1.1 true'
                                        '\n'])
        ret = self.script_env.run(self.script, '-otestoutput.xsf', 'testinput',
                                  expect_stderr=True)
        self.verify_output('testoutput.xsf',  self.std_stp_conf +
                           ['enable stpd s0\n', 'enable stpd s1\n',
                            'configure stpd s0 ports link-type edge 1\n'],
                           self.jumbo_ignore + self.ignore_web +
                           self.ignore_mgmt + self.ignore_idle)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr',
                           ['NOTICE: Writing translated configuration to file'
                            ' "testoutput.xsf"\n',
                            'WARN: XOS does not send BPDUs on RSTP/MSTP edge'
                            ' ports without edge-safeguard\n'],
                           ['Mapping', 'Port', 'LAGs', 'ser account'])

    def test_case_065(self):
        self.runner([], [], self.std_stp_conf +
                    ['enable stpd s0\n', 'enable stpd s1\n'],
                    self.jumbo_ignore + self.ignore_web + self.ignore_mgmt +
                    self.ignore_idle)

    def test_case_066(self):
        self.runner(['set spantree version rstp\n'], [], self.std_stp_conf +
                    ['enable stpd s0\n', 'enable stpd s1\n'],
                    self.jumbo_ignore + self.ignore_web + self.ignore_mgmt +
                    self.ignore_idle)

    def test_case_067(self):
        self.runner(['set spantree priority 0 0\n'], [], self.std_stp_conf +
                    ['configure stpd s0 priority 0\n', 'enable stpd s0\n',
                     'enable stpd s1\n'], self.jumbo_ignore + self.ignore_web +
                    self.ignore_mgmt + self.ignore_idle)

    def test_case_068(self):
        self.runner(['set spantree portadmin ge.1.1 disable\n'], [],
                    self.std_stp_conf +
                    ['enable stpd s0\n', 'enable stpd s1\n',
                     'disable stpd s0 ports 1\n'],
                    self.jumbo_ignore + self.ignore_web + self.ignore_mgmt +
                    self.ignore_idle)

    def test_case_069(self):
        self.runner(['set spantree adminedge ge.1.1 true\n',
                     'set spantree spanguard enable\n'], [],
                    self.std_stp_conf +
                    ['enable stpd s0\n', 'enable stpd s1\n', 'configure stpd '
                     's0 ports link-type edge 1 edge-safeguard enable\n'],
                    self.jumbo_ignore + self.ignore_web + self.ignore_mgmt +
                    self.ignore_idle)

    def test_case_070(self):
        self.runner(['set spantree priority 0\n'], [], self.std_stp_conf +
                    ['configure stpd s0 priority 0\n', 'enable stpd s0\n',
                     'enable stpd s1\n'], self.jumbo_ignore + self.ignore_web +
                    self.ignore_mgmt + self.ignore_idle)

    def test_case_071(self):
        eos_conf = [
            'set spantree mstcfgid cfgname REGION_NAME rev 42\n',
            'set spantree msti sid 1 create\n',
            'set spantree mstmap 1 sid 1\n',
        ]
        expected_conf = [
            'configure mstp region REGION_NAME\n',
            'configure mstp revision 42\n',
            'configure stpd s0 delete vlan Default ports all\n',
            'disable stpd s0 auto-bind vlan Default\n',
            'configure stpd s0 mode mstp cist\n',
            'enable stpd s0\n',
            'create stpd s1\n',
            'configure stpd s1 default-encapsulation dot1d\n',
            'configure stpd s1 mode mstp msti 1\n',
            'enable stpd s1 auto-bind vlan Default\n',
            'enable stpd s1\n',
        ]
        self.runner(eos_conf, [], expected_conf, self.jumbo_ignore +
                    self.ignore_web + self.ignore_mgmt + self.ignore_idle)

    def test_case_072(self):
        eos_conf = [
            'set spantree autoedge disable\n',
        ]
        expected_conf = self.std_stp_conf + ['enable stpd s0\n',
                                             'enable stpd s1\n']
        expected_err = [
            'NOTICE: Writing translated configuration to file '
            '"testoutput.xsf"\n',
            'INFO: Creating XOS equivalent of EOS default MSTP respectively'
            ' RSTP configuration\n',
        ]
        opts = ['--verbose']
        ignore_conf = (self.jumbo_ignore + self.ignore_web + self.ignore_mgmt +
                       self.ignore_idle)
        ignore_err = ['Mapping', 'Port', 'LAG', 'VLAN 1 ', 'ser account']
        self.create_input('testinput', eos_conf)
        ret = self.script_env.run(self.script, '-otestoutput.xsf', 'testinput',
                                  *opts, expect_stderr=True)
        self.verify_output('testoutput.xsf', expected_conf, ignore_conf)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr', expected_err, ignore_err)

    def test_case_073(self):
        eos_conf = [
            'set spantree autoedge enable\n',
        ]
        expected_conf = self.std_stp_conf + ['enable stpd s0\n',
                                             'enable stpd s1\n']
        expected_err = [
            'NOTICE: Writing translated configuration to file '
            '"testoutput.xsf"\n',
            'INFO: Creating XOS equivalent of EOS default MSTP respectively'
            ' RSTP configuration\n',
            'WARN: XOS does not support automatic edge port detection\n'
        ]
        opts = ['--verbose']
        ignore_conf = (self.jumbo_ignore + self.ignore_web + self.ignore_mgmt +
                       self.ignore_idle)
        ignore_err = ['Mapping', 'Port', 'LAG', 'VLAN 1 ', 'ser account']
        self.create_input('testinput', eos_conf)
        ret = self.script_env.run(self.script, '-otestoutput.xsf', 'testinput',
                                  *opts, expect_stderr=True)
        self.verify_output('testoutput.xsf', expected_conf, ignore_conf)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr', expected_err, ignore_err)

    def test_case_074(self):
        eos_conf = [
        ]
        expected_conf = self.std_stp_conf + ['enable stpd s0\n',
                                             'enable stpd s1\n']
        expected_err = [
            'NOTICE: Writing translated configuration to file '
            '"testoutput.xsf"\n',
            'INFO: Creating XOS equivalent of EOS default MSTP respectively'
            ' RSTP configuration\n',
            'INFO: XOS does not support automatic RSTP/MSTP edge port'
            ' detection\n'
        ]
        opts = ['--verbose']
        ignore_conf = (self.jumbo_ignore + self.ignore_web + self.ignore_mgmt +
                       self.ignore_idle)
        ignore_err = ['Mapping', 'Port', 'LAG', 'VLAN 1 ', 'ser account']
        self.create_input('testinput', eos_conf)
        ret = self.script_env.run(self.script, '-otestoutput.xsf', 'testinput',
                                  *opts, expect_stderr=True)
        self.verify_output('testoutput.xsf', expected_conf, ignore_conf)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr', expected_err, ignore_err)

    def test_case_129(self):
        self.runner(['set spantree msti sid 2 create\n',
                     'set vlan create 2000\n',
                     'set spantree mstmap 1,2000 sid 2\n',
                     'set vlan create 2001\n',
                     'set spantree msti sid 3 create\n',
                     'set spantree mstmap 2001 sid 3\n'], [],
                    ['create vlan VLAN_2000 tag 2000\n',
                     'create vlan VLAN_2001 tag 2001\n',
                     'configure mstp revision 0\n',
                     'configure stpd s0 delete vlan Default ports all\n',
                     'disable stpd s0 auto-bind vlan Default\n',
                     'configure stpd s0 mode mstp cist\n',
                     'enable stpd s0\n',
                     'create stpd s2\n',
                     'configure stpd s2 default-encapsulation dot1d\n',
                     'configure stpd s2 mode mstp msti 2\n',
                     'enable stpd s2 auto-bind vlan Default\n',
                     'enable stpd s2 auto-bind vlan VLAN_2000\n',
                     'enable stpd s2\n',
                     'create stpd s3\n',
                     'configure stpd s3 default-encapsulation dot1d\n',
                     'configure stpd s3 mode mstp msti 3\n',
                     'enable stpd s3 auto-bind vlan VLAN_2001\n',
                     'enable stpd s3\n',
                     ],
                    self.jumbo_ignore + self.ignore_web +
                    self.ignore_mgmt + self.ignore_idle)

# FM ACL
    def test_case_077(self):  # basic function test without file output
        acl_conf = ("router\nenable\nconfigure\naccess-list 1 permit host "
                    "55.1.2.3\nexit\nexit\nexit")
        ret = self.script_env.run(self.script, '--ignore-defaults', '--quiet',
                                  expect_stderr=True,
                                  stdin=str.encode(acl_conf))
        self.stderrToFile(ret.stdout, 'stdout')
        self.verify_output('stdout',
                           ['# acl_1.pol\n', 'entry 10 {\n', '  if {\n',
                            '    source-address 55.1.2.3/255.255.255.255;\n',
                            '  } then {\n', '    permit;\n', '  }\n', '}\n'] +
                           self._acl_deny_any(), [])

    def test_case_078(self):  # basic file writing test
        self.create_input('acl.cfg', ['router\n', 'enable\n', 'configure\n',
                          'access-list 1 permit host 55.1.2.3\n', 'exit\n',
                                      'exit\n', 'exit\n'])
        self.script_env.run(self.script, 'acl.cfg', '--quiet')
        # check if output is a file (change if output names are changed)
        self.assertTrue(os.path.isfile('{}/acl.xsf'.format(self.tmpdir)),
                        "Output not a file")
        self.assertTrue(os.path.isdir('{}/acl.acls'
                        .format(self.tmpdir)), "Output not a directory")
        self.assertTrue(os.path.isfile('{}/acl.acls/acl_1.pol'
                        .format(self.tmpdir)), "Output not a file")
        # check if output is right
        self.verify_output('acl.acls/acl_1.pol',
                           ['entry 10 {\n', '  if {\n',
                            '    source-address 55.1.2.3/255.255.255.255;\n',
                            '  } then {\n', '    permit;\n', '  }\n', '}\n'] +
                           self._acl_deny_any(), [])

    def test_case_079(self):  # check if syntactically wrong acl command fails
        self.create_input('acl.cfg', ['router\n', 'enable\n', 'configure\n',
                          'access-list 6 permit ip host 55.1.2.3\n', 'exit\n',
                                      'exit\n', 'exit\n'])
        ret = self.script_env.run(self.script, 'acl.cfg', '--quiet',
                                  expect_stderr=True, expect_error=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr', ['ERROR: Invalid address in ACE config '
                           '"access-list 6 permit ip host 55.1.2.3"\n'], [])
        self.assertEqual(ret.returncode, 1, "Wrong exit code")

    def test_case_105(self):  # check for WARN about ignored QoS
        self.create_input(
            'acl.cfg',
            ['router\n', 'enable\n', 'configure\n',
             'access-list 6 permit host 55.1.2.3 assign-queue 5\n',
             'access-list 1 permit any assign-queue 2\n',
             'access-list 100 permit udp host 61.102.3.2 61.112.0.0 0.0.0.255'
             ' dscp ef\n',
             'access-list 100 permit udp host 61.102.3.5 61.112.0.0 0.0.0.255'
             ' dscp ef assign-queue 4\n',
             'access-list 100 permit ip 61.114.6.7 0.0.0.255 host '
             '61.114.114.114 tos 23 fa\n',
             'access-list 100 permit tcp host 61.114.74.74 eq 17 any '
             'precedence 7\n',
             'access-list 100 permit udp host 61.114.43.33 eq 520 host '
             '61.114.43.33 eq 520 assign-queue 5\n',
             'access-list 100 permit udp host 61.114.43.33 eq 161 host '
             '61.88.12.34 tos ff cb assign-queue 4\n',
             'access-list 100 permit tcp any any established\n',
             'exit\n', 'exit\n', 'exit\n'
             ])
        ret = self.script_env.run(self.script, 'acl.cfg', '--log-level=WARN',
                                  expect_stderr=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr', [
            'WARN: Ignoring "assign-queue 5" in "access-list 6 permit host'
            ' 55.1.2.3 assign-queue 5"\n',
            'WARN: Ignoring "assign-queue 2" in "access-list 1 permit any '
            'assign-queue 2"\n',
            'WARN: Ignoring "dscp ef" in "access-list 100 permit udp host '
            '61.102.3.2 61.112.0.0 0.0.0.255 dscp ef"\n',
            'WARN: Ignoring "dscp ef assign-queue 4" in "access-list 100 '
            'permit udp host 61.102.3.5 61.112.0.0 0.0.0.255 dscp ef '
            'assign-queue 4"\n',
            'WARN: Ignoring "tos 23 fa" in "access-list 100 permit ip '
            '61.114.6.7 0.0.0.255 host 61.114.114.114 tos 23 fa"\n',
            'WARN: Ignoring "precedence 7" in "access-list 100 permit tcp host'
            ' 61.114.74.74 eq 17 any precedence 7"\n',
            'WARN: Ignoring "assign-queue 5" in "access-list 100 permit udp '
            'host 61.114.43.33 eq 520 host 61.114.43.33 eq 520 assign-queue 5'
            '"\n',
            'WARN: Ignoring "tos ff cb assign-queue 4" in "access-list 100 '
            'permit udp host 61.114.43.33 eq 161 host 61.88.12.34 tos ff cb '
            'assign-queue 4"\n',
            'WARN: Ignoring "established" in "access-list 100 permit tcp any '
            'any established"\n',
            ], [])
        self.assertEqual(ret.returncode, 0, "Wrong exit code")

    def test_case_080(self):  # test with 2 ACLs separated by a comment char
        self.create_input('acl.cfg',
                          ['router\n', 'enable\n', 'configure\n',
                           'access-list 2 deny any\n', '!\n', 'access-list 3 '
                           'permit host 55.1.2.3\n', 'exit\n', 'exit\n',
                           'exit\n'])
        self.script_env.run(self.script, 'acl.cfg', '--quiet')
        # check for files
        self.assertTrue(os.path.isdir('{}/acl.acls'
                        .format(self.tmpdir)), "Output not a directory")
        self.assertTrue(os.path.isfile('{}/acl.acls/acl_2.pol'
                        .format(self.tmpdir)), "Output not a file")
        self.assertTrue(os.path.isfile('{}/acl.acls/acl_3.pol'
                        .format(self.tmpdir)), "Output not a file")
        # check outputs
        self.verify_output('acl.acls/acl_2.pol',
                           ['entry 10 {\n', '  if {\n',
                            '    source-address 0.0.0.0/0;\n', '  } then {\n',
                            '    deny;\n', '  }\n', '}\n'] +
                           self._acl_deny_any(), [])
        self.verify_output('acl.acls/acl_3.pol',
                           ['entry 10 {\n', '  if {\n',
                            '    source-address 55.1.2.3/255.255.255.255;\n',
                            '  } then {\n', '    permit;\n', '  }\n', '}\n'] +
                           self._acl_deny_any(), [])

    def test_case_081(self):
        self.create_input('acl.cfg', ['router\n', 'enable\n', 'configure\n',
                                      'access-list 1 permit host 192.0.2.1\n',
                                      'access-list 1 deny 192.0.2.2 0.0.0.0\n',
                                      'access-list 1 permit 192.0.2.0 '
                                      '0.0.0.130\n', 'exit\n', 'exit\n',
                                      'exit\n'])
        self.script_env.run(self.script, 'acl.cfg', '--quiet')
        self.verify_output('acl.acls/acl_1.pol',
                           ['entry 10 {\n', '  if {\n',
                            '    source-address 192.0.2.1/255.255.255.255;\n',
                            '  } then {\n', '    permit;\n', '  }\n', '}\n',
                            'entry 20 {\n', '  if {\n',
                            '    source-address 192.0.2.2/255.255.255.255;\n',
                            '  } then {\n', '    deny;\n', '  }\n', '}\n',
                            'entry 30 {\n', '  if {\n',
                            '    source-address 192.0.2.0/255.255.255.125;\n',
                            '  } then {\n', '    permit;\n', '  }\n', '}\n'] +
                           self._acl_deny_any(40), [])

    def test_case_082(self):  # test for protocol based acls
        self.create_input('acl.cfg',
                          ['router\n', 'enable\n', 'configure\n',
                           'access-list 123 deny udp 10.0.0.1 0.0.0.0 eq 80 '
                           '10.0.1.0 0.0.0.255\n',
                           'access-list 123 deny tcp 10.0.0.1 0.0.0.0 eq 8088 '
                           '10.0.1.0 0.0.0.255 eq 8088\n',
                           'exit\n', 'exit\n', 'exit\n'])
        self.script_env.run(self.script, 'acl.cfg', '--quiet')
        self.verify_output('acl.acls/acl_123.pol',
                           ['entry 10 {\n', '  if {\n',
                            '    protocol udp;\n',
                            '    source-address 10.0.0.1/255.255.255.255;\n',
                            '    source-port 80;\n',
                            '    destination-address 10.0.1.0/255.255.255.0;'
                            '\n', '  } then {\n', '    deny;\n', '  }\n',
                            '}\n',
                            'entry 20 {\n', '  if {\n',
                            '    protocol tcp;\n',
                            '    source-address 10.0.0.1/255.255.255.255;\n',
                            '    source-port 8088;\n',
                            '    destination-address 10.0.1.0/255.255.255.0;'
                            '\n', '    destination-port 8088;\n',
                            '  } then {\n', '    deny;\n', '  }\n',
                            '}\n'] + self._acl_deny_any(30), [])

    def test_case_083(self):  # test for information if no router command
        self.create_input('acl_no_router.cfg',
                          ['access-list 1 permit host 55.1.2.3\n'])
        ret = self.script_env.run(self.script, 'acl_no_router.cfg',
                                  '--verbose', expect_stderr=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr',
                           ['INFO: "access-list" command outside router '
                            'configuration mode "access-list 1 permit '
                            'host 55.1.2.3"\n'], ['NOTICE: '] +
                           self.ignore_port_mapping + self.ignore_lag_info +
                           self.ignore_info_vlan_1 + self.ignore_stpd_info)
        self.verify_output('acl_no_router.acls/acl_1.pol',
                           ['entry 10 {\n', '  if {\n',
                            '    source-address 55.1.2.3/255.255.255.255;\n',
                            '  } then {\n', '    permit;\n', '  }\n', '}\n'] +
                           self._acl_deny_any(), [])

    def test_case_097(self):  # test for no warning if no router command
        self.create_input('acl_no_router.cfg',
                          ['access-list 1 permit host 55.1.2.3\n'])
        ret = self.script_env.run(self.script, 'acl_no_router.cfg',
                                  expect_stderr=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr', [], ['NOTICE: '])
        self.verify_output('acl_no_router.acls/acl_1.pol',
                           ['entry 10 {\n', '  if {\n',
                            '    source-address 55.1.2.3/255.255.255.255;\n',
                            '  } then {\n', '    permit;\n', '  }\n', '}\n'] +
                           self._acl_deny_any(), [])

    def test_case_084(self):  # test binding ACL to a port
        self.create_input('acl.cfg', ['router\n', 'enable\n', 'configure\n',
                                      'access-list 1 permit host 192.0.2.1\n',
                                      'access-list 1 deny 192.0.2.2 0.0.0.0\n',
                                      'access-list 1 permit 192.0.2.0 '
                                      '0.0.0.130\n', 'access-list interface 1'
                                      ' ge.1.1\n', 'exit\n', 'exit\n',
                                      'exit\n'])
        self.script_env.run(self.script, 'acl.cfg', '--quiet')
        self.verify_output('acl.acls/acl_1.pol',
                           ['entry 10 {\n', '  if {\n',
                            '    source-address 192.0.2.1/255.255.255.255;\n',
                            '  } then {\n', '    permit;\n', '  }\n', '}\n',
                            'entry 20 {\n', '  if {\n',
                            '    source-address 192.0.2.2/255.255.255.255;\n',
                            '  } then {\n', '    deny;\n', '  }\n', '}\n',
                            'entry 30 {\n', '  if {\n',
                            '    source-address 192.0.2.0/255.255.255.125;\n',
                            '  } then {\n', '    permit;\n', '  }\n', '}\n'] +
                           self._acl_deny_any(40), [])
        self.verify_output('acl.xsf',
                           ['configure access-list acl_1 ports 1 ingress\n'],
                           self.default_ignores)

    def test_case_106(self):  # sequence ignored WARN with ACL on port
        self.create_input('acl.cfg', ['router\n', 'enable\n', 'configure\n',
                                      'access-list 1 permit host 192.0.2.1\n',
                                      'access-list 1 deny 192.0.2.2 0.0.0.0\n',
                                      'access-list 1 permit 192.0.2.0 '
                                      '0.0.0.130\n', 'access-list interface 1'
                                      ' ge.1.1 sequence 2\n', 'access-list '
                                      'interface 1 ge.1.2 in sequence 3\n',
                                      'exit\n', 'exit\n', 'exit\n'])
        ret = self.script_env.run(self.script, 'acl.cfg',
                                  '--log-level', 'WARN', expect_stderr=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('acl.acls/acl_1.pol',
                           ['entry 10 {\n', '  if {\n',
                            '    source-address 192.0.2.1/255.255.255.255;\n',
                            '  } then {\n', '    permit;\n', '  }\n', '}\n',
                            'entry 20 {\n', '  if {\n',
                            '    source-address 192.0.2.2/255.255.255.255;\n',
                            '  } then {\n', '    deny;\n', '  }\n', '}\n',
                            'entry 30 {\n', '  if {\n',
                            '    source-address 192.0.2.0/255.255.255.125;\n',
                            '  } then {\n', '    permit;\n', '  }\n', '}\n'] +
                           self._acl_deny_any(40), [])
        self.verify_output('acl.xsf',
                           ['configure access-list acl_1 ports 1 ingress\n',
                            'configure access-list acl_1 ports 2 ingress\n'],
                           self.default_ignores)
        self.verify_output('stderr',
                           ['WARN: Ignoring ACL sequence number (access-list '
                            'interface) "access-list interface 1 ge.1.1 '
                            'sequence 2"\n',
                            'WARN: Ignoring ACL sequence number (access-list '
                            'interface) "access-list interface 1 ge.1.2 in '
                            'sequence 3"\n',
                            ],
                           [])

    def test_case_104(self):  # test binding same ACL twice to a port
        self.create_input('acl.cfg', ['router\n', 'enable\n', 'configure\n',
                                      'access-list 1 permit host 192.0.2.1\n',
                                      'access-list 1 deny 192.0.2.2 0.0.0.0\n',
                                      'access-list 1 permit 192.0.2.0 '
                                      '0.0.0.130\n', 'access-list interface 1'
                                      ' ge.1.1\n', 'access-list interface 1 '
                                      'ge.1.1 in\n', 'exit\n', 'exit\n',
                                      'exit\n'])
        self.script_env.run(self.script, 'acl.cfg', '--quiet')
        self.verify_output('acl.acls/acl_1.pol',
                           ['entry 10 {\n', '  if {\n',
                            '    source-address 192.0.2.1/255.255.255.255;\n',
                            '  } then {\n', '    permit;\n', '  }\n', '}\n',
                            'entry 20 {\n', '  if {\n',
                            '    source-address 192.0.2.2/255.255.255.255;\n',
                            '  } then {\n', '    deny;\n', '  }\n', '}\n',
                            'entry 30 {\n', '  if {\n',
                            '    source-address 192.0.2.0/255.255.255.125;\n',
                            '  } then {\n', '    permit;\n', '  }\n', '}\n'] +
                           self._acl_deny_any(40), [])
        self.verify_output('acl.xsf',
                           ['configure access-list acl_1 ports 1 ingress\n'],
                           self.default_ignores)

    def test_case_100(self):  # test binding 2 ACLs to a port
        self.create_input('acl.cfg', ['router\n', 'enable\n', 'configure\n',
                                      'access-list 1 permit host 192.0.2.1\n',
                                      'access-list 2 deny 192.0.2.2 0.0.0.0\n',
                                      'access-list 1 permit 192.0.2.0 '
                                      '0.0.0.130\n', 'access-list interface 1'
                                      ' ge.1.1\n', 'access-list interface 2'
                                      ' ge.1.1\n', 'exit\n', 'exit\n',
                                      'exit\n'])
        ret = self.script_env.run(self.script, 'acl.cfg', '--log-level=WARN',
                                  expect_stderr=True, expect_error=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr',
                           ['ERROR: XOS allows only one ACL per port '
                            '(port "1")\n'],
                           [])
        self.verify_output('acl.acls/acl_1.pol',
                           ['entry 10 {\n', '  if {\n',
                            '    source-address 192.0.2.1/255.255.255.255;\n',
                            '  } then {\n', '    permit;\n', '  }\n', '}\n',
                            'entry 20 {\n', '  if {\n',
                            '    source-address 192.0.2.0/255.255.255.125;\n',
                            '  } then {\n', '    permit;\n', '  }\n', '}\n'] +
                           self._acl_deny_any(30), [])
        self.verify_output('acl.acls/acl_2.pol',
                           ['entry 10 {\n', '  if {\n',
                            '    source-address 192.0.2.2/255.255.255.255;\n',
                            '  } then {\n', '    deny;\n', '  }\n', '}\n'] +
                           self._acl_deny_any(20), [])
        self.verify_output('acl.xsf',
                           [],
                           self.default_ignores)

    def test_case_085(self):  # test binding ACL to an SVI
        self.create_input('acl.cfg', ['router\n', 'enable\n', 'configure\n',
                                      'access-list 1 permit host 192.0.2.1\n',
                                      'access-list 1 deny 192.0.2.2 0.0.0.0\n',
                                      'access-list 1 permit 192.0.2.0 '
                                      '0.0.0.130\n', 'interface vlan 1\n',
                                      'ip access-group 1 in\n', 'exit\n'
                                      'exit\n', 'exit\n', 'exit\n'])
        self.script_env.run(self.script, 'acl.cfg', '--quiet')
        self.verify_output('acl.acls/acl_1.pol',
                           ['entry 10 {\n', '  if {\n',
                            '    source-address 192.0.2.1/255.255.255.255;\n',
                            '  } then {\n', '    permit;\n', '  }\n', '}\n',
                            'entry 20 {\n', '  if {\n',
                            '    source-address 192.0.2.2/255.255.255.255;\n',
                            '  } then {\n', '    deny;\n', '  }\n', '}\n',
                            'entry 30 {\n', '  if {\n',
                            '    source-address 192.0.2.0/255.255.255.125;\n',
                            '  } then {\n', '    permit;\n', '  }\n', '}\n'] +
                           self._acl_deny_any(40), [])
        self.verify_output('acl.xsf',
                           ['configure access-list acl_1 vlan Default '
                            'ingress\n'],
                           self.default_ignores)

    def test_case_101(self):  # test binding ACL to an SVI w/o in keyword
        self.create_input('acl.cfg', ['router\n', 'enable\n', 'configure\n',
                                      'access-list 1 permit host 192.0.2.1\n',
                                      'access-list 1 deny 192.0.2.2 0.0.0.0\n',
                                      'access-list 1 permit 192.0.2.0 '
                                      '0.0.0.130\n', 'interface vlan 1\n',
                                      'ip access-group 1\n', 'exit\n'
                                      'exit\n', 'exit\n', 'exit\n'])
        self.script_env.run(self.script, 'acl.cfg', '--quiet')
        self.verify_output('acl.acls/acl_1.pol',
                           ['entry 10 {\n', '  if {\n',
                            '    source-address 192.0.2.1/255.255.255.255;\n',
                            '  } then {\n', '    permit;\n', '  }\n', '}\n',
                            'entry 20 {\n', '  if {\n',
                            '    source-address 192.0.2.2/255.255.255.255;\n',
                            '  } then {\n', '    deny;\n', '  }\n', '}\n',
                            'entry 30 {\n', '  if {\n',
                            '    source-address 192.0.2.0/255.255.255.125;\n',
                            '  } then {\n', '    permit;\n', '  }\n', '}\n'] +
                           self._acl_deny_any(40), [])
        self.verify_output('acl.xsf',
                           ['configure access-list acl_1 vlan Default '
                            'ingress\n'],
                           self.default_ignores)

    def test_case_107(self):  # sequence ignored WARN with ACL on SVI
        self.create_input('acl.cfg', ['router\n', 'enable\n', 'configure\n',
                                      'access-list 1 permit host 192.0.2.1\n',
                                      'access-list 1 deny 192.0.2.2 0.0.0.0\n',
                                      'access-list 1 permit 192.0.2.0 '
                                      '0.0.0.130\n', 'interface vlan 1\n',
                                      'ip access-group 1 in sequence 1\n',
                                      'ip access-group 1 sequence 2\n',
                                      'exit\n', 'exit\n', 'exit\n', 'exit\n'])
        ret = self.script_env.run(self.script, 'acl.cfg',
                                  '--log-level', 'WARN', expect_stderr=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('acl.acls/acl_1.pol',
                           ['entry 10 {\n', '  if {\n',
                            '    source-address 192.0.2.1/255.255.255.255;\n',
                            '  } then {\n', '    permit;\n', '  }\n', '}\n',
                            'entry 20 {\n', '  if {\n',
                            '    source-address 192.0.2.2/255.255.255.255;\n',
                            '  } then {\n', '    deny;\n', '  }\n', '}\n',
                            'entry 30 {\n', '  if {\n',
                            '    source-address 192.0.2.0/255.255.255.125;\n',
                            '  } then {\n', '    permit;\n', '  }\n', '}\n'] +
                           self._acl_deny_any(40), [])
        self.verify_output('acl.xsf',
                           ['configure access-list acl_1 vlan Default '
                            'ingress\n'],
                           self.default_ignores)
        self.verify_output('stderr',
                           ['WARN: Ignoring "sequence 1" in "ip access-group 1'
                            ' in sequence 1" on "interface vlan 1"\n',
                            'WARN: Ignoring "sequence 2" in "ip access-group 1'
                            ' sequence 2" on "interface vlan 1"\n',
                            'WARN: XOS cannot disable switched virtual '
                            'interfaces, ignoring shutdown state of interface '
                            'VLAN 1\n',
                            ],
                           [])

    def test_case_102(self):  # test binding 2 ACLs to an SVI
        self.create_input('acl.cfg', ['router\n', 'enable\n', 'configure\n',
                                      'access-list 1 permit host 192.0.2.1\n',
                                      'access-list 2 deny 192.0.2.2 0.0.0.0\n',
                                      'access-list 1 permit 192.0.2.0 '
                                      '0.0.0.130\n',
                                      'interface vlan 1\n'
                                      'ip access-group 1\n',
                                      'ip access-group 2 in\n',
                                      'exit\n', 'exit\n', 'exit\n', 'exit\n'])
        ret = self.script_env.run(self.script, 'acl.cfg', '--quiet',
                                  expect_stderr=True, expect_error=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr',
                           ['ERROR: Only one ACL per VLAN possible with XOS'
                            ' (VLAN "Default", tag 1, ACLs: [1, 2])\n'],
                           [])
        self.verify_output('acl.acls/acl_1.pol',
                           ['entry 10 {\n', '  if {\n',
                            '    source-address 192.0.2.1/255.255.255.255;\n',
                            '  } then {\n', '    permit;\n', '  }\n', '}\n',
                            'entry 20 {\n', '  if {\n',
                            '    source-address 192.0.2.0/255.255.255.125;\n',
                            '  } then {\n', '    permit;\n', '  }\n', '}\n'] +
                           self._acl_deny_any(30), [])
        self.verify_output('acl.acls/acl_2.pol',
                           ['entry 10 {\n', '  if {\n',
                            '    source-address 192.0.2.2/255.255.255.255;\n',
                            '  } then {\n', '    deny;\n', '  }\n', '}\n'] +
                           self._acl_deny_any(20), [])
        self.verify_output('acl.xsf',
                           [],
                           self.default_ignores)

    def test_case_103(self):  # test binding same ACL twice to an SVI
        self.create_input('acl.cfg', ['router\n', 'enable\n', 'configure\n',
                                      'access-list 1 permit host 192.0.2.1\n',
                                      'access-list 1 deny 192.0.2.2 0.0.0.0\n',
                                      'access-list 1 permit 192.0.2.0 '
                                      '0.0.0.130\n', 'interface vlan 1\n',
                                      'ip access-group 1 in\n',
                                      'ip access-group 1\n', 'exit\n'
                                      'exit\n', 'exit\n', 'exit\n'])
        self.script_env.run(self.script, 'acl.cfg', '--quiet')
        self.verify_output('acl.acls/acl_1.pol',
                           ['entry 10 {\n', '  if {\n',
                            '    source-address 192.0.2.1/255.255.255.255;\n',
                            '  } then {\n', '    permit;\n', '  }\n', '}\n',
                            'entry 20 {\n', '  if {\n',
                            '    source-address 192.0.2.2/255.255.255.255;\n',
                            '  } then {\n', '    deny;\n', '  }\n', '}\n',
                            'entry 30 {\n', '  if {\n',
                            '    source-address 192.0.2.0/255.255.255.125;\n',
                            '  } then {\n', '    permit;\n', '  }\n', '}\n'] +
                           self._acl_deny_any(40), [])
        self.verify_output('acl.xsf',
                           ['configure access-list acl_1 vlan Default '
                            'ingress\n'],
                           self.default_ignores)

    def test_case_086(self):  # test for upper case ICMP protocol in ACL/ACE
        self.create_input('acl.cfg',
                          ['router\n', 'enable\n', 'configure\n',
                           'access-list 145 deny ICMP any any\n',
                           'exit\n', 'exit\n', 'exit\n'])
        self.script_env.run(self.script, 'acl.cfg', '--quiet')
        self.verify_output('acl.acls/acl_145.pol',
                           ['entry 10 {\n', '  if {\n',
                            '    protocol icmp;\n',
                            '    source-address 0.0.0.0/0;\n',
                            '    destination-address 0.0.0.0/0;\n',
                            '  } then {\n', '    deny;\n', '  }\n',
                            '}\n'] + self._acl_deny_any(), [])

    def test_case_087(self):  # test for ip access-group
        self.runner(['router\n', 'enable\n', 'configure\n',
                     'access-list 1 permit host 192.0.2.1\n',
                     'access-list 1 deny 192.0.2.2 0.0.0.0\n',
                     'access-list 1 permit 192.0.2.0 0.0.0.130\n', '!\n',
                     'interface vlan 1\n', 'ip access-group 1 in\n', 'exit\n',
                     '!\n', 'exit\n', 'exit\n', 'exit\n'], [],
                    ['configure access-list acl_1 vlan Default ingress\n'],
                    self.default_ignores)
        self.verify_output('testoutput.acls/acl_1.pol',
                           ['entry 10 {\n', '  if {\n',
                            '    source-address 192.0.2.1/255.255.255.255;\n',
                            '  } then {\n', '    permit;\n', '  }\n', '}\n',
                            'entry 20 {\n', '  if {\n',
                            '    source-address 192.0.2.2/255.255.255.255;\n',
                            '  } then {\n', '    deny;\n', '  }\n', '}\n',
                            'entry 30 {\n', '  if {\n',
                            '    source-address 192.0.2.0/255.255.255.125;\n',
                            '  } then {\n', '    permit;\n', '  }\n', '}\n'] +
                           self._acl_deny_any(40), [])

    def test_case_088(self):  # test for IGMP protocol in ACE
        self.runner(['router\n', 'enable\n', 'configure\n',
                     'access-list 196 permit igmp any 4.1.0.1 0.0.255.255\n',
                     'access-list 196 permit igmp 6.1.0.1 0.0.255.255 any\n',
                     'access-list 196 permit igmp any 4.1.0.5 0.0.255.255\n',
                     'access-list 196 permit igmp 6.1.0.5 0.0.255.255 any\n',
                     '!\n',
                     'interface vlan 1\n', 'ip access-group 196 in\n',
                     'exit\n', '!\n', 'exit\n', 'exit\n', 'exit\n'], [],
                    ['configure access-list acl_196 vlan Default ingress\n'],
                    self.default_ignores)
        self.verify_output('testoutput.acls/acl_196.pol',
                           ['entry 10 {\n', '  if {\n',
                            '    protocol igmp;\n',
                            '    source-address 0.0.0.0/0;\n',
                            '    destination-address 4.1.0.1/255.255.0.0;\n',
                            '  } then {\n', '    permit;\n', '  }\n', '}\n',
                            'entry 20 {\n', '  if {\n',
                            '    protocol igmp;\n',
                            '    source-address 6.1.0.1/255.255.0.0;\n',
                            '    destination-address 0.0.0.0/0;\n',
                            '  } then {\n', '    permit;\n', '  }\n', '}\n',
                            'entry 30 {\n', '  if {\n',
                            '    protocol igmp;\n',
                            '    source-address 0.0.0.0/0;\n',
                            '    destination-address 4.1.0.5/255.255.0.0;\n',
                            '  } then {\n', '    permit;\n', '  }\n', '}\n',
                            'entry 40 {\n', '  if {\n',
                            '    protocol igmp;\n',
                            '    source-address 6.1.0.5/255.255.0.0;\n',
                            '    destination-address 0.0.0.0/0;\n',
                            '  } then {\n', '    permit;\n', '  }\n', '}\n',
                            ] + self._acl_deny_any(50), [])

    def test_case_089(self):  # test print port mapping
        self.create_input('empty.cfg', [])
        ret = self.script_env.run(self.script, 'empty.cfg', '--verbose',
                                  expect_stderr=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr',
                           ['INFO: Mapping port "ge.1.1" to port "1"\n',
                            'INFO: Mapping port "ge.1.2" to port "2"\n',
                            'INFO: Mapping port "ge.1.3" to port "3"\n',
                            'INFO: Mapping port "ge.1.4" to port "4"\n',
                            'INFO: Mapping port "ge.1.5" to port "5"\n',
                            'INFO: Mapping port "ge.1.6" to port "6"\n',
                            'INFO: Mapping port "ge.1.7" to port "7"\n',
                            'INFO: Mapping port "ge.1.8" to port "8"\n',
                            'INFO: Mapping port "ge.1.9" to port "9"\n',
                            'INFO: Mapping port "ge.1.10" to port "10"\n',
                            'INFO: Mapping port "ge.1.11" to port "11"\n',
                            'INFO: Mapping port "ge.1.12" to port "12"\n',
                            'INFO: Mapping port "ge.1.13" to port "13"\n',
                            'INFO: Mapping port "ge.1.14" to port "14"\n',
                            'INFO: Mapping port "ge.1.15" to port "15"\n',
                            'INFO: Mapping port "ge.1.16" to port "16"\n',
                            'INFO: Mapping port "ge.1.17" to port "17"\n',
                            'INFO: Mapping port "ge.1.18" to port "18"\n',
                            'INFO: Mapping port "ge.1.19" to port "19"\n',
                            'INFO: Mapping port "ge.1.20" to port "20"\n',
                            'INFO: Mapping port "ge.1.21" to port "21"\n',
                            'INFO: Mapping port "ge.1.22" to port "22"\n',
                            'INFO: Mapping port "ge.1.23" to port "23"\n',
                            'INFO: Mapping port "ge.1.24" to port "24"\n',
                            'INFO: Mapping port "ge.1.25" to port "25"\n',
                            'INFO: Mapping port "ge.1.26" to port "26"\n',
                            'INFO: Mapping port "ge.1.27" to port "27"\n',
                            'INFO: Mapping port "ge.1.28" to port "28"\n',
                            'INFO: Mapping port "ge.1.29" to port "29"\n',
                            'INFO: Mapping port "ge.1.30" to port "30"\n',
                            'INFO: Mapping port "ge.1.31" to port "31"\n',
                            'INFO: Mapping port "ge.1.32" to port "32"\n',
                            'INFO: Mapping port "ge.1.33" to port "33"\n',
                            'INFO: Mapping port "ge.1.34" to port "34"\n',
                            'INFO: Mapping port "ge.1.35" to port "35"\n',
                            'INFO: Mapping port "ge.1.36" to port "36"\n',
                            'INFO: Mapping port "ge.1.37" to port "37"\n',
                            'INFO: Mapping port "ge.1.38" to port "38"\n',
                            'INFO: Mapping port "ge.1.39" to port "39"\n',
                            'INFO: Mapping port "ge.1.40" to port "40"\n',
                            'INFO: Mapping port "ge.1.41" to port "41"\n',
                            'INFO: Mapping port "ge.1.42" to port "42"\n',
                            'INFO: Mapping port "ge.1.43" to port "43"\n',
                            'INFO: Mapping port "ge.1.44" to port "44"\n',
                            'INFO: Mapping port "ge.1.45" to port "45"\n',
                            'INFO: Mapping port "ge.1.46" to port "46"\n',
                            'INFO: Mapping port "ge.1.47" to port "47"\n',
                            'INFO: Mapping port "ge.1.48" to port "48"\n',
                            'NOTICE: Mapping port "tg.1.49" to port "53"\n',
                            'NOTICE: Mapping port "tg.1.50" to port "54"\n',
                            'NOTICE: Port "49" of target switch is not used\n',
                            'NOTICE: Port "50" of target switch is not used\n',
                            'NOTICE: Port "51" of target switch is not used\n',
                            'NOTICE: Port "52" of target switch is not used\n',
                            ],
                           self.ignore_outfile + self.ignore_lag_info +
                           self.ignore_info_vlan_1 + self.ignore_stpd_info +
                           self.ignore_user)

    def test_case_090(self):  # test print stack notice
        self.create_input('empty.cfg', [])
        ret = self.script_env.run(self.script, 'empty.cfg',
                                  '--target=SummitX460-48t+2sf,',
                                  expect_stderr=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr', [
            'NOTICE: Mapping port "tg.1.49" to port "1:53"\n',
            'NOTICE: Mapping port "tg.1.50" to port "1:54"\n',
            'NOTICE: Port "1:49" of target switch is not used\n',
            'NOTICE: Port "1:50" of target switch is not used\n',
            'NOTICE: Port "1:51" of target switch is not used\n',
            'NOTICE: Port "1:52" of target switch is not used\n',
            'NOTICE: Creating configuration for switch / stack in stacking '
            'mode\n',
            'NOTICE: Stacking must be configured before applying this '
            'configuration\n',
            'NOTICE: See the ExtremeXOS Configuration Guide on how to '
            'configure stacking\n',
            ],
            self.ignore_outfile + self.ignore_lag_info +
            self.ignore_info_vlan_1 + self.ignore_stpd_info +
            self.ignore_user)

    def test_case_091(self):  # test a stack config translation
        self.create_input('stack.cfg', ['set port disable ge.*.44-48\n',
                                        'set vlan create 42\n',
                                        'set vlan name 42 MYVLAN\n',
                                        'set port vlan ge.*.1-43 42 '
                                        'modify-egress\n'])
        ret = self.script_env.run(self.script, 'stack.cfg',
                                  '--ignore-defaults',
                                  '--source=C5G124-48,C5G124-48,C5G124-48',
                                  '--target=SummitX460-48t,SummitX460-48t,'
                                  'SummitX460-48t',
                                  expect_stderr=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stack.xsf', [
            'disable ports 1:44\n',
            'disable ports 1:45\n',
            'disable ports 1:46\n',
            'disable ports 1:47\n',
            'disable ports 1:48\n',
            'disable ports 2:44\n',
            'disable ports 2:45\n',
            'disable ports 2:46\n',
            'disable ports 2:47\n',
            'disable ports 2:48\n',
            'disable ports 3:44\n',
            'disable ports 3:45\n',
            'disable ports 3:46\n',
            'disable ports 3:47\n',
            'disable ports 3:48\n',
            'configure vlan Default delete ports 1:1-43,2:1-43,3:1-43\n',
            'create vlan MYVLAN tag 42\n',
            'configure vlan MYVLAN add ports 1:1-43,2:1-43,3:1-43 untagged\n',
            ], [])
        self.verify_output('stderr', [
            'NOTICE: Writing translated configuration to file "stack.xsf"\n',
            'NOTICE: Port "1:49" of target switch is not used\n',
            'NOTICE: Port "1:50" of target switch is not used\n',
            'NOTICE: Port "1:51" of target switch is not used\n',
            'NOTICE: Port "1:52" of target switch is not used\n',
            'NOTICE: Port "2:49" of target switch is not used\n',
            'NOTICE: Port "2:50" of target switch is not used\n',
            'NOTICE: Port "2:51" of target switch is not used\n',
            'NOTICE: Port "2:52" of target switch is not used\n',
            'NOTICE: Port "3:49" of target switch is not used\n',
            'NOTICE: Port "3:50" of target switch is not used\n',
            'NOTICE: Port "3:51" of target switch is not used\n',
            'NOTICE: Port "3:52" of target switch is not used\n',
            'NOTICE: Creating configuration for switch / stack in stacking '
            'mode\n',
            'NOTICE: Stacking must be configured before applying this '
            'configuration\n',
            'NOTICE: See the ExtremeXOS Configuration Guide on how to '
            'configure stacking\n',
            ], [])

    def test_case_092(self):  # prompt to sysName
        self.create_input('prompt.cfg', ['set prompt Switch01\n'])
        ret = self.script_env.run(self.script, 'prompt.cfg',
                                  '--ignore-defaults',
                                  expect_stderr=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('prompt.xsf',
                           ['configure snmp sysName "Switch01"\n'],
                           [])
        self.verify_output('stderr', [],
                           self.default_ignores + self.ignore_outfile +
                           self.ignore_lag_info + self.ignore_info_vlan_1 +
                           self.ignore_port_mapping + self.ignore_stpd_info +
                           self.ignore_unused_ports)

    def test_case_093(self):  # sysName
        self.create_input('prompt.cfg', ['set system name Switch01\n'])
        ret = self.script_env.run(self.script, 'prompt.cfg',
                                  '--ignore-defaults',
                                  expect_stderr=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('prompt.xsf',
                           ['configure snmp sysName "Switch01"\n'],
                           [])
        self.verify_output('stderr', [],
                           self.default_ignores + self.ignore_outfile +
                           self.ignore_lag_info + self.ignore_info_vlan_1 +
                           self.ignore_port_mapping + self.ignore_stpd_info +
                           self.ignore_unused_ports)

    def test_case_094(self):  # sysName overwrites prompt
        self.create_input('prompt.cfg',
                          ['set system name Switch01\n',
                           'set prompt Switch02\n'])
        ret = self.script_env.run(self.script, 'prompt.cfg',
                                  '--ignore-defaults',
                                  expect_stderr=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('prompt.xsf',
                           ['configure snmp sysName "Switch01"\n'],
                           [])
        self.verify_output('stderr', ['WARN: The XOS prompt is derived from'
                                      ' the snmp system name, ignoring the '
                                      'configured prompt\n'],
                           self.default_ignores + self.ignore_outfile +
                           self.ignore_lag_info + self.ignore_info_vlan_1 +
                           self.ignore_port_mapping + self.ignore_stpd_info +
                           self.ignore_unused_ports)

    def test_case_096(self):  # sysContact
        self.create_input('contact.cfg',
                          ['set system contact admin@example.com\n'])
        ret = self.script_env.run(self.script, 'contact.cfg',
                                  '--ignore-defaults',
                                  expect_stderr=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('contact.xsf',
                           ['configure snmp sysContact "admin@example.com"\n'],
                           [])
        self.verify_output('stderr', [],
                           self.default_ignores + self.ignore_outfile +
                           self.ignore_lag_info + self.ignore_info_vlan_1 +
                           self.ignore_port_mapping + self.ignore_stpd_info +
                           self.ignore_unused_ports)

    def test_case_099(self):  # space OK in sysName and sysContact
        self.create_input('names.cfg',
                          ['set system contact ' +
                           '"Network Admin Team (admin@example.com)"\n',
                           'set system name "Switch 1"\n'])
        ret = self.script_env.run(self.script, 'names.cfg',
                                  '--ignore-defaults',
                                  expect_stderr=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('names.xsf',
                           ['configure snmp sysName "Switch 1"\n',
                            'configure snmp sysContact ' +
                            '"Network Admin Team (admin@example.com)"\n'],
                           [])
        self.verify_output('stderr', [],
                           self.default_ignores + self.ignore_outfile +
                           self.ignore_lag_info + self.ignore_info_vlan_1 +
                           self.ignore_port_mapping + self.ignore_stpd_info +
                           self.ignore_unused_ports)

    def test_case_098(self):  # sysLocation
        self.create_input('location.cfg',
                          ['set system location "HQ / Bldg 1 / Floor 3"\n'])
        ret = self.script_env.run(self.script, 'location.cfg',
                                  '--ignore-defaults',
                                  expect_stderr=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('location.xsf',
                           ['configure snmp sysLocation ' +
                            '"HQ / Bldg 1 / Floor 3"\n'],
                           [])
        self.verify_output('stderr', [],
                           self.default_ignores + self.ignore_outfile +
                           self.ignore_lag_info + self.ignore_info_vlan_1 +
                           self.ignore_port_mapping + self.ignore_stpd_info +
                           self.ignore_unused_ports)

    def test_case_108(self):  # banners with login ack
        self.create_input('test.cfg', [
            r'set banner login "***\n***\t--- Login Banner ---\n***"' '\n'
            r'set banner motd "***\n***\t--- Message of the Day ---\n***"' '\n'
        ])
        ret = self.script_env.run(self.script, 'test.cfg', expect_stderr=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('test.xsf', [
            'configure banner before-login acknowledge '
            'save-to-configuration\n',
            '***\n',
            '***\t--- Login Banner ---\n',
            '***\n',
            'Press RETURN to proceed to login\n',
            '\n',
            'configure banner after-login\n',
            '***\n',
            '***\t--- Message of the Day ---\n',
            '***\n',
            '\n',
        ], self.default_ignores)
        self.verify_output('stderr', [],
                           self.default_ignores + self.ignore_outfile +
                           self.ignore_lag_info + self.ignore_info_vlan_1 +
                           self.ignore_port_mapping + self.ignore_stpd_info +
                           self.ignore_unused_ports + self.ignore_user)

    def test_case_109(self):  # login banner w/o ack
        self.create_input('test.cfg', [
            r'set banner login "***\n***\t--- Login Banner ---\n***"' '\n'
        ])
        ret = self.script_env.run(self.script, 'test.cfg', '--ignore-defaults',
                                  expect_stderr=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('test.xsf', [
            'configure banner before-login save-to-configuration\n',
            '***\n',
            '***\t--- Login Banner ---\n',
            '***\n',
            '\n',
        ], self.default_ignores)
        self.verify_output('stderr', [],
                           self.default_ignores + self.ignore_outfile +
                           self.ignore_lag_info + self.ignore_info_vlan_1 +
                           self.ignore_port_mapping + self.ignore_stpd_info +
                           self.ignore_unused_ports)

    def test_case_110(self):  # login banner w/o ack and empty line
        self.create_input('test.cfg', [
            r'set banner login "***\n\n***\t--- Login Banner ---\n***"' '\n'
        ])
        ret = self.script_env.run(self.script, 'test.cfg', '--ignore-defaults',
                                  expect_stderr=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('test.xsf', [
            'configure banner before-login save-to-configuration\n',
            '***\n',
            '***\t--- Login Banner ---\n',
            '***\n',
            '\n',
        ], self.default_ignores)
        self.verify_output('stderr', ['WARN: XOS banner cannot contain empty'
                                      ' lines, omitting empty lines\n'],
                           self.default_ignores + self.ignore_outfile +
                           self.ignore_lag_info + self.ignore_info_vlan_1 +
                           self.ignore_port_mapping + self.ignore_stpd_info +
                           self.ignore_unused_ports)

    def test_case_111(self):  # disable telnet all with defaults
        self.create_input('test.cfg', [
            'set telnet disable all\n',
        ])
        ret = self.script_env.run(self.script, 'test.cfg',
                                  expect_stderr=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('test.xsf', [
            'disable telnet\n',
        ], self.default_ignores)
        self.verify_output('stderr', ['WARN: Outbound telnet cannot be '
                                      'disabled on XOS\n'],
                           self.default_ignores + self.ignore_outfile +
                           self.ignore_lag_info + self.ignore_info_vlan_1 +
                           self.ignore_port_mapping + self.ignore_stpd_info +
                           self.ignore_unused_ports + self.ignore_user)

    def test_case_112(self):  # disable telnet all without defaults
        self.create_input('test.cfg', [
            'set telnet disable all\n',
        ])
        ret = self.script_env.run(self.script, 'test.cfg', '--ignore-defaults',
                                  expect_stderr=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('test.xsf', [
            'disable telnet\n',
        ], self.default_ignores)
        self.verify_output('stderr', ['WARN: Outbound telnet cannot be '
                                      'disabled on XOS\n'],
                           self.default_ignores + self.ignore_outfile +
                           self.ignore_lag_info + self.ignore_info_vlan_1 +
                           self.ignore_port_mapping + self.ignore_stpd_info +
                           self.ignore_unused_ports)

    def test_case_113(self):  # disable telnet inbound with defaults
        self.create_input('test.cfg', [
            'set telnet disable inbound\n',
        ])
        ret = self.script_env.run(self.script, 'test.cfg',
                                  expect_stderr=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('test.xsf', [
            'disable telnet\n',
        ], self.default_ignores)
        self.verify_output('stderr', [],
                           self.default_ignores + self.ignore_outfile +
                           self.ignore_lag_info + self.ignore_info_vlan_1 +
                           self.ignore_port_mapping + self.ignore_stpd_info +
                           self.ignore_unused_ports + self.ignore_user)

    def test_case_114(self):  # disable telnet inbound without defaults
        self.create_input('test.cfg', [
            'set telnet disable inbound\n',
        ])
        ret = self.script_env.run(self.script, 'test.cfg', '--ignore-defaults',
                                  expect_stderr=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('test.xsf', [
            'disable telnet\n',
        ], self.default_ignores)
        self.verify_output('stderr', [],
                           self.default_ignores + self.ignore_outfile +
                           self.ignore_lag_info + self.ignore_info_vlan_1 +
                           self.ignore_port_mapping + self.ignore_stpd_info +
                           self.ignore_unused_ports)

    def test_case_115(self):  # disable telnet outbound with defaults
        self.create_input('test.cfg', [
            'set telnet disable outbound\n',
        ])
        ret = self.script_env.run(self.script, 'test.cfg',
                                  expect_stderr=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('test.xsf', [], self.default_ignores)
        self.verify_output('stderr', ['WARN: Outbound telnet cannot be '
                                      'disabled on XOS\n'],
                           self.default_ignores + self.ignore_outfile +
                           self.ignore_lag_info + self.ignore_info_vlan_1 +
                           self.ignore_port_mapping + self.ignore_stpd_info +
                           self.ignore_unused_ports + self.ignore_user)

    def test_case_116(self):  # enable telnet outbound without defaults
        self.create_input('test.cfg', [
            'set telnet enable outbound\n',
        ])
        ret = self.script_env.run(self.script, 'test.cfg', '--ignore-defaults',
                                  expect_stderr=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('test.xsf', [], self.default_ignores)
        self.verify_output('stderr', [],
                           self.default_ignores + self.ignore_outfile +
                           self.ignore_lag_info + self.ignore_info_vlan_1 +
                           self.ignore_port_mapping + self.ignore_stpd_info +
                           self.ignore_unused_ports)

    def test_case_117(self):  # disable telnet outbound without defaults verb.
        self.create_input('test.cfg', [
            'set telnet enable outbound\n',
        ])
        ret = self.script_env.run(self.script, 'test.cfg', '--ignore-defaults',
                                  '--verbose', expect_stderr=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('test.xsf', [], self.default_ignores)
        self.verify_output('stderr', ['INFO: Outbound telnet is always '
                                      'enabled on XOS\n'],
                           self.default_ignores + self.ignore_outfile +
                           self.ignore_lag_info + self.ignore_info_vlan_1 +
                           self.ignore_port_mapping + self.ignore_stpd_info +
                           self.ignore_unused_ports)

    def test_case_118(self):  # enable telnet all without defaults
        self.create_input('test.cfg', [
            'set telnet enable all\n',
        ])
        ret = self.script_env.run(self.script, 'test.cfg', '--ignore-defaults',
                                  expect_stderr=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('test.xsf', ['enable telnet\n'],
                           self.default_ignores)
        self.verify_output('stderr', [],
                           self.default_ignores + self.ignore_outfile +
                           self.ignore_lag_info + self.ignore_info_vlan_1 +
                           self.ignore_port_mapping + self.ignore_stpd_info +
                           self.ignore_unused_ports)

    def test_case_119(self):  # enable telnet all without defaults verbose
        self.create_input('test.cfg', [
            'set telnet enable all\n',
        ])
        ret = self.script_env.run(self.script, 'test.cfg', '--ignore-defaults',
                                  '--verbose', expect_stderr=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('test.xsf', ['enable telnet\n'],
                           self.default_ignores)
        self.verify_output('stderr', ['INFO: Outbound telnet is always '
                                      'enabled on XOS\n'],
                           self.default_ignores + self.ignore_outfile +
                           self.ignore_lag_info + self.ignore_info_vlan_1 +
                           self.ignore_port_mapping + self.ignore_stpd_info +
                           self.ignore_unused_ports)

    def test_case_130(self):  # enable ssh
        self.create_input('test.cfg', [
            'set ssh enabled\n',
        ])
        ret = self.script_env.run(self.script, 'test.cfg',
                                  expect_stderr=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('test.xsf', [
            'configure ssh2 key\n',
            'enable ssh2\n',
        ], self.default_ignores)
        self.verify_output('stderr',
                           ['NOTICE: ssh.xmod needs to be installed for SSH' +
                            ' commands to work\n'],
                           self.default_ignores + self.ignore_outfile +
                           self.ignore_lag_info + self.ignore_info_vlan_1 +
                           self.ignore_port_mapping + self.ignore_stpd_info +
                           self.ignore_unused_ports + self.ignore_user)

    def test_case_131(self):  # verify defaults from empty input config
        self.create_input('empty.cfg', [])
        ret = self.script_env.run(self.script, 'empty.cfg',
                                  expect_stderr=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('empty.xsf', self.default_config, [])
        self.verify_output('stderr', self.default_messages,
                           ['NOTICE: Writing translated configuration to'
                            ' file "empty.xsf"'])

    def test_case_132(self):  # disable webview
        self.create_input('web.cfg', ['set webview disable\n'])
        ret = self.script_env.run(self.script, 'web.cfg',
                                  expect_stderr=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('web.xsf', ['disable web http\n'],
                           self.jumbo_ignore + self.ignore_stpd +
                           self.ignore_mgmt + self.ignore_idle)
        self.verify_output('stderr', self.default_messages,
                           ['NOTICE: Writing translated configuration to'
                            ' file "web.xsf"'])

    def test_case_133(self):  # enable webview
        self.create_input('web.cfg', ['set webview enable\n'])
        self.script_env.run(self.script, 'web.cfg', '--ignore-defaults',
                            '--quiet')
        self.verify_output('web.xsf', ['enable web http\n'],
                           self.jumbo_ignore + self.ignore_stpd)

    def test_case_134(self):  # enable webview and SSL
        self.create_input('web.cfg',
                          ['set ssl enabled\n', 'set webview enable\n'])
        ret = self.script_env.run(self.script, 'web.cfg', '--ignore-defaults',
                                  expect_stderr=True)
        self.verify_output('web.xsf',
                           ['enable web http\n', 'enable web https\n'],
                           self.jumbo_ignore + self.ignore_stpd)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr',
                           ['NOTICE: ssh.xmod needs to be installed for'
                            ' HTTPS\n',
                            'NOTICE: You need to manually create a'
                            ' certificate for HTTPS to work (configure ssl'
                            ' certificate)\n',
                            ],
                           self.default_ignores + self.ignore_outfile +
                           self.ignore_lag_info + self.ignore_info_vlan_1 +
                           self.ignore_port_mapping + self.ignore_stpd_info +
                           self.ignore_unused_ports + self.def_map_msg)

    def test_case_135(self):  # enable webview over SSL only, no defaults
        self.create_input('web.cfg',
                          ['set ssl enabled\n',
                           'set webview enable ssl-only\n'])
        self.script_env.run(self.script, 'web.cfg', '--ignore-defaults',
                            '--quiet')
        self.verify_output('web.xsf',
                           ['disable web http\n', 'enable web https\n'],
                           self.jumbo_ignore + self.ignore_stpd)

    def test_case_136(self):  # enable webview over SSL only, with defaults
        self.create_input('web.cfg',
                          ['set ssl enabled\n',
                           'set webview enable ssl-only\n'])
        self.script_env.run(self.script, 'web.cfg', '--quiet')
        self.verify_output('web.xsf',
                           ['disable web http\n', 'enable web https\n'],
                           self.jumbo_ignore + self.ignore_stpd +
                           self.ignore_mgmt + self.ignore_idle)

    def test_case_137(self):  # disable DHCP client for management
        self.create_input('mgmt.cfg',
                          ['set ip protocol none\n'])
        self.script_env.run(self.script, 'mgmt.cfg', '--quiet')
        self.verify_output('mgmt.xsf',
                           [],
                           self.jumbo_ignore + self.ignore_stpd +
                           self.ignore_web + self.ignore_idle)

    def test_case_138(self):  # enable BOOTP client for management
        self.create_input('mgmt.cfg',
                          ['set ip protocol bootp\n'])
        self.script_env.run(self.script, 'mgmt.cfg', '--quiet')
        self.verify_output('mgmt.xsf',
                           ['enable bootp vlan Default\n'],
                           self.jumbo_ignore + self.ignore_stpd +
                           self.ignore_web + self.ignore_idle)

    def test_case_139(self):  # enable DHCP client for management
        self.create_input('mgmt.cfg',
                          ['set ip protocol dhcp\n'])
        self.script_env.run(self.script, 'mgmt.cfg', '--quiet')
        self.verify_output('mgmt.xsf',
                           ['enable dhcp vlan Default\n'],
                           self.jumbo_ignore + self.ignore_stpd +
                           self.ignore_web + self.ignore_idle)

    def test_case_140(self):  # enable DHCP client for management
        self.create_input('mgmt.cfg',
                          ['set host vlan 1\n',
                           'set ip protocol dhcp\n'])
        self.script_env.run(self.script, 'mgmt.cfg', '--quiet',
                            '--ignore-defaults')
        self.verify_output('mgmt.xsf',
                           ['enable dhcp vlan Default\n'],
                           self.jumbo_ignore + self.ignore_stpd +
                           self.ignore_web + self.ignore_idle)

    def test_case_141(self):  # use management port
        self.create_input('mgmt.cfg', [])
        self.script_env.run(self.script, 'mgmt.cfg', '--quiet', '--mgmt-port')
        self.verify_output('mgmt.xsf',
                           ['enable dhcp vlan Mgmt\n'],
                           self.jumbo_ignore + self.ignore_stpd +
                           self.ignore_web + self.ignore_idle)

    def test_case_142(self):  # static management address class C
        self.create_input('mgmt.cfg',
                          ['set ip protocol none\n',
                           'set ip address 192.0.2.11\n'])
        self.script_env.run(self.script, 'mgmt.cfg', '--quiet')
        self.verify_output('mgmt.xsf',
                           ['configure vlan Default ipaddress 192.0.2.11 '
                            '255.255.255.0\n'],
                           self.jumbo_ignore + self.ignore_stpd +
                           self.ignore_web + self.ignore_idle)

    def test_case_143(self):  # static management address class B
        self.create_input('mgmt.cfg',
                          ['set ip protocol none\n',
                           'set ip address 172.30.12.42\n'])
        self.script_env.run(self.script, 'mgmt.cfg', '--quiet')
        self.verify_output('mgmt.xsf',
                           ['configure vlan Default ipaddress 172.30.12.42 '
                            '255.255.0.0\n'],
                           self.jumbo_ignore + self.ignore_stpd +
                           self.ignore_web + self.ignore_idle)

    def test_case_144(self):  # static management address class A
        self.create_input('mgmt.cfg',
                          ['set ip protocol none\n',
                           'set ip address 10.11.12.13\n'])
        self.script_env.run(self.script, 'mgmt.cfg', '--quiet')
        self.verify_output('mgmt.xsf',
                           ['configure vlan Default ipaddress 10.11.12.13 '
                            '255.0.0.0\n'],
                           self.jumbo_ignore + self.ignore_stpd +
                           self.ignore_web + self.ignore_idle)

    def test_case_145(self):  # static management address with mask
        self.create_input('mgmt.cfg',
                          ['set ip protocol none\n',
                           'set ip address 10.11.12.13 mask 255.255.254.0\n'])
        self.script_env.run(self.script, 'mgmt.cfg', '--quiet')
        self.verify_output('mgmt.xsf',
                           ['configure vlan Default ipaddress 10.11.12.13 '
                            '255.255.254.0\n'],
                           self.jumbo_ignore + self.ignore_stpd +
                           self.ignore_web + self.ignore_idle)

    def test_case_146(self):  # static oob management address with mask
        self.create_input('mgmt.cfg',
                          ['set ip protocol none\n',
                           'set ip address 10.11.12.13 mask 255.255.254.0\n'])
        self.script_env.run(self.script, 'mgmt.cfg', '--quiet', '--mgmt-port')
        self.verify_output('mgmt.xsf',
                           ['configure vlan Mgmt ipaddress 10.11.12.13 '
                            '255.255.254.0\n'],
                           self.jumbo_ignore + self.ignore_stpd +
                           self.ignore_web + self.ignore_idle)

    def test_case_147(self):  # static management address with mask and gateway
        self.create_input('mgmt.cfg',
                          ['set ip protocol none\n',
                           'set ip address 10.11.12.13 mask 255.255.254.0 '
                           'gateway 10.11.13.254\n'])
        self.script_env.run(self.script, 'mgmt.cfg', '--quiet', '--mgmt-port')
        self.verify_output('mgmt.xsf',
                           ['configure vlan Mgmt ipaddress 10.11.12.13 '
                            '255.255.254.0\n',
                            'configure iproute add default 10.11.13.254 vr '
                            'VR-Mgmt\n'],
                           self.jumbo_ignore + self.ignore_stpd +
                           self.ignore_web + self.ignore_idle)

    def test_case_148(self):  # static management address with mask and gateway
        self.create_input('mgmt.cfg',
                          ['set ip protocol none\n',
                           'set ip address 10.11.12.13 mask 255.255.254.0 '
                           'gateway 10.11.13.254\n'])
        self.script_env.run(self.script, 'mgmt.cfg', '--quiet')
        self.verify_output('mgmt.xsf',
                           ['configure vlan Default ipaddress 10.11.12.13 '
                            '255.255.254.0\n',
                            'configure iproute add default 10.11.13.254\n',
                            ],
                           self.jumbo_ignore + self.ignore_stpd +
                           self.ignore_web + self.ignore_idle)

    def test_case_149(self):  # static management address with mask and VLAN
        self.create_input('mgmt.cfg',
                          ['set ip protocol none\n',
                           'set vlan create 2\n',
                           'set vlan name 2 Admin\n',
                           'set host vlan 2\n',
                           'set ip address 10.11.12.13 mask 255.255.254.0\n'])
        self.script_env.run(self.script, 'mgmt.cfg', '--quiet')
        self.verify_output('mgmt.xsf',
                           ['create vlan Admin tag 2\n',
                            'configure vlan Admin ipaddress 10.11.12.13 '
                            '255.255.254.0\n'],
                           self.jumbo_ignore + self.ignore_stpd +
                           self.ignore_web + self.ignore_idle)

    def test_case_150(self):  # disable idle timeout
        self.create_input('idle.cfg',
                          ['set logout 0\n'])
        self.script_env.run(self.script, 'idle.cfg', '--log-level=WARN')
        self.verify_output('idle.xsf',
                           ['disable idletimeout\n'],
                           self.jumbo_ignore + self.ignore_stpd +
                           self.ignore_web + self.ignore_mgmt)

    def test_case_151(self):  # idle timeout 20
        self.create_input('idle.cfg',
                          ['set logout 20\n'])
        self.script_env.run(self.script, 'idle.cfg', '--log-level=WARN')
        self.verify_output('idle.xsf',
                           [],
                           self.jumbo_ignore + self.ignore_stpd +
                           self.ignore_web + self.ignore_mgmt)

    def test_case_152(self):  # idle timeout 160
        self.create_input('idle.cfg',
                          ['set logout 160\n'])
        self.script_env.run(self.script, 'idle.cfg', '--log-level=WARN')
        self.verify_output('idle.xsf',
                           ['configure idletimeout 160\n'],
                           self.jumbo_ignore + self.ignore_stpd +
                           self.ignore_web + self.ignore_mgmt)

    def test_case_153(self):  # no warning if sysName oequals prompt
        self.create_input('prompt.cfg',
                          ['set system name Switch01\n',
                           'set prompt Switch01\n'])
        ret = self.script_env.run(self.script, 'prompt.cfg',
                                  '--ignore-defaults',
                                  expect_stderr=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('prompt.xsf',
                           ['configure snmp sysName "Switch01"\n'],
                           [])
        self.verify_output('stderr', [],
                           self.default_ignores + self.ignore_outfile +
                           self.ignore_lag_info + self.ignore_info_vlan_1 +
                           self.ignore_port_mapping + self.ignore_stpd_info +
                           self.ignore_unused_ports)

    def test_case_154(self):  # syslog server
        self.create_input('syslog.cfg',
                          ['set logging server 1 ip-addr 192.0.2.33 state '
                           'enable\n',
                           ])
        self.script_env.run(self.script, 'syslog.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('syslog.xsf',
                           ['configure syslog add 192.0.2.33:514 local4\n',
                            'configure log target syslog 192.0.2.33:514 local4'
                            ' severity debug-data\n',
                            'enable log target syslog 192.0.2.33:514 local4\n',
                            ],
                           [])

    def test_case_155(self):  # syslog server facility local7
        self.create_input('syslog.cfg',
                          ['set logging server 1 ip-addr 192.0.2.33 state '
                           'enable facility local7\n',
                           ])
        self.script_env.run(self.script, 'syslog.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('syslog.xsf',
                           ['configure syslog add 192.0.2.33:514 local7\n',
                            'configure log target syslog 192.0.2.33:514 local7'
                            ' severity debug-data\n',
                            'enable log target syslog 192.0.2.33:514 local7\n',
                            ],
                           [])

    def test_case_156(self):  # syslog server non-standard port
        self.create_input('syslog.cfg',
                          ['set logging server 1 ip-addr 192.0.2.33 state '
                           'enable port 4711\n',
                           ])
        self.script_env.run(self.script, 'syslog.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('syslog.xsf',
                           ['configure syslog add 192.0.2.33:4711 local4\n',
                            'configure log target syslog 192.0.2.33:4711 '
                            'local4 severity debug-data\n',
                            'enable log target syslog 192.0.2.33:4711 '
                            'local4\n',
                            ],
                           [])

    def test_case_157(self):  # syslog server severity 5
        self.create_input('syslog.cfg',
                          ['set logging server 1 ip-addr 192.0.2.33 state '
                           'enable severity 5\n',
                           ])
        self.script_env.run(self.script, 'syslog.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('syslog.xsf',
                           ['configure syslog add 192.0.2.33:514 local4\n',
                            'configure log target syslog 192.0.2.33:514 local4'
                            ' severity warning\n',
                            'enable log target syslog 192.0.2.33:514 local4\n',
                            ],
                           [])

    def test_case_158(self):  # disabled syslog server
        self.create_input('syslog.cfg',
                          ['set logging server 1 ip-addr 192.0.2.33\n',
                           ])
        self.script_env.run(self.script, 'syslog.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('syslog.xsf',
                           ['configure syslog add 192.0.2.33:514 local4\n',
                            'configure log target syslog 192.0.2.33:514 local4'
                            ' severity debug-data\n',
                            ],
                           [])

    def test_case_159(self):  # sntp server
        self.create_input('sntp.cfg',
                          ['set sntp server 192.0.2.33\n',
                           ])
        self.script_env.run(self.script, 'sntp.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('sntp.xsf',
                           ['configure sntp-client primary 192.0.2.33\n',
                            ],
                           [])

    def test_case_160(self):  # two sntp servers
        self.create_input('sntp.cfg',
                          ['set sntp server 192.0.2.33\n',
                           'set sntp server 192.0.2.34\n',
                           ])
        self.script_env.run(self.script, 'sntp.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('sntp.xsf',
                           ['configure sntp-client primary 192.0.2.33\n',
                            'configure sntp-client secondary 192.0.2.34\n',
                            ],
                           [])

    def test_case_161(self):  # two sntp servers and precedence
        self.create_input('sntp.cfg',
                          ['set sntp server 192.0.2.34 precedence 5\n',
                           'set sntp server 192.0.2.33\n',
                           ])
        self.script_env.run(self.script, 'sntp.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('sntp.xsf',
                           ['configure sntp-client primary 192.0.2.33\n',
                            'configure sntp-client secondary 192.0.2.34\n',
                            ],
                           [])

    def test_case_162(self):  # precendence in separate command
        self.create_input('sntp.cfg',
                          ['set sntp server 192.0.2.34\n',
                           'set sntp server 192.0.2.33\n',
                           'set sntp server 192.0.2.34 precedence 10\n',
                           ])
        self.script_env.run(self.script, 'sntp.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('sntp.xsf',
                           ['configure sntp-client primary 192.0.2.33\n',
                            'configure sntp-client secondary 192.0.2.34\n',
                            ],
                           [])

    def test_case_163(self):  # ignore SNTP key
        self.create_input('sntp.cfg',
                          ['set sntp server 192.0.2.34\n',
                           'set sntp server 192.0.2.33\n',
                           'set sntp server 192.0.2.34 precedence 10\n',
                           'set sntp server 192.0.2.33 key 1\n',
                           ])
        ret = self.script_env.run(self.script, 'sntp.cfg',
                                  '--ignore-defaults', '--log-level=WARN',
                                  expect_stderr=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr',
                           ['WARN: Ignoring SNTP server key (set sntp server'
                            ' 192.0.2.33 key 1)\n'],
                           [])
        self.verify_output('sntp.xsf',
                           ['configure sntp-client primary 192.0.2.33\n',
                            'configure sntp-client secondary 192.0.2.34\n',
                            ],
                           [])

    def test_case_164(self):  # two sntp servers with precedence
        self.create_input('sntp.cfg',
                          ['set sntp server 192.0.2.34 precedence 5\n',
                           'set sntp server 192.0.2.33 precedence 6\n',
                           ])
        self.script_env.run(self.script, 'sntp.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('sntp.xsf',
                           ['configure sntp-client primary 192.0.2.34\n',
                            'configure sntp-client secondary 192.0.2.33\n',
                            ],
                           [])

    def test_case_165(self):  # broadcast SNTP client
        self.create_input('sntp.cfg',
                          ['set sntp client broadcast\n',
                           ])
        self.script_env.run(self.script, 'sntp.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('sntp.xsf',
                           ['enable sntp-client\n',
                            ],
                           [])

    def test_case_166(self):  # disable SNTP client
        self.create_input('sntp.cfg',
                          ['set sntp client disable\n',
                           ])
        self.script_env.run(self.script, 'sntp.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('sntp.xsf',
                           ['disable sntp-client\n',
                            ],
                           [])

    def test_case_167(self):  # unicast SNTP client
        self.create_input('sntp.cfg',
                          ['set sntp client unicast\n',
                           'set sntp server 192.0.2.42\n',
                           ])
        self.script_env.run(self.script, 'sntp.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('sntp.xsf',
                           ['configure sntp-client primary 192.0.2.42\n',
                            'enable sntp-client\n',
                            ],
                           [])

    def test_case_168(self):  # unicast SNTP client w/o server
        self.create_input('sntp.cfg',
                          ['set sntp client unicast\n',
                           ])
        ret = self.script_env.run(self.script, 'sntp.cfg',
                                  '--ignore-defaults', '--log-level=WARN',
                                  expect_error=True, expect_stderr=True)
        self.verify_output('sntp.xsf', [], [])
        self.assertEqual(ret.returncode, 1, "Wrong exit code")
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr',
                           ['ERROR: At least one SNTP server needed for '
                            'unicast SNTP client\n',
                            'WARN: SNTP client mode "unicast" omitted from '
                            'translation\n',
                            ],
                           [])

    def test_case_169(self):  # broadcast SNTP client w/server
        self.create_input('sntp.cfg',
                          ['set sntp client broadcast\n',
                           'set sntp server 192.0.2.42\n',
                           ])
        ret = self.script_env.run(self.script, 'sntp.cfg',
                                  '--ignore-defaults', '--log-level=WARN',
                                  expect_stderr=True)
        self.verify_output('sntp.xsf',
                           ['configure sntp-client primary 192.0.2.42\n',
                            'enable sntp-client\n',
                            ],
                           [])
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr',
                           ['WARN: XOS uses unicast SNTP if an SNTP server is'
                            ' configured\n'
                            ],
                           [])

    def test_case_170(self):  # SVI IP
        self.create_input('svi.cfg',
                          ['router\n', 'enable\n', 'configure\n',
                           'ip routing\n',
                           'interface vlan 42\n',
                           'ip address 192.0.2.42 255.255.255.192\n',
                           'no shutdown\n',
                           'exit\n', 'exit\n', 'exit\n', 'exit\n',
                           ])
        self.script_env.run(self.script, 'svi.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('svi.xsf',
                           ['create vlan VLAN_0042 tag 42\n',
                            'configure vlan VLAN_0042 ipaddress 192.0.2.42'
                            ' 255.255.255.192\n',
                            'enable ipforwarding vlan VLAN_0042\n',
                            ],
                           [])

    def test_case_171(self):  # SVI IP w/secondaries
        self.create_input('svi.cfg',
                          ['router\n', 'enable\n', 'configure\n',
                           'ip routing\n',
                           'interface vlan 42\n',
                           'ip address 192.0.2.1 255.255.255.192\n',
                           'ip address 192.0.2.65 255.255.255.192 secondary\n',
                           'ip address 192.0.2.129 255.255.255.192'
                           ' secondary\n',
                           'no shutdown\n',
                           'exit\n', 'exit\n', 'exit\n', 'exit\n',
                           ])
        self.script_env.run(self.script, 'svi.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('svi.xsf',
                           ['create vlan VLAN_0042 tag 42\n',
                            'configure vlan VLAN_0042 ipaddress 192.0.2.1'
                            ' 255.255.255.192\n',
                            'enable ipforwarding vlan VLAN_0042\n',
                            'configure vlan VLAN_0042 add secondary-ipaddress'
                            ' 192.0.2.65 255.255.255.192\n',
                            'configure vlan VLAN_0042 add secondary-ipaddress'
                            ' 192.0.2.129 255.255.255.192\n',
                            ],
                           [])

    def test_case_172(self):  # SVI and host IP on same VLAN
        self.create_input('svi.cfg',
                          ['set host vlan 1\n',
                           'set ip address 10.0.0.1 mask 255.255.255.0\n',
                           'router\n', 'enable\n', 'configure\n',
                           'ip routing\n',
                           'interface vlan 1\n',
                           'ip address 192.0.2.42 255.255.255.192\n',
                           'exit\n', 'exit\n', 'exit\n', 'exit\n',
                           ])
        ret = self.script_env.run(self.script, 'svi.cfg',
                                  '--ignore-defaults', '--log-level=WARN',
                                  expect_error=True, expect_stderr=True)
        self.verify_output('svi.xsf',
                           ['configure vlan Default ipaddress 192.0.2.42'
                            ' 255.255.255.192\n',
                            'enable ipforwarding vlan Default\n',
                            ],
                           [])
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr',
                           ['WARN: XOS cannot disable switched virtual '
                            'interfaces, ignoring shutdown state of interface'
                            ' VLAN 1\n',
                            'ERROR: Both SVI and host management IP '
                            'configured for the same VLAN (Default)\n',
                            'WARN: Management IP address "10.0.0.1" omitted '
                            'from translation\n',
                            'WARN: Management Netmask "255.255.255.0" omitted'
                            ' from translation\n',
                            'WARN: Management VLAN "1" omitted from '
                            'translation\n',
                            ],
                           [])

    def test_case_173(self):  # Loopback IP
        self.create_input('loopback.cfg',
                          ['router\n', 'enable\n', 'configure\n',
                           'ip routing\n',
                           'interface loopback 4\n',
                           'ip address 192.0.2.42 255.255.255.192\n',
                           'no shutdown\n',
                           'exit\n', 'exit\n', 'exit\n', 'exit\n',
                           ])
        self.script_env.run(self.script, 'loopback.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('loopback.xsf',
                           ['create vlan Interface_Loopback_4\n',
                            'enable loopback-mode vlan Interface_Loopback_4\n',
                            'configure vlan Interface_Loopback_4 ipaddress'
                            ' 192.0.2.42 255.255.255.192\n',
                            'enable ipforwarding vlan Interface_Loopback_4\n',
                            ],
                           [])

    def test_case_174(self):  # Loopback IP w/secondaries
        self.create_input('loopback.cfg',
                          ['router\n', 'enable\n', 'configure\n',
                           'ip routing\n',
                           'interface loopback 2\n',
                           'ip address 192.0.2.1 255.255.255.192\n',
                           'ip address 192.0.2.65 255.255.255.192 secondary\n',
                           'ip address 192.0.2.129 255.255.255.192'
                           ' secondary\n',
                           'no shutdown\n',
                           'exit\n', 'exit\n', 'exit\n', 'exit\n',
                           ])
        self.script_env.run(self.script, 'loopback.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('loopback.xsf',
                           ['create vlan Interface_Loopback_2\n',
                            'enable loopback-mode vlan Interface_Loopback_2\n',
                            'configure vlan Interface_Loopback_2 ipaddress '
                            '192.0.2.1'
                            ' 255.255.255.192\n',
                            'enable ipforwarding vlan Interface_Loopback_2\n',
                            'configure vlan Interface_Loopback_2 add '
                            'secondary-ipaddress 192.0.2.65 255.255.255.192\n',
                            'configure vlan Interface_Loopback_2 add '
                            'secondary-ipaddress 192.0.2.129 '
                            '255.255.255.192\n',
                            ],
                           [])

    def test_case_175(self):  # SVI w/DHCP relay
        self.create_input('iphelper.cfg',
                          ['router\n', 'enable\n', 'configure\n',
                           'ip routing\n',
                           'interface vlan 42\n',
                           'ip address 192.0.2.42 255.255.255.192\n',
                           'ip helper-address 192.0.2.11\n',
                           'no shutdown\n',
                           'exit\n', 'exit\n', 'exit\n', 'exit\n',
                           ])
        ret = self.script_env.run(self.script, 'iphelper.cfg',
                                  '--ignore-defaults', '--log-level=NOTICE',
                                  expect_stderr=True)
        self.verify_output('iphelper.xsf',
                           ['create vlan VLAN_0042 tag 42\n',
                            'configure vlan VLAN_0042 ipaddress 192.0.2.42'
                            ' 255.255.255.192\n',
                            'enable ipforwarding vlan VLAN_0042\n',
                            'configure bootprelay add 192.0.2.11\n',
                            'enable bootprelay all\n',
                            ],
                           [])
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr',
                           ['NOTICE: XOS uses a global list of BOOTP / DHCP'
                            ' relay servers instead of per VLAN relay '
                            'servers\n',
                            'NOTICE: enabling BOOTP / DHCP relay on all '
                            'VLANs\n',
                            ],
                           ['Port', 'port', 'translated'])

    def test_case_176(self):  # two SVIs w/DHCP relay
        self.create_input('iphelper.cfg',
                          ['router\n', 'enable\n', 'configure\n',
                           'ip routing\n',
                           'interface vlan 1\n',
                           'ip address 10.0.0.1 255.255.255.0\n',
                           'ip helper-address 10.0.0.254\n',
                           'no shutdown\n',
                           'exit\n',
                           'interface vlan 42\n',
                           'ip address 192.0.2.42 255.255.255.0\n',
                           'ip helper-address 192.0.2.11\n',
                           'no shutdown\n',
                           'exit\n', 'exit\n', 'exit\n', 'exit\n',
                           ])
        ret = self.script_env.run(self.script, 'iphelper.cfg',
                                  '--ignore-defaults', '--log-level=NOTICE',
                                  expect_stderr=True)
        self.verify_output('iphelper.xsf',
                           ['configure vlan Default ipaddress 10.0.0.1'
                            ' 255.255.255.0\n',
                            'enable ipforwarding vlan Default\n',
                            'configure bootprelay add 10.0.0.254\n',
                            'create vlan VLAN_0042 tag 42\n',
                            'configure vlan VLAN_0042 ipaddress 192.0.2.42'
                            ' 255.255.255.0\n',
                            'enable ipforwarding vlan VLAN_0042\n',
                            'configure bootprelay add 192.0.2.11\n',
                            'enable bootprelay all\n',
                            ],
                           [])
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr',
                           ['NOTICE: XOS uses a global list of BOOTP / DHCP'
                            ' relay servers instead of per VLAN relay '
                            'servers\n',
                            'NOTICE: enabling BOOTP / DHCP relay on all '
                            'VLANs\n',
                            ],
                           ['Port', 'port', 'translated'])

    def test_case_177(self):  # no ip routing w/SVI
        self.create_input('svi.cfg',
                          ['router\n', 'enable\n', 'configure\n',
                           'no ip routing\n',
                           'interface vlan 42\n',
                           'ip address 192.0.2.42 255.255.255.192\n',
                           'no shutdown\n',
                           'exit\n', 'exit\n', 'exit\n', 'exit\n',
                           ])
        self.script_env.run(self.script, 'svi.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('svi.xsf',
                           ['create vlan VLAN_0042 tag 42\n',
                            'configure vlan VLAN_0042 ipaddress 192.0.2.42'
                            ' 255.255.255.192\n',
                            ],
                           [])

    def test_case_178(self):  # no ip routing w/Loopback
        self.create_input('loopback.cfg',
                          ['router\n', 'enable\n', 'configure\n',
                           'no ip routing\n',
                           'interface loopback 4\n',
                           'ip address 192.0.2.42 255.255.255.192\n',
                           'no shutdown\n',
                           'exit\n', 'exit\n', 'exit\n', 'exit\n',
                           ])
        self.script_env.run(self.script, 'loopback.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('loopback.xsf',
                           ['create vlan Interface_Loopback_4\n',
                            'enable loopback-mode vlan Interface_Loopback_4\n',
                            'configure vlan Interface_Loopback_4 ipaddress'
                            ' 192.0.2.42 255.255.255.192\n',
                            ],
                           [])

    def test_case_179(self):  # IPv4 static routes
        self.create_input('routes.cfg',
                          ['router\n', 'enable\n', 'configure\n',
                           'ip routing\n',
                           'ip route 0.0.0.0 0.0.0.0 192.0.2.101\n',
                           'ip route 10.0.0.0 255.0.0.0 192.0.2.202\n',
                           'interface vlan 1\n',
                           'ip address 192.0.2.42 255.255.255.0\n',
                           'no shutdown\n',
                           'exit\n', 'exit\n', 'exit\n', 'exit\n',
                           ])
        self.script_env.run(self.script, 'routes.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('routes.xsf',
                           ['configure vlan Default ipaddress 192.0.2.42'
                            ' 255.255.255.0\n',
                            'enable ipforwarding vlan Default\n',
                            'configure iproute add default 192.0.2.101\n',
                            'configure iproute add 10.0.0.0 255.0.0.0'
                            ' 192.0.2.202\n',
                            ],
                           [])

    def test_case_180(self):  # timezone and summer time CE(S)T
        self.create_input('time.cfg',
                          ['set timezone CET 1\n',
                           'set summertime recurring last sunday march 02:00'
                           ' last sunday october 03:00 60\n',
                           'set summertime enable CEST\n',
                           ])
        self.script_env.run(self.script, 'time.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('time.xsf',
                           ['configure timezone name CET 60 autodst name CEST'
                            ' 60 begins every last sunday march at 02 00 ends'
                            ' every last sunday october at 03 00\n',
                            ],
                           [])

    def test_case_181(self):  # timezone UTC
        self.create_input('time.cfg',
                          ['set timezone UTC 0\n',
                           ])
        self.script_env.run(self.script, 'time.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('time.xsf',
                           ['configure timezone name UTC 0 noautodst\n'
                            ],
                           [])

    def test_case_182(self):  # timezone UTC w/o offset
        self.create_input('time.cfg',
                          ['set timezone UTC\n',
                           ])
        self.script_env.run(self.script, 'time.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('time.xsf',
                           ['configure timezone name UTC 0 noautodst\n'
                            ],
                           [])

    def test_case_183(self):  # timezone MSK
        self.create_input('time.cfg',
                          ['set timezone MSK 3\n',
                           ])
        self.script_env.run(self.script, 'time.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('time.xsf',
                           ['configure timezone name MSK 180 noautodst\n'
                            ],
                           [])

    def test_case_184(self):  # timezone AWST
        self.create_input('time.cfg',
                          ['set timezone AWST 08 00\n',
                           ])
        self.script_env.run(self.script, 'time.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('time.xsf',
                           ['configure timezone name AWST 480 noautodst\n'
                            ],
                           [])

    def test_case_185(self):  # timezone and summer time AC(S|D)T
        self.create_input('time.cfg',
                          ['set timezone ACST 9 30\n',
                           'set summertime recurring last sunday october 02:00'
                           ' last sunday march 03:00 60\n',
                           'set summertime enable ACDT\n',
                           ])
        self.script_env.run(self.script, 'time.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('time.xsf',
                           ['configure timezone name ACST 570 autodst name '
                            'ACDT 60 begins every last sunday october at 02 00'
                            ' ends every last sunday march at 03 00\n',
                            ],
                           [])

    def test_case_186(self):  # timezone and summer time P(S|D)T
        self.create_input('time.cfg',
                          ['set timezone PST -8\n',
                           'set summertime recurring second sunday march 02:00'
                           ' first sunday november 02:00 60\n',
                           'set summertime enable PDT\n',
                           ])
        self.script_env.run(self.script, 'time.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('time.xsf',
                           ['configure timezone name PST -480 autodst name '
                            'PDT 60 begins every second sunday march at 02 00'
                            ' ends every first sunday november at 02 00\n',
                            ],
                           [])

    def test_case_187(self):  # radius server for management access
        self.create_input('aaa.cfg',
                          ['set ip address 192.0.2.1 mask 255.255.255.0\n',
                           'set host vlan 1\n',
                           'set radius server 3 192.0.2.33 1812 SECRET'
                           ' realm management-access\n',
                           'set radius server 2 192.0.2.42 1645 PASSWORD'
                           ' realm management-access\n',
                           'set radius enable\n',
                           ])
        self.script_env.run(self.script, 'aaa.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('aaa.xsf',
                           ['configure vlan Default ipaddress 192.0.2.1'
                            ' 255.255.255.0\n',
                            'configure radius mgmt-access primary server'
                            ' 192.0.2.42 1645 client-ip 192.0.2.1'
                            ' shared-secret PASSWORD vr VR-Default\n',
                            'configure radius mgmt-access secondary server'
                            ' 192.0.2.33 1812 client-ip 192.0.2.1'
                            ' shared-secret SECRET vr VR-Default\n',
                            'enable radius mgmt-access\n',
                            ],
                           [])

    def test_case_188(self):  # radius server for management access w/intf
        self.create_input('aaa.cfg',
                          ['router\n', 'enable\n', 'configure\n',
                           'interface vlan 1\n',
                           'ip address 192.0.2.1 255.255.255.0\n',
                           'no shutdown\n',
                           'exit\n', 'exit\n', 'exit\n', 'exit\n',
                           'set radius server 3 192.0.2.33 1812 SECRET'
                           ' realm management-access\n',
                           'set radius server 2 192.0.2.42 1645 PASSWORD'
                           ' realm management-access\n',
                           'set radius interface vlan 1\n',
                           'set radius enable\n',
                           ])
        self.script_env.run(self.script, 'aaa.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('aaa.xsf',
                           ['configure vlan Default ipaddress 192.0.2.1'
                            ' 255.255.255.0\n',
                            'configure radius mgmt-access primary server'
                            ' 192.0.2.42 1645 client-ip 192.0.2.1'
                            ' shared-secret PASSWORD vr VR-Default\n',
                            'configure radius mgmt-access secondary server'
                            ' 192.0.2.33 1812 client-ip 192.0.2.1'
                            ' shared-secret SECRET vr VR-Default\n',
                            'enable radius mgmt-access\n',
                            ],
                           [])

    def test_case_189(self):  # radius server for management access int Lo0
        self.create_input('aaa.cfg',
                          ['router\n', 'enable\n', 'configure\n',
                           'interface loopback 0\n',
                           'ip address 192.0.2.1 255.255.255.0\n',
                           'no shutdown\n',
                           'exit\n', 'exit\n', 'exit\n', 'exit\n',
                           'set radius server 3 192.0.2.33 1812 SECRET'
                           ' realm management-access\n',
                           'set radius server 2 192.0.2.42 1645 PASSWORD'
                           ' realm management-access\n',
                           'set radius enable\n',
                           ])
        self.script_env.run(self.script, 'aaa.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('aaa.xsf',
                           ['create vlan Interface_Loopback_0\n',
                            'enable loopback-mode vlan Interface_Loopback_0\n',
                            'configure vlan Interface_Loopback_0 ipaddress'
                            ' 192.0.2.1 255.255.255.0\n',
                            'configure radius mgmt-access primary server'
                            ' 192.0.2.42 1645 client-ip 192.0.2.1'
                            ' shared-secret PASSWORD vr VR-Default\n',
                            'configure radius mgmt-access secondary server'
                            ' 192.0.2.33 1812 client-ip 192.0.2.1'
                            ' shared-secret SECRET vr VR-Default\n',
                            'enable radius mgmt-access\n',
                            ],
                           [])

    def test_case_190(self):  # radius server for management access int Lo7
        self.create_input('aaa.cfg',
                          ['router\n', 'enable\n', 'configure\n',
                           'interface loopback 7\n',
                           'ip address 192.0.2.1 255.255.255.0\n',
                           'no shutdown\n',
                           'exit\n', 'exit\n', 'exit\n', 'exit\n',
                           'set radius server 3 192.0.2.33 1812 SECRET'
                           ' realm management-access\n',
                           'set radius server 2 192.0.2.42 1645 PASSWORD'
                           ' realm management-access\n',
                           'set radius interface loopback 7\n',
                           'set radius enable\n',
                           ])
        self.script_env.run(self.script, 'aaa.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('aaa.xsf',
                           ['create vlan Interface_Loopback_7\n',
                            'enable loopback-mode vlan Interface_Loopback_7\n',
                            'configure vlan Interface_Loopback_7 ipaddress'
                            ' 192.0.2.1 255.255.255.0\n',
                            'configure radius mgmt-access primary server'
                            ' 192.0.2.42 1645 client-ip 192.0.2.1'
                            ' shared-secret PASSWORD vr VR-Default\n',
                            'configure radius mgmt-access secondary server'
                            ' 192.0.2.33 1812 client-ip 192.0.2.1'
                            ' shared-secret SECRET vr VR-Default\n',
                            'enable radius mgmt-access\n',
                            ],
                           [])

    def test_case_191(self):  # radius server for management access, mgmt port
        self.create_input('aaa.cfg',
                          ['set ip address 192.0.2.1 mask 255.255.255.0\n',
                           'set host vlan 1\n',
                           'set radius server 3 192.0.2.33 1812 SECRET'
                           ' realm management-access\n',
                           'set radius server 2 192.0.2.42 1645 PASSWORD'
                           ' realm management-access\n',
                           'set radius enable\n',
                           ])
        self.script_env.run(self.script, 'aaa.cfg',
                            '--ignore-defaults', '--log-level=WARN',
                            '--mgmt-port')
        self.verify_output('aaa.xsf',
                           ['configure vlan Mgmt ipaddress 192.0.2.1'
                            ' 255.255.255.0\n',
                            'configure radius mgmt-access primary server'
                            ' 192.0.2.42 1645 client-ip 192.0.2.1'
                            ' shared-secret PASSWORD vr VR-Mgmt\n',
                            'configure radius mgmt-access secondary server'
                            ' 192.0.2.33 1812 client-ip 192.0.2.1'
                            ' shared-secret SECRET vr VR-Mgmt\n',
                            'enable radius mgmt-access\n',
                            ],
                           [])

    def test_case_192(self):  # tacacs server
        self.create_input('aaa.cfg',
                          ['set ip address 192.0.2.1 mask 255.255.255.0\n',
                           'set host vlan 1\n',
                           'set tacacs server 3 192.0.2.33 49 SECRET\n',
                           'set tacacs server 2 192.0.2.42 49 PASSWORD\n',
                           'set tacacs enable\n',
                           ])
        self.script_env.run(self.script, 'aaa.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('aaa.xsf',
                           ['configure vlan Default ipaddress 192.0.2.1'
                            ' 255.255.255.0\n',
                            'configure tacacs primary server'
                            ' 192.0.2.42 49 client-ip 192.0.2.1'
                            ' vr VR-Default\n',
                            'configure tacacs primary shared-secret'
                            ' PASSWORD\n',
                            'configure tacacs secondary server'
                            ' 192.0.2.33 49 client-ip 192.0.2.1'
                            ' vr VR-Default\n',
                            'configure tacacs secondary shared-secret'
                            ' SECRET\n',
                            'enable tacacs\n',
                            ],
                           [])

    def test_case_193(self):  # tacacs server, mgmt port
        self.create_input('aaa.cfg',
                          ['set ip address 192.0.2.1 mask 255.255.255.0\n',
                           'set host vlan 1\n',
                           'set tacacs server 3 192.0.2.33 49 SECRET\n',
                           'set tacacs server 2 192.0.2.42 49 PASSWORD\n',
                           'set tacacs enable\n',
                           ])
        self.script_env.run(self.script, 'aaa.cfg',
                            '--ignore-defaults', '--log-level=WARN',
                            '--mgmt-port')
        self.verify_output('aaa.xsf',
                           ['configure vlan Mgmt ipaddress 192.0.2.1'
                            ' 255.255.255.0\n',
                            'configure tacacs primary server'
                            ' 192.0.2.42 49 client-ip 192.0.2.1'
                            ' vr VR-Mgmt\n',
                            'configure tacacs primary shared-secret'
                            ' PASSWORD\n',
                            'configure tacacs secondary server'
                            ' 192.0.2.33 49 client-ip 192.0.2.1'
                            ' vr VR-Mgmt\n',
                            'configure tacacs secondary shared-secret'
                            ' SECRET\n',
                            'enable tacacs\n',
                            ],
                           [])

    def test_case_194(self):  # tacacs server default int Lo0
        self.create_input('aaa.cfg',
                          ['router\n', 'enable\n', 'configure\n',
                           'interface loopback 0\n',
                           'ip address 192.0.2.1 255.255.255.0\n',
                           'no shutdown\n',
                           'exit\n', 'exit\n', 'exit\n', 'exit\n',
                           'set tacacs server 3 192.0.2.33 49 SECRET\n',
                           'set tacacs server 2 192.0.2.42 49 PASSWORD\n',
                           'set tacacs enable\n',
                           ])
        self.script_env.run(self.script, 'aaa.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('aaa.xsf',
                           ['create vlan Interface_Loopback_0\n',
                            'enable loopback-mode vlan Interface_Loopback_0\n',
                            'configure vlan Interface_Loopback_0 ipaddress'
                            ' 192.0.2.1 255.255.255.0\n',
                            'configure tacacs primary server'
                            ' 192.0.2.42 49 client-ip 192.0.2.1'
                            ' vr VR-Default\n',
                            'configure tacacs primary shared-secret'
                            ' PASSWORD\n',
                            'configure tacacs secondary server'
                            ' 192.0.2.33 49 client-ip 192.0.2.1'
                            ' vr VR-Default\n',
                            'configure tacacs secondary shared-secret'
                            ' SECRET\n',
                            'enable tacacs\n',
                            ],
                           [])

    def test_case_195(self):  # tacacs server manual int Lo5
        self.create_input('aaa.cfg',
                          ['router\n', 'enable\n', 'configure\n',
                           'interface loopback 5\n',
                           'ip address 192.0.2.1 255.255.255.0\n',
                           'no shutdown\n',
                           'exit\n', 'exit\n', 'exit\n', 'exit\n',
                           'set tacacs server 3 192.0.2.33 49 SECRET\n',
                           'set tacacs server 2 192.0.2.42 49 PASSWORD\n',
                           'set tacacs interface loopback 5\n',
                           'set tacacs enable\n',
                           ])
        self.script_env.run(self.script, 'aaa.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('aaa.xsf',
                           ['create vlan Interface_Loopback_5\n',
                            'enable loopback-mode vlan Interface_Loopback_5\n',
                            'configure vlan Interface_Loopback_5 ipaddress'
                            ' 192.0.2.1 255.255.255.0\n',
                            'configure tacacs primary server'
                            ' 192.0.2.42 49 client-ip 192.0.2.1'
                            ' vr VR-Default\n',
                            'configure tacacs primary shared-secret'
                            ' PASSWORD\n',
                            'configure tacacs secondary server'
                            ' 192.0.2.33 49 client-ip 192.0.2.1'
                            ' vr VR-Default\n',
                            'configure tacacs secondary shared-secret'
                            ' SECRET\n',
                            'enable tacacs\n',
                            ],
                           [])

    def test_case_196(self):  # tacacs server manual int Vlan 42
        self.create_input('aaa.cfg',
                          ['router\n', 'enable\n', 'configure\n',
                           'interface vlan 42\n',
                           'ip address 192.0.2.1 255.255.255.0\n',
                           'no shutdown\n',
                           'exit\n', 'exit\n', 'exit\n', 'exit\n',
                           'set tacacs server 3 192.0.2.33 49 SECRET\n',
                           'set tacacs server 2 192.0.2.42 49 PASSWORD\n',
                           'set tacacs interface vlan 42\n',
                           'set tacacs enable\n',
                           ])
        self.script_env.run(self.script, 'aaa.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('aaa.xsf',
                           ['create vlan VLAN_0042 tag 42\n',
                            'configure vlan VLAN_0042 ipaddress'
                            ' 192.0.2.1 255.255.255.0\n',
                            'configure tacacs primary server'
                            ' 192.0.2.42 49 client-ip 192.0.2.1'
                            ' vr VR-Default\n',
                            'configure tacacs primary shared-secret'
                            ' PASSWORD\n',
                            'configure tacacs secondary server'
                            ' 192.0.2.33 49 client-ip 192.0.2.1'
                            ' vr VR-Default\n',
                            'configure tacacs secondary shared-secret'
                            ' SECRET\n',
                            'enable tacacs\n',
                            ],
                           [])

    def test_case_197(self):  # SNMP trap receiver
        self.create_input('snmp.cfg',
                          ['set snmp targetparams Pv1 user v1COMM'
                           ' security-model v1 message-processing v1\n',
                           'set snmp targetparams Pv2c user v2COMM'
                           ' security-model v2c message-processing v2c\n',
                           'set snmp targetaddr TRv1 192.0.2.55 param Pv1\n',
                           'set snmp targetaddr TRv2c 192.0.2.56 param Pv2c\n',
                           ])
        self.script_env.run(self.script, 'snmp.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('snmp.xsf',
                           ['configure snmp add trapreceiver 192.0.2.55'
                            ' community v1COMM\n',
                            'configure snmp add trapreceiver 192.0.2.56'
                            ' community v2COMM\n',
                            ],
                           [])

    def test_case_198(self):  # disable rw/ro user accounts
        self.create_input('accounts.cfg',
                          ['set system login ro read-only disable\n',
                           'set system login rw read-write disable\n',
                           ])
        self.script_env.run(self.script, 'accounts.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('accounts.xsf',
                           ['create account user user\n',
                            'disable account user\n',
                            ],
                           [])

    def test_case_199(self):  # disable rw/ro user accounts w/defaults
        self.create_input('accounts.cfg',
                          ['set system login ro read-only disable\n',
                           'set system login rw read-write disable\n',
                           ])
        self.script_env.run(self.script, 'accounts.cfg', '--log-level=WARN')
        self.verify_output('accounts.xsf', self.default_config +
                           ['disable account user\n',
                            ],
                           [])

    def test_case_200(self):  # create user accounts
        self.create_input('accounts.cfg',
                          ['set system login sysadmin super-user enable\n',
                           'set system login support read-write enable\n',
                           'set system login helpdesk read-only enable\n',
                           'set system login consultant read-write disable'
                           ' password s3cr3tp@ssw0rd\n',
                           ])
        self.script_env.run(self.script, 'accounts.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('accounts.xsf',
                           ['create account admin consultant s3cr3tp@ssw0rd\n',
                            'disable account consultant\n',
                            'create account user helpdesk\n',
                            'create account admin support\n',
                            'create account admin sysadmin\n',
                            ],
                           [])

    def test_case_201(self):  # encrypted password is ignored
        self.create_input('accounts.cfg',
                          ['set system login admin super-user enable password'
                           ' :7c1a3d40b26abab519357f5b935beb10a92d2357b9639a'
                           '62cb267947947df76f5407d85d1449730294:\n',
                           ])
        ret = self.script_env.run(self.script, 'accounts.cfg',
                                  '--ignore-defaults', '--log-level=WARN',
                                  expect_stderr=True)
        self.verify_output('accounts.xsf',
                           ['create account admin admin\n',
                            ],
                           [])
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr',
                           ['WARN: Cannot convert encrypted password for'
                            ' user account "admin"\n',
                            ],
                           [])

    def test_case_202(self):  # delete rw/ro user accounts w/defaults
        self.create_input('accounts.cfg',
                          ['clear system login ro\n',
                           'clear system login rw\n',
                           ])
        self.script_env.run(self.script, 'accounts.cfg', '--log-level=WARN')
        self.verify_output('accounts.xsf', self.default_config +
                           ['delete account user\n',
                            ],
                           [])

    def test_case_203(self):  # SVI IP w/secondaries
        self.create_input('svi.cfg',
                          ['router\n', 'enable\n', 'configure\n',
                           'ip routing\n',
                           'interface vlan 42\n',
                           'ip address 192.0.2.1 255.255.255.192\n',
                           'ip address 192.0.2.129 255.255.255.192\n',
                           'ip address 192.0.2.65 255.255.255.192 secondary\n',
                           'no shutdown\n',
                           'exit\n', 'exit\n', 'exit\n', 'exit\n',
                           ])
        self.script_env.run(self.script, 'svi.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('svi.xsf',
                           ['create vlan VLAN_0042 tag 42\n',
                            'configure vlan VLAN_0042 ipaddress 192.0.2.129'
                            ' 255.255.255.192\n',
                            'enable ipforwarding vlan VLAN_0042\n',
                            'configure vlan VLAN_0042 add secondary-ipaddress'
                            ' 192.0.2.65 255.255.255.192\n',
                            ],
                           [])

    def test_case_204(self):  # Loopback IP w/secondaries
        self.create_input('loopback.cfg',
                          ['router\n', 'enable\n', 'configure\n',
                           'ip routing\n',
                           'interface loopback 2\n',
                           'ip address 192.0.2.1 255.255.255.192\n',
                           'ip address 192.0.2.129 255.255.255.192\n',
                           'ip address 192.0.2.65 255.255.255.192 secondary\n',
                           'no shutdown\n',
                           'exit\n', 'exit\n', 'exit\n', 'exit\n',
                           ])
        self.script_env.run(self.script, 'loopback.cfg',
                            '--ignore-defaults', '--log-level=WARN')
        self.verify_output('loopback.xsf',
                           ['create vlan Interface_Loopback_2\n',
                            'enable loopback-mode vlan Interface_Loopback_2\n',
                            'configure vlan Interface_Loopback_2 ipaddress '
                            '192.0.2.129'
                            ' 255.255.255.192\n',
                            'enable ipforwarding vlan Interface_Loopback_2\n',
                            'configure vlan Interface_Loopback_2 add '
                            'secondary-ipaddress 192.0.2.65 255.255.255.192\n',
                            ],
                           [])

    def test_case_205(self):  # wrong ip address command sequence (SVI)
        self.create_input('svi.cfg',
                          ['router\n', 'enable\n', 'configure\n',
                           'ip routing\n',
                           'interface vlan 42\n',
                           'ip address 192.0.2.1 255.255.255.192\n',
                           'ip address 192.0.2.65 255.255.255.192 secondary\n',
                           'ip address 192.0.2.129 255.255.255.192\n',
                           'no shutdown\n',
                           'exit\n', 'exit\n', 'exit\n', 'exit\n',
                           ])
        ret = self.script_env.run(self.script, 'svi.cfg',
                                  '--ignore-defaults', '--log-level=WARN',
                                  expect_stderr=True, expect_error=True)
        self.verify_output('svi.xsf',
                           ['create vlan VLAN_0042 tag 42\n',
                            'configure vlan VLAN_0042 ipaddress 192.0.2.1'
                            ' 255.255.255.192\n',
                            'enable ipforwarding vlan VLAN_0042\n',
                            'configure vlan VLAN_0042 add secondary-ipaddress'
                            ' 192.0.2.65 255.255.255.192\n',
                            ],
                           [])
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr',
                           ['ERROR: Cannot change primary interface IP for'
                            ' interface "interface vlan 42" with secondary'
                            ' IP address(es) (ip address 192.0.2.129'
                            ' 255.255.255.192)\n',
                            ],
                           [])

    def test_case_206(self):  # wrong ip address command sequence (Lo7)
        self.create_input('loopback.cfg',
                          ['router\n', 'enable\n', 'configure\n',
                           'ip routing\n',
                           'interface loopback 7\n',
                           'ip address 192.0.2.1 255.255.255.192\n',
                           'ip address 192.0.2.65 255.255.255.192 secondary\n',
                           'ip address 192.0.2.129 255.255.255.192\n',
                           'no shutdown\n',
                           'exit\n', 'exit\n', 'exit\n', 'exit\n',
                           ])
        ret = self.script_env.run(self.script, 'loopback.cfg',
                                  '--ignore-defaults', '--log-level=WARN',
                                  expect_stderr=True, expect_error=True)
        self.verify_output('loopback.xsf',
                           ['create vlan Interface_Loopback_7\n',
                            'enable loopback-mode vlan Interface_Loopback_7\n',
                            'configure vlan Interface_Loopback_7 ipaddress '
                            '192.0.2.1'
                            ' 255.255.255.192\n',
                            'enable ipforwarding vlan Interface_Loopback_7\n',
                            'configure vlan Interface_Loopback_7 add '
                            'secondary-ipaddress 192.0.2.65 255.255.255.192\n',
                            ],
                           [])
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr',
                           ['ERROR: Cannot change primary interface IP for'
                            ' interface "interface loopback 7" with secondary'
                            ' IP address(es) (ip address 192.0.2.129'
                            ' 255.255.255.192)\n',
                            ],
                           [])

    def test_case_207(self):  # static management address, DHCP manual on
        self.create_input('mgmt.cfg',
                          ['set ip protocol dhcp\n',
                           'set ip address 192.0.2.11\n'])
        ret = self.script_env.run(self.script, 'mgmt.cfg', '--log-level=WARN',
                                  expect_stderr=True, expect_error=True)
        self.verify_output('mgmt.xsf',
                           ['configure vlan Default ipaddress 192.0.2.11 '
                            '255.255.255.0\n'],
                           self.jumbo_ignore + self.ignore_stpd +
                           self.ignore_web + self.ignore_idle)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr',
                           ['ERROR: Management IPv4 address configured'
                            ' statically, but dynamic IPv4 address assignment'
                            ' active, using static IPv4 address only\n',
                            'WARN: Management IP protocol "dhcp" omitted from'
                            ' translation\n',
                            ],
                           [])

    def test_case_208(self):  # static management address, BOOTP manual on
        self.create_input('mgmt.cfg',
                          ['set ip protocol bootp\n',
                           'set ip address 192.0.2.11\n'])
        ret = self.script_env.run(self.script, 'mgmt.cfg', '--log-level=WARN',
                                  expect_stderr=True, expect_error=True)
        self.verify_output('mgmt.xsf',
                           ['configure vlan Default ipaddress 192.0.2.11 '
                            '255.255.255.0\n'],
                           self.jumbo_ignore + self.ignore_stpd +
                           self.ignore_web + self.ignore_idle)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr',
                           ['ERROR: Management IPv4 address configured'
                            ' statically, but dynamic IPv4 address assignment'
                            ' active, using static IPv4 address only\n',
                            'WARN: Management IP protocol "bootp" omitted from'
                            ' translation\n',
                            ],
                           [])

    def test_case_209(self):  # static management address, DHCP default on
        self.create_input('mgmt.cfg',
                          ['set ip address 192.0.2.11\n'])
        ret = self.script_env.run(self.script, 'mgmt.cfg', '--log-level=WARN',
                                  expect_stderr=True, expect_error=True)
        self.verify_output('mgmt.xsf',
                           ['configure vlan Default ipaddress 192.0.2.11 '
                            '255.255.255.0\n'],
                           self.jumbo_ignore + self.ignore_stpd +
                           self.ignore_web + self.ignore_idle)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr',
                           ['WARN: Management IPv4 address configured'
                            ' statically, but dynamic IPv4 address assignment'
                            ' active, using static IPv4 address only\n',
                            ],
                           [])

    def test_case_210(self):  # empty translation
        self.create_input('eos_to_exos_defaults.cfg',
                          self.eos_to_exos_defaults_conf)
        self.script_env.run(self.script, 'eos_to_exos_defaults.cfg',
                            '--log-level=WARN')
        self.verify_output('eos_to_exos_defaults.xsf', [], [])

    def test_case_211(self):  # check for WARN about ignored QoS no router mode
        self.create_input(
            'acl.cfg',
            ['access-list 6 permit host 55.1.2.3 assign-queue 5\n',
             'access-list 1 permit any assign-queue 2\n',
             'access-list 100 permit udp host 61.102.3.2 61.112.0.0 0.0.0.255'
             ' dscp ef\n',
             'access-list 100 permit udp host 61.102.3.5 61.112.0.0 0.0.0.255'
             ' dscp ef assign-queue 4\n',
             'access-list 100 permit ip 61.114.6.7 0.0.0.255 host '
             '61.114.114.114 tos 23 fa\n',
             'access-list 100 permit tcp host 61.114.74.74 eq 17 any '
             'precedence 7\n',
             'access-list 100 permit udp host 61.114.43.33 eq 520 host '
             '61.114.43.33 eq 520 assign-queue 5\n',
             'access-list 100 permit udp host 61.114.43.33 eq 161 host '
             '61.88.12.34 tos ff cb assign-queue 4\n',
             'access-list 100 permit tcp any any established\n',
             ])
        ret = self.script_env.run(self.script, 'acl.cfg', '--log-level=WARN',
                                  expect_stderr=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr', [
            'WARN: Ignoring "assign-queue 5" in "access-list 6 permit host'
            ' 55.1.2.3 assign-queue 5"\n',
            'WARN: Ignoring "assign-queue 2" in "access-list 1 permit any '
            'assign-queue 2"\n',
            'WARN: Ignoring "dscp ef" in "access-list 100 permit udp host '
            '61.102.3.2 61.112.0.0 0.0.0.255 dscp ef"\n',
            'WARN: Ignoring "dscp ef assign-queue 4" in "access-list 100 '
            'permit udp host 61.102.3.5 61.112.0.0 0.0.0.255 dscp ef '
            'assign-queue 4"\n',
            'WARN: Ignoring "tos 23 fa" in "access-list 100 permit ip '
            '61.114.6.7 0.0.0.255 host 61.114.114.114 tos 23 fa"\n',
            'WARN: Ignoring "precedence 7" in "access-list 100 permit tcp host'
            ' 61.114.74.74 eq 17 any precedence 7"\n',
            'WARN: Ignoring "assign-queue 5" in "access-list 100 permit udp '
            'host 61.114.43.33 eq 520 host 61.114.43.33 eq 520 assign-queue 5'
            '"\n',
            'WARN: Ignoring "tos ff cb assign-queue 4" in "access-list 100 '
            'permit udp host 61.114.43.33 eq 161 host 61.88.12.34 tos ff cb '
            'assign-queue 4"\n',
            'WARN: Ignoring "established" in "access-list 100 permit tcp any '
            'any established"\n',
            ], [])
        self.assertEqual(ret.returncode, 0, "Wrong exit code")

    def test_case_212(self):  # check for WARN about incomplete MSTI mapping
        self.create_input(
            'mstp.cfg',
            ['set spantree mstcfgid cfgname HQ rev 1\n',
             'set spantree msti sid 1 create\n',
             'set spantree msti sid 2 create\n',
             'set spantree mstmap 1,4,10,100,102,104,200,666,1000 sid 1\n',
             'set spantree mstmap 20,101,103,105,300 sid 2\n',
             'set spantree priority 0 1\n',
             'set spantree priority 4096 2\n',
             ])
        ret = self.script_env.run(self.script, 'mstp.cfg', '--log-level=WARN',
                                  expect_stderr=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr', [
            'WARN: XOS can only map configured VLANs to MST instances, the '
            'following VLANs have been omitted from MST instance 1: [4, 10, '
            '100, 102, 104, 200, 666, 1000]\n',
            'WARN: XOS can only map configured VLANs to MST instances, the '
            'following VLANs have been omitted from MST instance 2: [20, 101, '
            '103, 105, 300]\n',
            ], [])
        self.assertEqual(ret.returncode, 0, "Wrong exit code")
        self.verify_output('mstp.xsf',
                           ['configure mstp region HQ\n',
                            'configure mstp revision 1\n',
                            'configure stpd s0 delete vlan Default ports '
                            'all\n',
                            'disable stpd s0 auto-bind vlan Default\n',
                            'configure stpd s0 mode mstp cist\n',
                            'enable stpd s0\n',
                            'create stpd s1\n',
                            'configure stpd s1 default-encapsulation dot1d\n',
                            'configure stpd s1 mode mstp msti 1\n',
                            'enable stpd s1 auto-bind vlan Default\n',
                            'configure stpd s1 priority 0\n',
                            'enable stpd s1\n',
                            'create stpd s2\n',
                            'configure stpd s2 default-encapsulation dot1d\n',
                            'configure stpd s2 mode mstp msti 2\n',
                            'configure stpd s2 priority 4096\n',
                            'enable stpd s2\n'],
                           self.jumbo_ignore + self.ignore_web +
                           self.ignore_mgmt + self.ignore_idle)

    def test_case_213(self):  # tacacs server, encr. secret
        self.create_input('aaa.cfg',
                          ['set ip address 192.0.2.1 mask 255.255.255.0\n',
                           'set host vlan 1\n',
                           'set tacacs server 1 192.0.2.33 49 '
                           ':0123456789abcdef0123456789abcdef0123456789abcdef'
                           '0123456789abcdef0123456789abcdef01\n',
                           'set tacacs enable\n',
                           ])
        ret = self.script_env.run(self.script, 'aaa.cfg', '--ignore-defaults',
                                  '--log-level=WARN', expect_stderr=True)
        self.verify_output('aaa.xsf',
                           ['configure vlan Default ipaddress 192.0.2.1'
                            ' 255.255.255.0\n',
                            'configure tacacs primary server'
                            ' 192.0.2.33 49 client-ip 192.0.2.1'
                            ' vr VR-Default\n',
                            'enable tacacs\n',
                            ],
                           [])
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr', [
            'WARN: Ignoring encrypted TACACS+ secret (set tacacs server 1'
            ' 192.0.2.33 49 :0123456789abcdef0123456789abcdef0123456789ab'
            'cdef0123456789abcdef0123456789abcdef01)\n'
            ], [])
        self.assertEqual(ret.returncode, 0, "Wrong exit code")

    def test_case_214(self):  # tacacs server, encr. secret
        self.create_input('aaa.cfg',
                          ['set ip address 192.0.2.1 mask 255.255.255.0\n',
                           'set host vlan 1\n',
                           'set tacacs server 1 192.0.2.33 49 '
                           ':0123456789abcdef0123456789abcdef0123456789abcdef'
                           '0123456789abcdef0123456789abcdef01:\n',
                           'set tacacs enable\n',
                           ])
        ret = self.script_env.run(self.script, 'aaa.cfg', '--ignore-defaults',
                                  '--log-level=WARN', expect_stderr=True)
        self.verify_output('aaa.xsf',
                           ['configure vlan Default ipaddress 192.0.2.1'
                            ' 255.255.255.0\n',
                            'configure tacacs primary server'
                            ' 192.0.2.33 49 client-ip 192.0.2.1'
                            ' vr VR-Default\n',
                            'enable tacacs\n',
                            ],
                           [])
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr', [
            'WARN: Ignoring encrypted TACACS+ secret (set tacacs server 1'
            ' 192.0.2.33 49 :0123456789abcdef0123456789abcdef0123456789ab'
            'cdef0123456789abcdef0123456789abcdef01:)\n'
            ], [])
        self.assertEqual(ret.returncode, 0, "Wrong exit code")

    def test_case_215(self):  # radius server, encr. secret
        self.create_input('aaa.cfg',
                          ['set ip address 192.0.2.1 mask 255.255.255.0\n',
                           'set host vlan 1\n',
                           'set radius server 1 192.0.2.33 1812 '
                           ':0123456789abcdef0123456789abcdef0123456789abcdef'
                           '0123456789abcdef0123456789abcdef01:'
                           ' realm management-access\n',
                           'set radius enable\n',
                           ])
        ret = self.script_env.run(self.script, 'aaa.cfg', '--ignore-defaults',
                                  '--log-level=WARN', expect_stderr=True)
        self.verify_output('aaa.xsf',
                           ['configure vlan Default ipaddress 192.0.2.1'
                            ' 255.255.255.0\n',
                            'configure radius mgmt-access primary server'
                            ' 192.0.2.33 1812 client-ip 192.0.2.1'
                            ' vr VR-Default\n',
                            'enable radius mgmt-access\n',
                            ],
                           [])
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr', [
            'WARN: Ignoring encrypted RADIUS secret (set radius server 1'
            ' 192.0.2.33 1812 :0123456789abcdef0123456789abcdef0123456789ab'
            'cdef0123456789abcdef0123456789abcdef01: realm management-access)'
            '\n'
            ], [])
        self.assertEqual(ret.returncode, 0, "Wrong exit code")

    def test_case_216(self):  # no reserved keyword account names
        self.create_input('accounts.cfg',
                          ['set system login cli super-user enable\n',
                           ])
        ret = self.script_env.run(self.script, 'accounts.cfg',
                                  '--ignore-defaults', '--log-level=WARN',
                                  expect_stderr=True)
        self.verify_output('accounts.xsf',
                           ['create account admin acc_cli\n',
                            ],
                           [])
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr',
                           ['WARN: Replaced account name "cli" with "acc_cli"'
                            ' because "cli" is a reserved keyword in XOS\n',
                            ],
                           [])


if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
