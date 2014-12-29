#!/bin/sh

jsonlint -s -v NetKAN/*.netkan

echo Commit hash: ${ghprbActualCommit}

# export TRAVIS_PULL_REQUEST=true
# prove
