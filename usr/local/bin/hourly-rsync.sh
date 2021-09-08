#!/bin/bash

# UBC JupyterHub Cluster Student Home Snapshot Task Script
# By Rahim Khoja (rahim.khoja@ubc.ca)
# https://www.linkedin.com/in/rahim-khoja-879944139/

echo
echo "---UBC JupyterHub Cluster Student Home Snapshot Task Script---"
echo "---By: Rahim Khoja (rahim.khoja@ubc.ca)---"
echo

# Requirements: Ubuntu 20.04 LTS or CentOS 7 or any modern Linux Distro
#               Flock
#               Rsync
#               Bash 4 or Greater

# Stop on Error
set -eE  # same as: `set -o errexit -o errtrace`

# Failure Function
function failure() {
    local lineno=$1
    local msg=$2
    echo ""
    echo -e "\033[0;31mError at Line Number $lineno: '$msg'\033[0m"
    echo ""
}

# Failure Function Trap
trap 'failure ${LINENO} "$BASH_COMMAND"' ERR

# Check the bash shell script is being run by root/sudo
if [[ $EUID -ne 0 ]];
then
    echo "This script must be run with sudo" 1>&2
    exit 1
fi


# Variables
HOMEDIR='/mnt/efs/home/'
SNAPDIR='/mnt/efs/snap/'
COURSE='STAT100a'


# Array of User Home Directories
HOME_ARRAY=("${HOMEDIR}"/*/)          # This creates an array of the full paths to all subdirs
HOME_ARRAY=("${HOME_ARRAY[@]%/}")     # This removes the trailing slash on each item
HOME_ARRAY=("${HOME_ARRAY[@]##*/}")   # This gets rid of Path


COUNT=0  # COUNT Variable To Loop Thru HOME_ARRAY
RUNNING=1  # RUNNING Variable to Control While Loop


while [ $RUNNING -eq 1 ]
do
    # Create Lockfile File Location String
    LOCKFILE=/var/lock/"${COURSE}_${HOME_ARRAY[${COUNT}]}".lock

    # Create Home Directory Location String
    STUDENTHOME="${HOMEDIR}${HOME_ARRAY[${COUNT}]}"
    echo ${STUDENTHOME}
    # Create the lockfile.
    touch $LOCKFILE

    # Create a file descriptor over the given lockfile.
    exec {FD}<>$LOCKFILE

    # Try to Not Create the Lock. On Success Wait 10 Seconds
    if ! flock -w 2 -x -n $FD; then
        echo "Error! File is Locked"
        sleep 10

    else
        echo "Lock Aquired!"

        # RSYNC Command to Copy Directory
        rsync -avhW --no-compress "${STUDENTHOME}" "${SNAPDIR}"

        # Unlock Lock File
        flock -u $FD

        # Add 1 to Count
        COUNT=$(($COUNT + 1))

        # Remove LockFile
        rm -f $LOCKFILE
        echo "Lock Released!"
    fi

    # Check if on Last Array Item
    if [ "${#HOME_ARRAY[@]}" -eq "${COUNT}" ]; then

        # Set Running to 0; Break While Loop
        RUNNING=0
    fi
done
