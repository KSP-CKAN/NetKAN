#!/bin/bash

set -e

# Default flags.
KSP_VERSION_DEFAULT="1.1.2"
KSP_NAME_DEFAULT="dummy"

# Locations of CKAN and NetKAN.
LATEST_CKAN_URL="http://ckan-travis.s3.amazonaws.com/ckan.exe"
LATEST_NETKAN_URL="http://ckan-travis.s3.amazonaws.com/netkan.exe"
LATEST_CKAN_META="https://github.com/KSP-CKAN/CKAN-meta/archive/master.tar.gz"

# Third party utilities.
JQ_PATH="jq"

# Return codes.
EXIT_OK=0
EXIT_FAILED_PROVE_STEP=1
EXIT_FAILED_JSON_VALIDATION=2

# Allow us to specify a commit id as the first argument
if [ -n "$1" ]
then
    echo "Using CLI argument of $1"
    ghprbActualCommit=$1
fi
    
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
    case $KSP_VERSION in
    "0.23")
        echo "Overriding '0.23' with '0.23.0'"
        KSP_VERSION="0.23.0"
        ;;
    "0.25")
        echo "Overriding '0.25' with '0.25.0'"
        KSP_VERSION="0.25.0"
        ;;
    "0.90")
        echo "Overriding '0.90' with '0.90.0'"
        KSP_VERSION="0.90.0"
        ;;
    "1.0")
        echo "Overriding '1.0' with '1.0.5'"
        KSP_VERSION="1.0.5"
        ;;
    "1.0.99")
        echo "Overriding '1.0.99' with '1.0.5'"
        KSP_VERSION="1.0.5"
        ;;
    "1.1")
        echo "Overriding '1.1' with '$KSP_VERSION_DEFAULT'"
        KSP_VERSION=$KSP_VERSION_DEFAULT
        ;;
    "1.1.99")
        echo "Overriding '1.1.99' with '$KSP_VERSION_DEFAULT'"
        KSP_VERSION=$KSP_VERSION_DEFAULT
        ;;
    "any")
        echo "Overriding any with '$KSP_VERSION_DEFAULT'"
        KSP_VERSION=$KSP_VERSION_DEFAULT
        ;;
    "null")
        echo "Overriding 'null' with '$KSP_VERSION_DEFAULT'"
        KSP_VERSION=$KSP_VERSION_DEFAULT
        ;;
    "")
        echo "Overriding empty version with '$KSP_VERSION_DEFAULT'"
        KSP_VERSION=$KSP_VERSION_DEFAULT
        ;;
    *)
        echo "No override, Running with '$KSP_VERSION'"
        ;;
    esac
    
    
    echo "Creating a dummy KSP '$KSP_VERSION' install"
    
    # Remove any existing KSP dummy install.
    if [ -d "dummy_ksp/" ]
    then
        rm -rf dummy_ksp
    fi
    
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
        REGISTRY_FILE=$HOME/.mono/registry/CurrentUser/software/ckan/values.xml
        if [ -r $REGISTRY_FILE ]
        then
            rm -f $REGISTRY_FILE
        fi
    fi
    
    # Register the new dummy install.
    mono ckan.exe ksp add $KSP_NAME "`pwd`/dummy_ksp"
    
    # Set the instance to default.
    mono ckan.exe ksp default $KSP_NAME
    
    # Point to the local metadata instead of GitHub.
    mono ckan.exe repo add local "file://`pwd`/master.tar.gz"
    mono ckan.exe repo remove default
    
    # Link to the downloads cache.
    ln -s ../../downloads_cache/ dummy_ksp/CKAN/downloads/
}

# ------------------------------------------------
# Function for injecting metadata into a tar.gz
# archive. Assummes metadata.tar.gz to be present.
# ------------------------------------------------
inject_metadata () {
    # TODO: Arrays + Bash Functions aren't fun. This needs
    # Improvement but appears to work. The variables are
    # available to the called functions.

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
    # TODO: Unsure why this suddenly needs [*] declaration
    # but it does work
    for f in ${OTHER_FILES[*]}
    do
        echo "Injecting: $f"
        cp $f CKAN-meta-master
    done
    
    # Recompress the archive.
    rm -f master.tar.gz
    tar -czf master.tar.gz CKAN-meta-master
}

# ------------------------------------------------
# Main entry point.
# ------------------------------------------------

if [ -n "$ghprbActualCommit" ]
then
    echo "Commit hash: $ghprbActualCommit"
    export COMMIT_CHANGES="`git diff --diff-filter=AM --name-only --stat origin/master...HEAD`"
else
    echo "No commit provided, skipping further tests."
    exit $EXIT_OK
fi

# Make sure we start from a clean slate.
if [ -d "built/" ]
then
    rm -rf built
fi

if [ -d "downloads_cache/" ]
then
    rm -rf downloads_cache
fi

if [ -e "master.tar.gz" ]
then
    rm -f master.tar.gz
fi

if [ -e "metadata.tar.gz" ]
then
    rm -f metadata.tar.gz
fi

# Check JSON.
echo "Running jsonlint on the changed files"
echo "If you get an error below you should look for syntax errors in the metadata"

for f in $COMMIT_CHANGES
do
    if [[ "$f" =~ build.sh|metadata.t ]]
    then
        echo "Lets try not to validate '$f' with jsonlint"
        continue
    fi

    echo "Validating $f..."
    jsonlint -s -v $f
    
    if [ $? -ne 0 ]
    then
        echo "Failed to validate $f"
        exit $EXIT_FAILED_JSON_VALIDATION
    fi
done
echo ""

# Run basic tests.
echo "Running basic sanity tests on metadata."
echo "If these fail, then fix whatever is causing them first."

if ! prove
then
    echo "Prove step failed."
    exit $EXIT_FAILED_PROVE_STEP
fi

# Find the changes to test.
echo "Finding changes to test..."

# Print the changes.
echo "Detected file changes:"
for f in $COMMIT_CHANGES
do
    echo "$f"
done
echo ""

# Create folders.
mkdir built
mkdir downloads_cache # TODO: Point to cache folder here instead if possible.

# Fetch latest ckan and netkan executable.
echo "Fetching latest ckan.exe"
wget --quiet $LATEST_CKAN_URL -O ckan.exe
mono ckan.exe version

echo "Fetching latest netkan.exe"
wget --quiet $LATEST_NETKAN_URL -O netkan.exe
mono netkan.exe --version

# Fetch the latest metadata.
echo "Fetching latest metadata"
wget --quiet $LATEST_CKAN_META -O metadata.tar.gz

# Determine KSP dummy name.
if [ -z $ghprbActualCommit ]
then
    KSP_NAME=dummy
else
    KSP_NAME=$ghprbActualCommit
fi

# Build all the passed .netkan files.
# Note: Additional NETKAN_OPTIONS may be set on jenkins jobs
for f in $COMMIT_CHANGES
do
    if [[ "$f" =~ build.sh|metadata.t ]];then
        echo "Lets try not to build '$f' with netkan"
        continue
    fi

    echo "Running NetKAN for $f"
    mono netkan.exe $f --cachedir="downloads_cache" --outputdir="built" $NETKAN_OPTIONS
done

# Test all the built files.
for ckan in built/*.ckan
do
    if [ ! -e "$ckan" ]
    then
        echo "No ckan files to test"
        continue
    fi

    echo "Checking $ckan"
    echo "----------------------------------------------"
    echo ""
    cat $ckan | python -m json.tool
    echo "----------------------------------------------"
    echo ""
    
    # Get a list of all the OTHER files.
    OTHER_FILES=()
    
    for o in built/*.ckan
    do
        OTHER_FILES+=($o)
    done
    
    # Inject into metadata.
    inject_metadata $OTHER_FILES
    
    # Extract identifier and KSP version.
    CURRENT_IDENTIFIER=$($JQ_PATH '.identifier' $ckan)
    CURRENT_KSP_VERSION=$($JQ_PATH 'if .ksp_version then .ksp_version else .ksp_version_max end' $ckan)
    
    # Strip "'s.
    CURRENT_IDENTIFIER=${CURRENT_IDENTIFIER//'"'}
    CURRENT_KSP_VERSION=${CURRENT_KSP_VERSION//'"'}
    
    echo "Extracted $CURRENT_IDENTIFIER as identifier."
    echo "Extracted $CURRENT_KSP_VERSION as KSP version."
    
    # Create a dummy KSP install.
    create_dummy_ksp $CURRENT_KSP_VERSION $KSP_NAME
    
    echo "Running ckan update"
    mono ckan.exe update
    
    echo "Running ckan install -c $ckan"
    mono ckan.exe install -c $ckan --headless
    
    # Print list of installed mods.
    mono ckan.exe list --porcelain
    
    # Check the installed files for this .ckan file.
    mono ckan.exe show $CURRENT_IDENTIFIER
    
    # Cleanup.
    mono ckan.exe ksp forget $KSP_NAME
done
