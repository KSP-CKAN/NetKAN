#!/bin/bash
set -x
set -e

echo Fetching latest ckan.exe

# fetch latest ckan.exe
wget --quiet http://ci.ksp-ckan.org:8080/job/CKAN/lastSuccessfulBuild/artifact/ckan.exe -O ckan.exe

echo Creating a dummy KSP install

# create a dummy KSP install
if [ "${USER}" = "jenkins" ]
then
    REGISTRY_FILE=${HOME}/.mono/registry/CurrentUser/software/ckan/values.xml
    if [ -r ${REGISTRY_FILE} ]
    then
        rm -f ${REGISTRY_FILE}
    fi
fi

mkdir dummy_ksp
echo Version 0.90.0 > dummy_ksp/readme.txt
mkdir dummy_ksp/GameData
mkdir dummy_ksp/Ships/
mkdir dummy_ksp/Ships/VAB
mkdir dummy_ksp/Ships/SPH

if [ -z ${ghprbActualCommit} ]
then
    KSP_NAME=dummy
else
    KSP_NAME=${ghprbActualCommit}
fi

mono --debug ckan.exe ksp add ${KSP_NAME} "`pwd`/dummy_ksp"
mono --debug ckan.exe ksp default ${KSP_NAME}

echo Running ckan update
mono --debug ckan.exe update

if [ -z ${ghprbActualCommit} ]
then
    echo No commit hash, running all netkan files
    export COMMIT_CHANGES=NetKAN/*.netkan
else
    echo Commit hash: ${ghprbActualCommit}
    export COMMIT_CHANGES="`git diff --diff-filter=AM --name-only --stat origin/master`"
fi

echo Running jsonlint on the changed files
echo If you get an error below you should look for syntax errors in the metadata

jsonlint -s -v ${COMMIT_CHANGES}

echo Fetching latest netkan.exe

# fetch latest netkan.exe
wget --quiet http://ci.ksp-ckan.org:8080/job/NetKAN/lastSuccessfulBuild/artifact/netkan.exe -O netkan.exe

mkdir built

# additional NETKAN_OPTIONS may be set on jenkins jobs
for f in ${COMMIT_CHANGES}
do
	echo Running NetKAN for $f
	mono --debug netkan.exe $f --cachedir="dummy_ksp/CKAN/downloads" --outputdir="built" ${NETKAN_OPTIONS}
done

for f in built/*.ckan
do
	echo ----------------------------------------------
	echo 
	cat $f | python -m json.tool
	echo ----------------------------------------------
	echo 
	echo Running ckan install -c $f
	mono --debug ckan.exe install -c $f --headless
done


echo ----------------------------------------------
echo
ADDON_LIST=$(mono ckan.exe list --porcelain)
OFS=${IFS}
IFS=' '
echo ${ADDON_LIST} | while read state name version
do
    # echo "state name version '${state}' '${name}' '${version}'"
    mono --debug ckan.exe show ${name}
    echo ----------------------------------------------
    echo
done
IFS=${OFS}
