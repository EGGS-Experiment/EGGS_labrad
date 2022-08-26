#!/bin/bash
# LabRAD Node
#   Starts a LabRAD Node.

# PREP
  # get the current directory
FILE_DIR="$( dirname "$0" )"

# todo: take in command line arguments


# set up environment
source ~/.bash_profile
export LABRADHOST=localhost
export LABRADPASSWORD=''
export LABRADPORT=7682
export LABRAD_TLS=off
export LABRAD_TLS_PORT=7643
conda activate labart

# todo: start labrad manager
# todo: start labrad web gui
# todo: start labrad node

# change shell title
echo -n -e "\033]0;LabRAD Shell\007"

# run file
python -ix $FILE_DIR

# unset variables
unset FILE_DIR
