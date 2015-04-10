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
        script = os.path.normpath(os.path.abspath("{}/../src/cli.py".format(
                                  os.path.dirname(os.path.abspath(__file__)))))

    # list of keywords to ignore in most tests
    # (mostly when NOT using --ignore-defaults)
    default_ignores = ["jumbo-frame", "stpd"]
    jumbo_ignore = ["jumbo-frame"]
    ignore_stpd = ["stpd"]
    ignore_port_mapping = ["INFO: Mapping port", "NOTICE: Mapping port"]
    ignore_outfile = ["NOTICE: Writing translated configuration to file"]
    ignore_lag_info = ["INFO: LAG ",
                       "NOTICE: XOS always allows single port LAGs"]
    ignore_info_vlan_1 = ['INFO: Cannot rename VLAN 1 from "Default" to '
                          '"DEFAULT VLAN"']
    ignore_stpd_info = ["INFO: Creating XOS equivalent of EOS default MSTP "
                        "respectively RSTP configuration",
                        "INFO: XOS does not support automatic RSTP/MSTP edge "
                        "port detection"]

    # our standard STP compatibility configuration
    std_stp_conf = ['configure stpd s0 delete vlan Default ports all\n',
                    'disable stpd s0 auto-bind vlan Default\n',
                    'configure stpd s0 mode mstp cist\n',
                    'create stpd s1\n',
                    'configure stpd s1 mode mstp msti 1\n',
                    'enable stpd s1 auto-bind vlan Default\n']

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
            'entry {}'.format(nr) + ' {\n', '  if {\n', '  } then {\n',
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

    def test_case_022(self):  # check if --keep-unknown-lines works
        # needs another command if set dhcp is ever implemented
        self.create_input('test.cfg', ["set dhcp disable\n"])
        self.script_env.run(self.script, '-otest.xsf', 'test.cfg',
                            '--ignore-defaults', '--keep-unknown-lines',
                            '--quiet')
        # verify if line untouched and has a newline before it
        self.verify_output('test.xsf', ["\n", "set dhcp disable\n"], [])

    def test_case_023(self):  # check if --comment-unknown-lines works
        # needs another command if set dhcp is ever implemented
        self.create_input('test.cfg', ["set dhcp disable\n"])
        self.script_env.run(self.script, '-otest.xsf', 'test.cfg',
                            '--ignore-defaults', '--comment-unknown-lines',
                            '--quiet')
        # verify if line is commented with XOS comment char and has a newline
        # before it
        self.verify_output('test.xsf', ["\n", "# set dhcp disable\n"], [])

    def test_case_024(self):  # check if --err-unknown-lines works
        # needs another command if set dhcp is ever implemented
        self.create_input('test.cfg', ["set dhcp disable\n"])
        ret = self.script_env.run(self.script, '-otest.xsf', 'test.cfg',
                                  '--ignore-defaults', '--err-unknown-lines',
                                  '--quiet', expect_error=True)
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
        self.runner([""], [], expected_content, self.ignore_stpd)

    def test_case_010(self):
        self.runner(['set port jumbo disable ge.1.12'], [], [],
                    ["enable jumbo-frame"] + self.ignore_stpd)
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
                    ["create vlan SYS_NLD_0100 tag 100\n"],
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
                     "create vlan SYS_NLD_0100 tag 100\n",
                     "configure vlan SYS_NLD_0100 add ports 1 untagged\n"],
                    self.default_ignores)

    def test_case_030(self):
        self.create_input('testinput', ['set port vlan ge.1.1 100'])
        ret = self.script_env.run(self.script, '-o testoutput.xsf',
                                  'testinput', '--quiet', expect_error=True,
                                  expect_stderr=True)
        self.assertEqual(ret.returncode, 1, "Wrong exit code")
        self.assertEqual(ret.stderr, "ERROR: VLAN 100 not found (set port "
                                     "vlan)\n", "Unexpected Error")
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
                    ['create vlan SYS_NLD_0002 tag 2\n',
                     'configure vlan SYS_NLD_0002 add ports 2-3,5 tagged\n',
                     'create vlan SYS_NLD_0003 tag 3\n',
                     'configure vlan SYS_NLD_0003 add ports 2-3,5 tagged\n'],
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
                     'create vlan SYS_NLD_3001 tag 3001\n',
                     'configure vlan SYS_NLD_3001 add ports 53-54 tagged\n',
                     'create vlan SYS_NLD_3002 tag 3002\n',
                     'configure vlan SYS_NLD_3002 add ports 53-54 tagged\n',
                     'create vlan SYS_NLD_3003 tag 3003\n',
                     'configure vlan SYS_NLD_3003 add ports 53-54 tagged\n',
                     'create vlan SYS_NLD_3004 tag 3004\n',
                     'configure vlan SYS_NLD_3004 add ports 53-54 tagged\n',
                     'create vlan SYS_NLD_3005 tag 3005\n',
                     'configure vlan SYS_NLD_3005 add ports 53-54 tagged\n',
                     'create vlan SYS_NLD_3006 tag 3006\n',
                     'configure vlan SYS_NLD_3006 add ports 53-54 tagged\n',
                     'create vlan SYS_NLD_3007 tag 3007\n',
                     'configure vlan SYS_NLD_3007 add ports 53-54 tagged\n',
                     'create vlan SYS_NLD_3008 tag 3008\n',
                     'configure vlan SYS_NLD_3008 add ports 53-54 tagged\n',
                     'create vlan SYS_NLD_3009 tag 3009\n',
                     'configure vlan SYS_NLD_3009 add ports 53-54 tagged\n',
                     'create vlan SYS_NLD_3010 tag 3010\n',
                     'configure vlan SYS_NLD_3010 add ports 53-54 tagged\n'],
                    self.ignore_stpd)

    def test_case_033(self):
        self.runner(['set vlan create 2\n', 'set vlan create 3\n'],
                    ['--ignore-defaults', '--quiet'],
                    ['create vlan SYS_NLD_0002 tag 2\n',
                     'create vlan SYS_NLD_0003 tag 3\n'], [])

    def test_case_034(self):
        self.runner(['set vlan create 2,3\n'],
                    ['--ignore-defaults', '--quiet'],
                    ['create vlan SYS_NLD_0002 tag 2\n',
                     'create vlan SYS_NLD_0003 tag 3\n'], [])

    def test_case_035(self):
        self.runner(['set vlan create 2,3\n',
                     'set port vlan ge.1.2 2 modify-egress\n',
                     'set port vlan ge.1.3 3 modify-egress\n'],
                    ['--ignore-defaults', '--quiet'],
                    ['configure vlan Default delete ports 2-3\n',
                     'create vlan SYS_NLD_0002 tag 2\n',
                     'configure vlan SYS_NLD_0002 add ports 2 untagged\n',
                     'create vlan SYS_NLD_0003 tag 3\n',
                     'configure vlan SYS_NLD_0003 add ports 3 untagged\n'], [])

    def test_case_036(self):
        self.runner(['set vlan create 2,3\n',
                     'set vlan egress 2 ge.1.1 tagged\n',
                     'set vlan egress 3 ge.1.1 tagged\n'],
                    ['--ignore-defaults', '--quiet'],
                    ['create vlan SYS_NLD_0002 tag 2\n',
                     'configure vlan SYS_NLD_0002 add ports 1 tagged\n',
                     'create vlan SYS_NLD_0003 tag 3\n',
                     'configure vlan SYS_NLD_0003 add ports 1 tagged\n'], [])

    def test_case_037(self):
        self.runner(['set vlan create 2,3\n',
                     'set vlan egress 2,3 ge.1.1 tagged\n'],
                    ['--ignore-defaults', '--quiet'],
                    ['create vlan SYS_NLD_0002 tag 2\n',
                     'configure vlan SYS_NLD_0002 add ports 1 tagged\n',
                     'create vlan SYS_NLD_0003 tag 3\n',
                     'configure vlan SYS_NLD_0003 add ports 1 tagged\n'], [])

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
        self.verify_output('testoutput', ['create vlan SYS_NLD_0002 tag 2\n'],
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
                            ' vlan SYS_NLD_0002 tag 2\n', 'configure vlan '
                            'SYS_NLD_0002 add ports 1 untagged\n'], [])
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
                            ' edge port detection'] + self.ignore_port_mapping)

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
                         '(\'Default\', 1) (\'SYS_NLD_0002\', 2)\n'
                         'ERROR: Untagged VLAN egress and ingress differs for '
                         'port "1"\n',
                         "Wrong error message")

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

# FM STP
    def test_case_060(self):
        self.runner(['set spantree enable\n'], [], self.std_stp_conf +
                    ['enable stpd s0\n', 'enable stpd s1\n'],
                    self.jumbo_ignore)

    def test_case_061(self):
        self.runner(['set spantree disable\n'], [], [],
                    self.jumbo_ignore)

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
            'ERROR: No VLANs associated with any MST instance\n',
            'WARN: VLAN "Default" with tag "1" is not part of any MST'
            ' instance\n',
        ]
        self.verify_output('testoutput.xsf', expected_output,
                           self.jumbo_ignore)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr', expected_errors,
                           ['Mapping', 'Port', 'LAGs'])
        self.assertEqual(ret.returncode, 1)

    def test_case_063(self):
        self.runner(['set spantree msti sid 2 create\n', 'set vlan create 2000'
                     '\n', 'set spantree mstmap 2000 sid 2\n'], [],
                    ['create vlan SYS_NLD_2000 tag 2000\n',
                     'configure mstp revision 0\n',
                     'configure stpd s0 delete vlan Default ports all\n',
                     'disable stpd s0 auto-bind vlan Default\n',
                     'configure stpd s0 mode mstp cist\n',
                     'enable stpd s0\n',
                     'create stpd s2\n',
                     'configure stpd s2 default-encapsulation dot1d\n',
                     'configure stpd s2 mode mstp msti 2\n',
                     'enable stpd s2 auto-bind vlan SYS_NLD_2000\n',
                     'enable stpd s2\n',
                     ], self.jumbo_ignore)

    def test_case_064(self):
        self.create_input('testinput', ['set spantree adminedge ge.1.1 true'
                                        '\n'])
        ret = self.script_env.run(self.script, '-otestoutput.xsf', 'testinput',
                                  expect_stderr=True)
        self.verify_output('testoutput.xsf',  self.std_stp_conf +
                           ['enable stpd s0\n', 'enable stpd s1\n',
                            'configure stpd s0 ports link-type edge 1\n'],
                           self.jumbo_ignore)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr',
                           ['NOTICE: Writing translated configuration to file'
                            ' "testoutput.xsf"\n',
                            'WARN: XOS does not send BPDUs on RSTP/MSTP edge'
                            ' ports without edge-safeguard\n'],
                           ['Mapping', 'Port', 'LAGs'])

    def test_case_065(self):
        self.runner([], [], self.std_stp_conf +
                    ['enable stpd s0\n', 'enable stpd s1\n'],
                    self.jumbo_ignore)

    def test_case_066(self):
        self.runner(['set spantree version rstp\n'], [], self.std_stp_conf +
                    ['enable stpd s0\n', 'enable stpd s1\n'],
                    self.jumbo_ignore)

    def test_case_067(self):
        self.runner(['set spantree priority 0 0\n'], [], self.std_stp_conf +
                    ['configure stpd s0 priority 0\n', 'enable stpd s0\n',
                     'enable stpd s1\n'], self.jumbo_ignore)

    def test_case_068(self):
        self.runner(['set spantree portadmin ge.1.1 disable\n'], [],
                    self.std_stp_conf +
                    ['enable stpd s0\n', 'enable stpd s1\n',
                     'disable stpd s0 ports 1\n'],
                    self.jumbo_ignore)

    def test_case_069(self):
        self.runner(['set spantree adminedge ge.1.1 true\n',
                     'set spantree spanguard enable\n'], [],
                    self.std_stp_conf +
                    ['enable stpd s0\n', 'enable stpd s1\n', 'configure stpd '
                     's0 ports link-type edge 1 edge-safeguard enable\n'],
                    self.jumbo_ignore)

    def test_case_070(self):
        self.runner(['set spantree priority 0\n'], [], self.std_stp_conf +
                    ['configure stpd s0 priority 0\n', 'enable stpd s0\n',
                     'enable stpd s1\n'], self.jumbo_ignore)

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
        self.runner(eos_conf, [], expected_conf, self.jumbo_ignore)

    def test_cast_072(self):
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
        ignore_conf = self.jumbo_ignore
        ignore_err = ['Mapping', 'Port', 'LAG', 'VLAN 1 ']
        self.create_input('testinput', eos_conf)
        ret = self.script_env.run(self.script, '-otestoutput.xsf', 'testinput',
                                  *opts, expect_stderr=True)
        self.verify_output('testoutput.xsf', expected_conf, ignore_conf)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr', expected_err, ignore_err)

    def test_cast_073(self):
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
        ignore_conf = self.jumbo_ignore
        ignore_err = ['Mapping', 'Port', 'LAG', 'VLAN 1 ']
        self.create_input('testinput', eos_conf)
        ret = self.script_env.run(self.script, '-otestoutput.xsf', 'testinput',
                                  *opts, expect_stderr=True)
        self.verify_output('testoutput.xsf', expected_conf, ignore_conf)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr', expected_err, ignore_err)

    def test_cast_074(self):
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
        ignore_conf = self.jumbo_ignore
        ignore_err = ['Mapping', 'Port', 'LAG', 'VLAN 1 ']
        self.create_input('testinput', eos_conf)
        ret = self.script_env.run(self.script, '-otestoutput.xsf', 'testinput',
                                  *opts, expect_stderr=True)
        self.verify_output('testoutput.xsf', expected_conf, ignore_conf)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr', expected_err, ignore_err)

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
                                      'exit\n', 'exit'])
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
                                      'exit\n', 'exit'])
        ret = self.script_env.run(self.script, 'acl.cfg', '--quiet',
                                  expect_stderr=True, expect_error=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr', ['ERROR: Invalid address in ACE config '
                           '"access-list 6 permit ip host 55.1.2.3"\n'], [])
        self.assertEqual(ret.returncode, 1, "Wrong exit code")

    def test_case_080(self):  # test with 2 ACLs seperated by a comment char
        self.create_input('acl.cfg',
                          ['router\n', 'enable\n', 'configure\n',
                           'access-list 2 deny any\n', '!\n', 'access-list 3 '
                           'permit host 55.1.2.3\n', 'exit\n', 'exit\n',
                           'exit'])
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
                           ['entry 10 {\n', '  if {\n', '  } then {\n',
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
                                      'exit'])
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
                           'exit\n', 'exit\n', 'exit'])
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
                                      ' ge.1.1\n', 'exit\n', 'exit\n', 'exit'])
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

    def test_case_072(self):  # test binding 2 ACLs to a port
        self.create_input('acl.cfg', ['router\n', 'enable\n', 'configure\n',
                                      'access-list 1 permit host 192.0.2.1\n',
                                      'access-list 2 deny 192.0.2.2 0.0.0.0\n',
                                      'access-list 1 permit 192.0.2.0 '
                                      '0.0.0.130\n', 'access-list interface 1'
                                      ' ge.1.1\n', 'access-list interface 2'
                                      ' ge.1.1\n', 'exit\n', 'exit\n', 'exit'])
        ret = self.script_env.run(self.script, 'acl.cfg', '--quiet',
                                  expect_stderr=True, expect_error=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr',
                           ['ERROR: EXOS allows only one ACL per port\n'],
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
                                      'exit\n', 'exit\n', 'exit'])
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

    def test_case_074(self):  # test binding ACL to an SVI
        self.create_input('acl.cfg', ['router\n', 'enable\n', 'configure\n',
                                      'access-list 1 permit host 192.0.2.1\n',
                                      'access-list 1 deny 192.0.2.2 0.0.0.0\n',
                                      'access-list 1 permit 192.0.2.0 '
                                      '0.0.0.130\n', 'interface vlan 1\n',
                                      'ip access-group 1\n', 'exit\n'
                                      'exit\n', 'exit\n', 'exit'])
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

    def test_case_073(self):  # test binding 2 ACLs to an SVI
        self.create_input('acl.cfg', ['router\n', 'enable\n', 'configure\n',
                                      'access-list 1 permit host 192.0.2.1\n',
                                      'access-list 2 deny 192.0.2.2 0.0.0.0\n',
                                      'access-list 1 permit 192.0.2.0 '
                                      '0.0.0.130\n',
                                      'interface vlan 1\n'
                                      'ip access-group 1\n',
                                      'ip access-group 2 in\n',
                                      'exit\n', 'exit\n', 'exit\n', 'exit'])
        ret = self.script_env.run(self.script, 'acl.cfg', '--quiet',
                                  expect_stderr=True, expect_error=True)
        self.stderrToFile(ret.stderr, 'stderr')
        self.verify_output('stderr',
                           ['ERROR: Only one ACL per VLAN possible with EXOS'
                            '\n'],
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

    def test_case_086(self):  # test for upper case ICMP protocol in ACL/ACE
        self.create_input('acl.cfg',
                          ['router\n', 'enable\n', 'configure\n',
                           'access-list 145 deny ICMP any any\n',
                           'exit\n', 'exit\n', 'exit'])
        self.script_env.run(self.script, 'acl.cfg', '--quiet')
        self.verify_output('acl.acls/acl_145.pol',
                           ['entry 10 {\n', '  if {\n',
                            '    protocol icmp;\n',
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
                            '    destination-address 4.1.0.1/255.255.0.0;\n',
                            '  } then {\n', '    permit;\n', '  }\n', '}\n',
                            'entry 20 {\n', '  if {\n',
                            '    protocol igmp;\n',
                            '    source-address 6.1.0.1/255.255.0.0;\n',
                            '  } then {\n', '    permit;\n', '  }\n', '}\n',
                            'entry 30 {\n', '  if {\n',
                            '    protocol igmp;\n',
                            '    destination-address 4.1.0.5/255.255.0.0;\n',
                            '  } then {\n', '    permit;\n', '  }\n', '}\n',
                            'entry 40 {\n', '  if {\n',
                            '    protocol igmp;\n',
                            '    source-address 6.1.0.5/255.255.0.0;\n',
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
                           self.ignore_info_vlan_1 + self.ignore_stpd_info)

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
            self.ignore_info_vlan_1 + self.ignore_stpd_info)

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


if __name__ == '__main__':
    unittest.main()

# vim:filetype=python:expandtab:shiftwidth=4:tabstop=4
