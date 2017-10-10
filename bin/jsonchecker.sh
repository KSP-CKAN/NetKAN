#!/bin/bash
# V1.0
# Micha Werle
# Usage: check [-q] [<file pattern>]

PROGNAME=$0
DEBUG=0
ERROR=0
QUIET=0
VERBOSE=0
PATTERN=*

usage() {
	cat << EOF >&2
USAGE: $PROGNAME [options] [<pattern>]

This utility checks a file or set of files for being valid JSON. It prints out a list
of files which are not valid JSON.

Options:
  -q : quiet mode - suppress output of invalid file names.
  -v : verbose output - list files being processed.
  -h : print this help.
EOF
	exit 2
}

while getopts hqv name
do
	case $name in
		(q) QUIET=1;;
		(v)	VERBOSE=1;;
		(h)	usage;;
		(*)	usage;;
	esac
done

shift $((OPTIND - 1))

if [ $# -gt 0 ]; then
	PATTERN=$*
fi
if [ $DEBUG -gt 0 ]; then
	echo "Processing files using pattern $PATTERN..."
fi

for F in $PATTERN; do
	if [[ $VERBOSE -gt 0 ]]; then
		echo "Checking $F..."
	fi
	python -m json.tool $F 2>/dev/null >/dev/null
	if [ $? -ne 0 ]; then
		ERROR=1
		if [[ $VERBOSE -gt 0 ]]; then
			echo "*** $F is not valid JSON."
		elif [[ $QUIET -eq 0 ]]; then
			echo "$F"
		fi
	fi
done

# Return 0 if all files passed
exit $ERROR

