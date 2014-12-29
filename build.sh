#!/bin/sh

echo Commit hash: ${ghprbActualCommit}
echo Changes in this commit:
export COMMIT_CHANGES=`git diff-tree --no-commit-id --name-only -r ${ghprbActualCommit}`
echo ${COMMIT_CHANGES}

jsonlint -s -v ${COMMIT_CHANGES}

# fetch latest netkan.exe
wget -O netkan.exe http://ci.ksp-ckan.org:8080/job/NetKAN/lastSuccessfulBuild/artifact/netkan.exe

for * in ${COMMIT_CHANGES}
do
	mono --debug netkan.exe ${COMMIT_CHANGES} --cachedir="." --outputdir="."
done