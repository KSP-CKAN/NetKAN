#!/bin/sh

echo Commit hash: ${ghprbActualCommit}
echo Changes in this commit:
git diff-tree --no-commit-id --name-only -r ${ghprbActualCommit}

jsonlint -s -v `git diff-tree --no-commit-id --name-only -r ${ghprbActualCommit}`

# fetch latest netkan.exe
wget -O netkan.exe http://ci.ksp-ckan.org:8080/job/NetKAN/lastSuccessfulBuild/artifact/netkan.exe

