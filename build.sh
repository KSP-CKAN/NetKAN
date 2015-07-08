#!/bin/bash

# Default flags.
KSP_VERSION_DEFAULT="1.0.2"
KSP_NAME_DEFAULT="dummy"

# Locations of CKAN and NetKAN.
LATEST_CKAN_URL="http://ckan-travis.s3.amazonaws.com/ckan.exe"
LATEST_NETKAN_URL="http://ckan-travis.s3.amazonaws.com/netkan.exe"

# Third party utilities.
JQ_PATH="jq"

# ------------------------------------------------
# Function for creating dummy KSP directories to
# test on. Takes version as an argument.
# ------------------------------------------------
create_dummy_ksp () {
    KSP_VERSION=$KSP_VERSION_DEFAULT
    KSP_NAME=$KSP_NAME_DEFAULT
    
    # Set the version to the requested KSP version if supplied.
    if [ $# -eq 2 ]
    then
        KSP_VERSION=$1
        KSP_NAME=$2
    fi
    
    # TODO: Manual hack, a better way to handle this kind of identifiers may be needed.
    if [ "$KSP_VERSION" == "0.90" ]
    then
        KSP_VERSION="0.90.0"
    fi
    
    echo "Creating a dummy KSP $KSP_VERSION install"
    
    # Remove any existing KSP dummy install.
    rm -rf dummy_ksp
    
    # Create a new dummy KSP.
    mkdir dummy_ksp
    mkdir dummy_ksp/CKAN
    mkdir dummy_ksp/GameData
    mkdir dummy_ksp/Ships/
    mkdir dummy_ksp/Ships/VAB
    mkdir dummy_ksp/Ships/SPH
    mkdir dummy_ksp/Ships/@thumbs
    mkdir dummy_ksp/Ships/@thumbs/VAB
    mkdir dummy_ksp/Ships/@thumbs/SPH
    
    echo "Version $KSP_VERSION" > dummy_ksp/readme.txt
    
    # Copy in resources.
    cp ckan.exe dummy_ksp/ckan.exe
    
    # Reset the Mono registry.
    if [ "$USER" = "jenkins" ]
    then
        REGISTRY_FILE=${HOME}/.mono/registry/CurrentUser/software/ckan/values.xml
        if [ -r $REGISTRY_FILE ]
        then
            rm -f $REGISTRY_FILE
        fi
    fi
    
    # Register the new dummy install.
    mono ckan.exe ksp add ${KSP_NAME} "`pwd`/dummy_ksp"
    
    # Set the instance to default.
    mono ckan.exe ksp default ${KSP_NAME}
    
    # Point to the local metadata instead of GitHub.
    mono ckan.exe repo add local "file://`pwd`/master.tar.gz"
    mono ckan.exe repo remove default
    
    # Link to the downloads cache.
    ln -s downloads_cache dummy_ksp/CKAN/downloads
}

# ------------------------------------------------
# Function for injecting metadata into a tar.gz
# archive. Assummes metadata.tar.gz to be present.
# ------------------------------------------------
inject_metadata () {
    # Check input, requires at least 1 argument.
    if [ $# -ne 1 ]
    then
        echo "Nothing to inject."
        cp metadata.tar.gz master.tar.gz
        return 0
    fi
    
    echo "Injecting into metadata."
    
    # Extract the metadata into a new folder.
    rm -rf CKAN-meta-master
    tar -xzf metadata.tar.gz
    
    # Copy in the files to inject.
    for f in $1
    do
        cp f CKAN-meta-master
    done
    
    # Recompress the archive.
    rm -f master.tar.gz
    tar -czf master.tar.gz CKAN-meta-master
}

# ------------------------------------------------
# Main entry point.
# ------------------------------------------------

# Make sure we start from a clean slate.
rm -rf built
rm -rf downloads_cache
rm -f master.tar.gz
rm -f metadata.tar.gz

# Run basic tests.
echo "Running basic sanity tests on metadata."
echo "If these fail, then fix whatever is causing them first."

if ! prove
then
    echo "Prove step failed."
    exit 1
fi

# Find the changes to test.
echo "Finding changes to test..."

if [ -z $ghprbActualCommit ]
then
    echo "No commit hash, running all netkan files"
    export COMMIT_CHANGES=NetKAN/*.netkan
else
    echo "Commit hash: $ghprbActualCommit"
    export COMMIT_CHANGES="`git diff --diff-filter=AM --name-only --stat origin/master NetKAN`"
fi

if [ "$COMMIT_CHANGES" = "" ]
then
    echo "No .netkan changes, skipping further tests."
    exit 0
fi

# Check JSON.
echo "Running jsonlint on the changed files"
echo "If you get an error below you should look for syntax errors in the metadata"

jsonlint -s -v $COMMIT_CHANGES

# Create folders.
mkdir built
mkdir downloads_cache # TODO: Point to cache folder here instead if possible.

# Fetch latest ckan and netkan executable.
echo "Fetching latest ckan.exe"
wget --quiet $LATEST_CKAN_URL -O ckan.exe

echo "Fetching latest netkan.exe"
wget --quiet $LATEST_NETKAN_URL -O netkan.exe

# Fetch the latest metadata.
echo "Fetching latest metadata"
wget --quiet https://github.com/KSP-CKAN/CKAN-meta/archive/master.tar.gz -O metadata.tar.gz

# Determine KSP dummy name.
if [ -z $ghprbActualCommit ]
then
    KSP_NAME=dummy
else
    KSP_NAME=$ghprbActualCommit
fi

mono --debug ckan.exe ksp add ${KSP_NAME} "`pwd`/dummy_ksp"
mono --debug ckan.exe ksp default ${KSP_NAME}

echo Running ckan update
mono --debug ckan.exe update

echo Running jsonlint on the changed files
echo If you get an error below you should look for syntax errors in the metadata

jsonlint -s -v ${COMMIT_CHANGES}

echo Fetching latest netkan.exe

# fetch latest netkan.exe (corresponding to CKAN/master)
wget --quiet https://ckan-travis.s3.amazonaws.com/netkan.exe

mkdir built

# Build all the passed .netkan files.
# Note: Additional NETKAN_OPTIONS may be set on jenkins jobs
for f in $COMMIT_CHANGES
do
    echo "Running NetKAN for $f"
    mono netkan.exe $f --cachedir="downloads_cache" --outputdir="built" ${NETKAN_OPTIONS}
done

# Reset KSP.
mono ckan.exe ksp forget $KSP_NAME_DEFAULT

# Test all the built files.
for f in built/*.ckan
do
    echo "Checking $f"
    echo "----------------------------------------------"
    echo ""
    cat $f | python -m json.tool
    echo "----------------------------------------------"
    echo ""
    
    # Get a list of all the OTHER files.
    OTHER_FILES=()
    
    for o in built/*.ckan
    do
        if [ "$f" != "$o" ]
        then
            OTHER_FILES+=($o)
        fi
    done
    
    # Inject into metadata.
    inject_metadata $OTHER_FILES
    
    # Extract identifier and KSP version.
    CURRENT_IDENTIFIER=$($JQ_PATH '.identifier' $f)
    CURRENT_KSP_VERSION=$($JQ_PATH 'if .ksp_version then .ksp_version else .ksp_version_min end' $f)
    
    # Strip "'s.
    CURRENT_IDENTIFIER=${CURRENT_IDENTIFIER//'"'}
    CURRENT_KSP_VERSION=${CURRENT_KSP_VERSION//'"'}
    
    echo "Extracted $CURRENT_IDENTIFIER as identifier."
    echo "Extracted $CURRENT_KSP_VERSION as KSP version."
    
    # Create a dummy KSP install.
    create_dummy_ksp $CURRENT_KSP_VERSION $KSP_NAME
    
    echo "Running ckan update"
    mono ckan.exe update
    
    echo "Running ckan install -c $f"
    mono ckan.exe install -c $f --headless
    
    # Print list of installed mods.
    mono ckan.exe list --porcelain
    
    # Check the installed files for this .ckan file.
    mono ckan.exe show $CURRENT_IDENTIFIER
    
    # Cleanup.
    mono ckan.exe ksp forget $KSP_NAME
done
