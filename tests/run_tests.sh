#! /bin/sh

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

exit_val=0
test_count=0
PYTHON=python3

export PYTHONDONTWRITEBYTECODE=yippee

BASEDIR=$(dirname $0)
export PYTHONPATH=$BASEDIR/../src:$PYTHONPATH

# separate test programs inside a tests directory
for TEST in $BASEDIR/*[Tt]est.py; do
	test_count=$(( $test_count + 1 ))
	printf -- '\n*** Running test program "%s" ***\n' "$(basename "$TEST")"
	"$PYTHON" "$TEST" > /dev/null
	exit_val=$(( $exit_val + $? ))
done
# doctest tests as part of the source file
for TEST in $BASEDIR/../src/Utils.py $BASEDIR/../src/Tokenizer.py; do
	test_count=$(( $test_count + 1 ))
	printf -- '\n*** Running doc test for "%s" ***\n' "$(basename "$TEST")"
	OUT=$("$PYTHON" "$TEST")
	if test -n "$OUT"; then
		exit_val=$(( $exit_val + 1 ))
		echo FAIL
	else
		echo OK
	fi
done

test "$exit_val" -ne 0 &&
	printf -- '\n***\n*** --- %d of %d test programs failed ---\n***\n' \
		"$exit_val" "$test_count"
exit $exit_val
