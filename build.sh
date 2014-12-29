#!/bin/sh

echo Commit hash: ${ghprbActualCommit}
echo Changes in this commit:
export COMMIT_CHANGES=`git diff-tree --no-commit-id --name-only -r ${ghprbActualCommit}`
echo ${COMMIT_CHANGES}

jsonlint -s -v ${COMMIT_CHANGES}

# fetch latest netkan.exe
wget -O netkan.exe http://ci.ksp-ckan.org:8080/job/NetKAN/lastSuccessfulBuild/artifact/netkan.exe

mkdir built

for f in ${COMMIT_CHANGES}
do
	mono --debug netkan.exe $f --cachedir="." --outputdir="built"
done

# fetch latest ckan.exe
wget -O ckan.exe http://ci.ksp-ckan.org:8080/job/NetKAN/lastSuccessfulBuild/artifact/ckan.exe

# create a dummy KSP install
mkdir dummy_ksp
echo Version 0.90.0 > dummy_ksp/readme.txt
mkdir dummy_ksp/GameData

mono --debug ckan.exe ksp add default "`pwd`/dummy_ksp"
mono --debug ckan.exe ksp default default

for f in built/*.ckan
	mono --debug ckan.exe install -c $f
do

done