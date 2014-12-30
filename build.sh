#!/bin/sh

echo Commit hash: ${ghprbActualCommit}
echo Changes in this commit:
export COMMIT_CHANGES=`git diff-tree --no-commit-id --name-only -r ${ghprbActualCommit}`
echo ${COMMIT_CHANGES}

jsonlint -s -v ${COMMIT_CHANGES}

# fetch latest netkan.exe
wget --quiet http://ci.ksp-ckan.org:8080/job/NetKAN/lastSuccessfulBuild/artifact/netkan.exe -O netkan.exe

mkdir built

for f in ${COMMIT_CHANGES}
do
	mono --debug netkan.exe $f --cachedir="." --outputdir="built"
done

# fetch latest ckan.exe
wget --quiet http://ci.ksp-ckan.org:8080/job/CKAN/lastSuccessfulBuild/artifact/ckan.exe -O ckan.exe

# create a dummy KSP install
mkdir dummy_ksp
echo Version 0.90.0 > dummy_ksp/readme.txt
mkdir dummy_ksp/GameData

mono --debug ckan.exe ksp add ${ghprbActualCommit} "`pwd`/dummy_ksp"
mono --debug ckan.exe ksp default ${ghprbActualCommit}
mono --debug ckan.exe update

for f in built/*.ckan
do
	mono --debug ckan.exe install -c $f --headless
done
