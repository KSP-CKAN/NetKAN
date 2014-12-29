#!/bin/sh

jsonlint -s -v NetKAN/*.netkan

echo Commit hash: ${sha1}

# export TRAVIS_PULL_REQUEST=true
# prove
