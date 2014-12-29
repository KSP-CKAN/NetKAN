#!/bin/sh

jsonlint -s -v NetKAN/*.netkan

echo Commit hash: ${ghprbActualCommit}
echo Changed files:
git diff-tree --no-commit-id --name-only -r ${ghprbActualCommit}

# export TRAVIS_PULL_REQUEST=true
# prove
